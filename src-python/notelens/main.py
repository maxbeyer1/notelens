"""
Main entry point for NoteLens Python backend.
"""
import logging
import signal
import sys
import asyncio
import concurrent.futures
from functools import partial
import uuid
import time

from notelens.core.message_bus import (
    MessageBus, Message, SystemAction, SetupStage,
    SearchMessage, WatcherChangeMessage, SystemControlMessage,
    SetupStartMessage, SetupProgressMessage, SetupCompleteMessage,
    SystemStatusMessage
)
from notelens.core.setup_manager import SetupManager
from notelens.core.config import config
from notelens.core.database import DatabaseManager
from notelens.core.watcher import WatcherService
from notelens.notes.service import NoteService
from notelens.notes.tracker import NoteTracker
from notelens.notes.parser.parser import NotesParser
from notelens.websocket.server import NoteLensWebSocket
from notelens.websocket.models import (
    SetupStatusType, SetupCompleteResponse, SetupCompletePayload,
    MessageType, SetupStats, MessageStatus
)

### LOGGING CONFIG ###

if config.env_mode == "PROD":
    logging.basicConfig(level=logging.INFO)
else:  # DEV mode
    # Enable asyncio debug mode
    asyncio.get_event_loop().set_debug(True)

    # Debug logging configuration
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logging.getLogger('asyncio').setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)


