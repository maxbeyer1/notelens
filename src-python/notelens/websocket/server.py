"""
WebSocket server implementation for NoteLens.
"""
import asyncio
import json
import logging
import time
from threading import Lock
from datetime import datetime
from typing import Dict, Set, Optional
from http import HTTPStatus
from websockets.asyncio.server import ServerConnection, serve
from websockets.exceptions import ConnectionClosed

from .handlers.base import WebSocketHandler
from ..core.message_bus import MessageBus

logger = logging.getLogger(__name__)


class NoteLensWebSocket:
    """
    WebSocket server for NoteLens application.
    Handles communication between Tauri frontend and Python backend.

    Attributes:
        message_bus (MessageBus): Message bus instance for communication.
        host (str): Hostname for the WebSocket server.
        port (int): Port number for the WebSocket server.
        clients (Set[ServerConnection]): Set of connected clients.
        server (websockets.server.WebSocketServer): WebSocket server instance.
        _shutdown_event (asyncio.Event): Event to signal server shutdown.

    Example usage:
        ```python
        async def run_websocket_server():
            server = NoteLensWebSocket()
            await server.start()

        if __name__ == "__main__":
            asyncio.run(run_websocket_server())
        ```
    """

    def __init__(self, message_bus: MessageBus, host: str = "localhost", port: int = 8003):
        self.host = host
        self.port = port
        self.message_bus = message_bus
        self.clients: Set[ServerConnection] = set()
        self.server = None
        self._shutdown_event = None
        self._broadcast_queue: asyncio.Queue = asyncio.Queue()
        self._broadcast_task = None
        self._clients_lock = Lock()

        # Register message handlers
        self.handlers: Dict[str, WebSocketHandler] = self._setup_handlers()

    def _setup_handlers(self) -> Dict[str, WebSocketHandler]:
        """Initialize message handlers."""
        # Import handlers here to avoid circular imports
        # pylint: disable=import-outside-toplevel
        from .handlers.search import SearchHandler
        from .handlers.setup import SetupHandler
        # from .handlers.system import SystemControlHandler
        from .handlers.ping import PingHandler

        return {
            "search_request": SearchHandler(self.message_bus),
            # "watcher_control": SystemControlHandler(self.message_bus),
            # "get_system_status": SystemControlHandler(self.message_bus),
            "ping": PingHandler(self.message_bus),
            "setup_start": SetupHandler(self.message_bus),
            # Add other handlers as needed
        }

    def is_running(self) -> bool:
        """Check if the server is running."""
        return self.server is not None and self.server.is_serving()

    async def start(self):
        """Start the WebSocket server.

        Returns:
            The WebSocket server instance.
        """
        self._shutdown_event = asyncio.Event()

        try:
            # Start broadcast handler task
            self._broadcast_task = asyncio.create_task(
                self._handle_broadcasts(),
                name="broadcast_handler"
            )

            # Start WebSocket server
            self.server = await serve(
                self.handle_client,
                self.host,
                self.port,
                ping_interval=20,  # Keep-alive ping every 20 seconds
                ping_timeout=60,   # Connection timeout after 60 seconds of no response
                process_request=self.process_http_request  # Handle HTTP health checks
            )

            logger.info("WebSocket server started on ws://%s:%d",
                        self.host, self.port)
            # await self._shutdown_event.wait()

            return self.server

        # except Exception as e:
        #     logger.error("Failed to start WebSocket server: %s", str(e))
        #     raise
        # finally:
        #     # Ensure broadcast task is cancelled
        #     if self._broadcast_task:
        #         self._broadcast_task.cancel()

        #         try:
        #             await self._broadcast_task  # Wait for task to finish
        #         except asyncio.CancelledError:  # Ignore cancellation
        #             pass
        except Exception as e:
            logger.error("Failed to start WebSocket server: %s", str(e))
            if self._broadcast_task:
                self._broadcast_task.cancel()
                try:
                    await self._broadcast_task
                except asyncio.CancelledError:
                    pass
            raise

    async def shutdown(self, sig=None):
        """Gracefully shutdown the WebSocket server."""
        if sig:
            logger.info("Received exit signal %s", sig.name)

        logger.info("Shutting down WebSocket server...")

        # Close all client connections
        if self.clients:
            await asyncio.gather(*[
                client.close(1001, "Server shutting down")
                for client in self.clients
            ])

        # Close the server
        if self.server:
            self.server.close()
            await self.server.wait_closed()

        # Cancel broadcast task
        if self._broadcast_task:
            self._broadcast_task.cancel()
            try:
                await self._broadcast_task
            except asyncio.CancelledError:
                pass

        # Set shutdown event
        if self._shutdown_event:
            self._shutdown_event.set()

    def process_http_request(self, connection, request):
        """Handle HTTP requests for health checks."""
        if request.path == "/health":
            return connection.respond(HTTPStatus.OK, "OK\n")
        return None

    async def _handle_broadcasts(self):
        """Handle broadcast messages from queue."""
        try:
            while not self._shutdown_event.is_set():
                logger.debug("Waiting for next broadcast message...")
                message = await self._broadcast_queue.get()
                logger.debug("Got broadcast message, about to send to clients")

                try:
                    #  Log current event loop state
                    loop = asyncio.get_running_loop()
                    logger.debug(f"Current event loop: {
                                 id(loop)}, is_running: {loop.is_running()}")

                    # Ensure timestamp is present
                    if "timestamp" not in message:
                        message["timestamp"] = datetime.now().timestamp()

                    # Get current clients safely
                    with self._clients_lock:
                        current_clients = set(self.clients)  # Make a copy

                    if not current_clients:
                        logger.debug("No clients connected, broadcast skipped")
                        continue

                    # Send to all clients
                    send_tasks = []
                    for client in current_clients:
                        try:
                            send_tasks.append(
                                asyncio.create_task(
                                    client.send(json.dumps(message))
                                )
                            )
                        except Exception as e:
                            logger.error(
                                "Failed to queue broadcast to client: %s", str(e))
                            continue

                    if send_tasks:
                        await asyncio.gather(*send_tasks, return_exceptions=True)
                        logger.debug(
                            "Broadcast completed to %d clients", len(send_tasks))

                except Exception as e:
                    logger.error("Error in broadcast handler: %s", str(e))
                finally:
                    self._broadcast_queue.task_done()

        except asyncio.CancelledError:
            logger.debug("Broadcast handler cancelled")
        except Exception as e:
            logger.error("Broadcast handler error: %s", str(e))

    async def broadcast(self, message: Dict):
        """Queue a message for broadcasting to all clients."""
        await self._broadcast_queue.put(message)
        logger.debug("Message queued for broadcast")

    async def handle_client(self, websocket: ServerConnection):
        """Handle individual client connections."""
        client_id = str(websocket.id)
        logger.info("New client connected: %s", client_id)

        try:
            # Add client to set thread-safely
            with self._clients_lock:
                self.clients.add(websocket)

            # Handle client messages
            async for message in websocket:
                try:
                    await self.process_message(websocket, message)
                except json.JSONDecodeError:
                    await self.send_error(websocket, "invalid_message", "Invalid JSON format")
                except Exception as e:
                    logger.error("Error processing message: %s", str(e))
                    await self.send_error(websocket, "processing_error", str(e))

        except ConnectionClosed:
            logger.info("Client disconnected: %s", client_id)
        except Exception as e:
            logger.error("Error handling client %s: %s", client_id, str(e))
        finally:
            # Remove client from set thread-safely
            with self._clients_lock:
                self.clients.remove(websocket)

    async def process_message(self, websocket: ServerConnection, message: str):
        """Process incoming WebSocket messages."""
        data = json.loads(message)

        # Validate message structure
        if not self._validate_message(data):
            await self.send_error(websocket, "invalid_message", "Invalid message format")
            return

        # Get appropriate handler for message type
        handler = self.handlers.get(data["type"])
        if handler:
            try:
                await handler.handle(websocket, data)
            except Exception as e:
                logger.error("Error in message handler: %s", str(e))
                await self.send_error(
                    websocket,
                    "handler_error",
                    f"Error processing {data['type']}: {str(e)}",
                    request_id=data.get("requestId")
                )
        else:
            await self.send_error(
                websocket,
                "unknown_type",
                f"Unknown message type: {data['type']}",
                request_id=data.get("requestId")
            )

    @staticmethod
    def _validate_message(data: Dict) -> bool:
        """Validate incoming message format."""
        required_fields = {"type", "requestId", "timestamp"}
        return all(field in data for field in required_fields)

    @staticmethod
    async def send_message(websocket: ServerConnection, message: Dict):
        """Send a message to a client."""
        await websocket.send(json.dumps(message))

    @staticmethod
    async def send_error(
        websocket: ServerConnection,
        code: str,
        message: str,
        details: Optional[Dict] = None,
        request_id: Optional[str] = None
    ):
        """Send an error message to a client."""
        error_message = {
            "type": "error",
            "requestId": request_id,
            "timestamp": datetime.now().timestamp(),
            "status": "error",
            "payload": {
                "error": {
                    "code": code,
                    "message": message,
                    "details": details
                }
            }
        }
        await websocket.send(json.dumps(error_message))


# async def run_test_server():
#     """Run a test instance of the WebSocket server."""
#     logging.basicConfig(level=logging.INFO)
#     server = NoteLensWebSocket(host="localhost", port=8000)

#     try:
#         await server.start()
#     except KeyboardInterrupt:
#         await server.shutdown()

# if __name__ == "__main__":
    # This allows us to run the WebSocket server directly for testing
    # asyncio.run(run_test_server())
