"""
WebSocket server implementation for NoteLens.
"""
import asyncio
import json
import logging
import signal
from datetime import datetime
from typing import Dict, Set, Optional
from http import HTTPStatus
from websockets.asyncio.server import ServerConnection, serve
from websockets.exceptions import ConnectionClosed

logger = logging.getLogger(__name__)


class NoteLensWebSocket:
    """
    WebSocket server for NoteLens application.
    Handles communication between Tauri frontend and Python backend.

    Attributes:
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

    def __init__(self, host: str = "localhost", port: int = 8000):
        self.host = host
        self.port = port
        self.clients: Set[ServerConnection] = set()
        self.server = None
        self._shutdown_event = None

    async def start(self):
        """Start the WebSocket server."""
        self._shutdown_event = asyncio.Event()

        # Setup signal handlers
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(
                sig, lambda s=sig: asyncio.create_task(self.shutdown(s)))

        try:
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
            await self._shutdown_event.wait()

        except Exception as e:
            logger.error("Failed to start WebSocket server: %s", str(e))
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

        # Set shutdown event
        if self._shutdown_event:
            self._shutdown_event.set()

    def process_http_request(self, connection, request):
        """Handle HTTP requests for health checks."""
        if request.path == "/health":
            return connection.respond(HTTPStatus.OK, "OK\n")
        return None

    async def handle_client(self, websocket: ServerConnection):
        """Handle individual client connections."""
        client_id = str(websocket.id)
        logger.info("New client connected: %s", client_id)

        try:
            # Add client to set
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
            self.clients.remove(websocket)

    async def process_message(self, websocket: ServerConnection, message: str):
        """Process incoming WebSocket messages."""
        data = json.loads(message)

        # Validate message structure
        if not self._validate_message(data):
            await self.send_error(websocket, "invalid_message", "Invalid message format")
            return

        # Handle different message types
        handler = self._get_message_handler(data["type"])
        if handler:
            try:
                await handler(websocket, data)
            except Exception as e:
                logger.error("Error in message handler: %s", str(e))
                await self.send_error(
                    websocket,
                    "handler_error",
                    f"Error processing {data['type']}: {str(e)}"
                )
        else:
            await self.send_error(websocket, "unknown_type", f"Unknown message type: {data['type']}")

    def _get_message_handler(self, message_type: str):
        """Get the appropriate handler for a message type."""
        # Message handler mapping will be implemented as we add functionality
        handlers = {
            "ping": self._handle_ping,
            # Additional handlers will be added here
        }
        return handlers.get(message_type)

    async def _handle_ping(self, websocket: ServerConnection, data: Dict):
        """Handle ping messages (for testing)."""
        await self.send_message(websocket, {
            "type": "pong",
            "requestId": data.get("requestId"),
            "timestamp": datetime.now().timestamp(),
            "payload": None,
            "status": "success"
        })

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


async def run_test_server():
    """Run a test instance of the WebSocket server."""
    logging.basicConfig(level=logging.INFO)
    server = NoteLensWebSocket(host="localhost", port=8000)

    try:
        await server.start()
    except KeyboardInterrupt:
        await server.shutdown()

if __name__ == "__main__":
    # This allows us to run the WebSocket server directly for testing
    asyncio.run(run_test_server())


# Example usage in main.py:
"""
async def run_websocket_server():
    server = NoteLensWebSocket()
    await server.start()

if __name__ == "__main__":
    asyncio.run(run_websocket_server())
"""