class NoteLensApp:
    """Main application class for NoteLens backend."""

    def __init__(self):
        # Services
        self.message_bus = MessageBus()
        self.db_manager = None
        self.watcher_service = None
        self.note_service = None
        self.note_tracker = None
        self.websocket_server = None
        self.setup_manager = None

        # Application loop
        self._shutdown_event = asyncio.Event()
        self._tasks = set()
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

    async def _run_in_executor(self, func, *args):
        """Run a blocking function in the thread pool executor."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self._executor, func, *args)

    async def setup(self):
        """Initialize and setup all services."""
        try:
            # WebSocket server
            self.websocket_server = NoteLensWebSocket(
                message_bus=self.message_bus)

            # Setup manager
            self.setup_manager = SetupManager(
                self.message_bus, self.websocket_server)

            # Initialize and setup database
            self.db_manager = DatabaseManager()
            self.db_manager.setup()

            # Notes services
            self.note_service = NoteService(self.db_manager)
            self.note_tracker = NoteTracker(
                self.note_service, self.setup_manager)

            # Watcher service
            self.watcher_service = WatcherService(self.message_bus)

        except Exception as e:
            logger.error("Failed to setup services: %s", e)
            await self.cleanup()
            raise

    async def process_messages(self):
        """Process messages from the message bus."""
        try:
            while not self._shutdown_event.is_set():
                try:
                    message = await self.message_bus.get_next_message()
                    was_priority = isinstance(message.payload, (
                        SetupProgressMessage,
                        SystemStatusMessage
                    ))

                    # start_time = time.time()
                    # logger.debug(
                    #     "Starting to process message type: %s at %s",
                    #     type(message.payload),
                    #     start_time
                    # )

                    try:
                        payload = message.payload

                        if isinstance(payload, SearchMessage):
                            # Handle search request
                            logger.info("Received search request: query=%s, limit=%s",
                                        payload.query, payload.limit)

                            results = self.note_service.search_notes(
                                payload.query,
                                payload.limit
                            )
                            if message.reply_queue:
                                await message.reply_queue.put(results)

                        elif isinstance(payload, WatcherChangeMessage):
                            # Handle database change
                            logger.info(
                                "Received database change notification")

                            try:
                                parser = NotesParser()
                                parser_data = parser.parse_database()
                                if parser_data:
                                    stats = await self.note_tracker.process_notes(
                                        parser_data)
                                    logger.info(
                                        "Notes processing complete: %s", stats)
                            except Exception as e:
                                logger.error(
                                    "Error processing database change: %s", str(e))

                        elif isinstance(payload, SystemControlMessage):
                            # Handle system control messages
                            logger.info("Received system control message: %s",
                                        payload.action)

                            if payload.action == SystemAction.START:
                                self.watcher_service.start()
                            elif payload.action == SystemAction.STOP:
                                self.watcher_service.stop()

                            if message.reply_queue:
                                await message.reply_queue.put({
                                    "status": "success",
                                    "action": payload.action.name
                                })

                        elif isinstance(payload, SetupStartMessage):
                            # Handle setup initiation
                            await self._handle_setup_start(message)

                        elif isinstance(payload, SetupProgressMessage):
                            # Handle setup progress updates
                            await self._handle_setup_progress(message)

                        elif isinstance(payload, SetupCompleteMessage):
                            # Handle setup completion
                            await self._handle_setup_complete(message)

                        else:
                            logger.warning("Unknown message type: %s",
                                           type(payload))

                        # end_time = time.time()
                        # logger.debug(
                        #     "Finished processing message type: %s, took %.2f seconds",
                        #     type(message.payload),
                        #     end_time - start_time
                        # )
                    finally:
                        # Mark task as done
                        self.message_bus.task_done(was_priority)

                except asyncio.CancelledError:
                    logger.debug("Message processing cancelled")
                    break
                except Exception as e:
                    logger.error("Error processing message: %s",
                                 e, exc_info=True)
                    continue

        finally:
            logger.debug("Message processing stopped")

    async def _handle_setup_start(self, message: Message[SetupStartMessage]):
        """Handle setup initiation."""
        logger.info("Starting system setup")

        # setup_manager = SetupManager(self.message_bus)

        try:
            # Stage 1: Ensure services are initialized and started
            await self.setup_manager.start_stage(
                SetupStage.INITIALIZING,
                SetupStatusType.CHECKING_SERVICES
            )

            # Check all services
            services_status = {
                "database": self.note_service.is_available(),
                "websocket": self.websocket_server.is_running(),
                "watcher": self.watcher_service.is_available()
            }

            # If any service is not available, raise an error
            unavailable_services = [
                service for service, status in services_status.items()
                if not status
            ]

            if unavailable_services:
                raise RuntimeError(
                    f"Required services unavailable: {
                        ', '.join(unavailable_services)}"
                )

            await self.setup_manager.complete_stage(SetupStatusType.SERVICES_READY)

            # Stage 2: Parse Notes database
            await self.setup_manager.start_stage(
                SetupStage.PARSING,
                SetupStatusType.READING_DATABASE
            )

            parser = NotesParser()
            
            # Create a simpler progress callback to minimize thread communication issues
            # This function gets called from a separate thread via run_coroutine_threadsafe
            async def parsing_progress_callback(progress: float, message: str):
                logger.debug(f"Parsing progress: {progress:.2f} - {message}")
                
                # Use only the direct websocket broadcast method since it's more reliable
                # This simplifies our approach and reduces points of failure
                try:
                    from notelens.websocket.models import SetupStatusType
                    await self.websocket_server.broadcast({
                        "type": "setup_progress",
                        "stage": "parsing",
                        "status_type": SetupStatusType.READING_DATABASE,
                        "status": f"Reading database: {message}",
                        "processing": {
                            "current_note": message
                        }
                    })
                except Exception as e:
                    logger.error(f"Error in progress callback: {str(e)}")
                    # Continue execution and don't fail the parsing process
            
            # Store a reference to the current running loop before starting the thread
            current_loop = asyncio.get_running_loop()
            
            # Create wrapper function to call the callback from the executor
            def parse_with_progress():
                # Create a synchronous callback that schedules the async callback
                def sync_callback(progress: float, message: str):
                    # Use the stored loop reference instead of trying to get it in the thread
                    try:
                        asyncio.run_coroutine_threadsafe(
                            parsing_progress_callback(progress, message),
                            current_loop
                        )
                    except Exception as e:
                        # Log any errors but don't crash the parser
                        print(f"Progress callback error (non-fatal): {str(e)}")
                
                # Call parser with our callback
                return parser.parse_database(progress_callback=sync_callback)
            
            # Run in thread pool to avoid blocking
            parser_data = await self._run_in_executor(parse_with_progress)

            if not parser_data:
                raise ValueError("Parser returned no data")

            await self.setup_manager.complete_stage(
                SetupStatusType.DATABASE_READ
            )

            # Stage 3: Process Notes
            await self.setup_manager.start_stage(
                SetupStage.PROCESSING,
                SetupStatusType.PREPARING_NOTES
            )

            # Process notes - note_tracker will handle progress updates
            stats = await self.note_tracker.process_notes(parser_data)

            await self.message_bus.send(SetupCompleteMessage(
                success=True,
                stats=stats
            ))

            if message.reply_queue:
                await message.reply_queue.put({
                    "status": "success",
                    "stats": stats
                })

        except Exception as e:
            logger.error("Setup error: %s", str(e), exc_info=True)
            await self.message_bus.send(SetupCompleteMessage(
                success=False,
                error=str(e)
            ))

            if message.reply_queue:
                await message.reply_queue.put({
                    "status": "error",
                    "error": str(e)
                })

    async def _handle_setup_progress(self, message: Message[SetupProgressMessage]):
        """Handle setup progress updates."""
        logger.debug(
            "Setup progress - Stage: %s, Status: %s, Notes: %d/%d",
            message.payload.stage.name,
            message.payload.status,
            message.payload.processed_notes or 0,
            message.payload.total_notes or 0
        )

        # Broadcast progress to websocket clients
        await self.websocket_server.broadcast(
            {
                "type": "setup_progress",
                "stage": message.payload.stage.name.lower(),
                "status": message.payload.status,
                "total_notes": message.payload.total_notes,
                "processed_notes": message.payload.processed_notes,
                "current_note": message.payload.current_note,
                "stats": message.payload.stats
            }
        )
        
        logger.debug("Setup progress broadcast completed")

    async def _handle_setup_complete(self, message: Message[SetupCompleteMessage]):
        """Handle setup completion."""
        if message.payload.success:
            logger.info("Setup completed successfully")
            logger.info("Final statistics: %s", message.payload.stats)

            complete_response = SetupCompleteResponse(
                type=MessageType.SETUP_COMPLETE,
                request_id=str(uuid.uuid4()),
                status=MessageStatus.SUCCESS,
                payload=SetupCompletePayload(
                    success=True,
                    stats=SetupStats(**(message.payload.stats or {}))
                )
            )

            # Broadcast completion to websocket clients
            await self.websocket_server.broadcast(
                {
                    "type": "setup_complete",
                    "success": True,
                    "stats": message.payload.stats
                }
            )

            # Start services
            # await self.message_bus.send(SystemControlMessage(
            #     action=SystemAction.START
            # ))
        else:
            logger.error("Setup failed: %s", message.payload.error)
            # Broadcast error to websocket clients
            await self.websocket_server.broadcast(
                {
                    "type": "setup_complete",
                    "success": False,
                    "error": message.payload.error
                }
            )

    async def cleanup(self, sig=None):
        """Cleanup function to handle graceful shutdown."""
        if sig:
            logger.info("Received exit signal %s, shutting down...", sig)

        logger.info("Starting cleanup...")

        # Set shutdown event to trigger cleanup
        if self._shutdown_event:
            logger.info("Setting shutdown event...")
            self._shutdown_event.set()

        # Shutdown executor
        if self._executor:
            logger.info("Shutting down executor...")
            self._executor.shutdown(wait=True)

        # Stop WebSocket server
        if self.websocket_server:
            logger.info("Shutting down WebSocket server...")
            await self.websocket_server.shutdown()

        # Stop watcher service
        if self.watcher_service and self.watcher_service.running:
            logger.info("Stopping watcher service...")
            await self.watcher_service.stop()

        # Cancel all tasks
        for task in self._tasks:
            if not task.done():
                logger.debug("Cancelling task: %s", task.get_name())
                task.cancel()

        if self._tasks:
            logger.debug("Waiting for tasks to complete...")
            await asyncio.gather(*self._tasks, return_exceptions=True)

        # Close database connection
        if self.db_manager:
            logger.info("Closing database connection...")
            self.db_manager.close()

        logger.info("Cleanup complete")

    async def run(self):
        """Run the main application loop."""
        await self.setup()

        try:
            # Start WebSocket server
            # websocket_task = asyncio.create_task(
            #     self.websocket_server.start(),
            #     name="websocket_server"
            # )
            # self._tasks.add(websocket_task)
            websocket_server = await self.websocket_server.start()

            # Start message processor
            message_task = asyncio.create_task(
                self.process_messages(),
                name="message_processor"
            )
            self._tasks.add(message_task)

            # Start watcher service
            if self.watcher_service:
                self.watcher_service.start()

            # Wait for shutdown event
            await self._shutdown_event.wait()

        except asyncio.CancelledError:
            logger.info("Application tasks cancelled")
        except Exception as e:
            logger.error("Error in main loop: %s", str(e))
        finally:
            await self.cleanup()


def main():
    """Main entry point for NoteLens backend."""
    app = NoteLensApp()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    def signal_handler(sig):
        """Handle shutdown signals."""
        logger.info("Received signal %s", sig)
        loop.stop()

    # Set up signal handlers
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, partial(signal_handler, sig))

    try:
        loop.create_task(app.run())
        loop.run_forever()
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    finally:
        loop.run_until_complete(app.cleanup())
        logger.info("Shutting down event loop...")
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
        logger.info("Application exited")
        sys.exit(0)


if __name__ == "__main__":
    main()
