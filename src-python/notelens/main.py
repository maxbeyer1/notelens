"""
Main entry point for NoteLens Python backend.
"""
import logging
import signal
import sys
import asyncio

from notelens.core.database import DatabaseManager
from notelens.core.watcher import WatcherService
from notelens.core.message_bus import MessageBus, MessageType
from notelens.notes.service import NoteService
from notelens.notes.tracker import NoteTracker
from notelens.notes.parser.parser import NotesParser
from notelens.websocket.server import NoteLensWebSocket

# Enable asyncio debug mode
asyncio.get_event_loop().set_debug(True)

# Standard logging configuration
# logging.basicConfig(level=logging.INFO)

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
        self.message_bus = MessageBus()
        self.db_manager = None
        self.watcher_service = None
        self.note_service = None
        self.note_tracker = None
        self.websocket_server = None
        self._shutdown_event = None
        self._tasks = set()

    async def setup(self):
        """Initialize and setup all services."""
        try:
            # Initialize and setup database
            self.db_manager = DatabaseManager()
            self.db_manager.setup()

            # Notes services
            self.note_service = NoteService(self.db_manager)
            self.note_tracker = NoteTracker(self.note_service)

            # WebSocket server
            self.websocket_server = NoteLensWebSocket(
                message_bus=self.message_bus)

            # Watcher service
            self.watcher_service = WatcherService(self.message_bus)

            self._shutdown_event = asyncio.Event()

            # Register signal handlers for cleanup
            for sig in (signal.SIGTERM, signal.SIGINT):
                asyncio.get_running_loop().add_signal_handler(
                    sig,
                    lambda s=sig: asyncio.create_task(self.cleanup(sig))
                )

        except Exception as e:
            logger.error("Failed to setup services: %s", e)
            await self.cleanup()
            raise

    async def process_messages(self):
        """Process messages from the message bus."""
        while not self._shutdown_event.is_set():
            try:
                message = await self.message_bus.main_queue.get()

                if message.type == MessageType.DB_SEARCH:
                    # Handle search request
                    logger.info("Received search request: %s", message.payload)

                    results = self.note_service.search_notes(
                        message.payload["query"],
                        message.payload["limit"]
                    )
                    if message.reply_queue:
                        await message.reply_queue.put(results)

                elif message.type == MessageType.WATCHER_CHANGE:
                    # Handle database change
                    logger.info("Received database change notification")

                    try:
                        parser = NotesParser()
                        parser_data = parser.parse_database()
                        if parser_data:
                            stats = self.note_tracker.process_notes(
                                parser_data)
                            logger.info("Notes processing complete: %s", stats)
                    except Exception as e:
                        logger.error(
                            "Error processing database change: %s", str(e))

                elif message.type == MessageType.SYSTEM_CONTROL:
                    # Handle system control messages
                    logger.info("Received system control message: %s",
                                message.payload)

                    action = message.payload.get("action")
                    if action == "start":
                        self.watcher_service.start()
                    elif action == "stop":
                        self.watcher_service.stop()

                    if message.reply_queue:
                        await message.reply_queue.put({
                            "status": "success",
                            "action": action
                        })

            except Exception as e:
                logger.error("Error processing message: %s", e, exc_info=True)

    async def cleanup(self, sig=None):
        """Cleanup function to handle graceful shutdown."""
        if sig:
            logger.info("Received exit signal %s, shutting down...", sig)

        logger.info("Cleaning up...")

        # Set shutdown event to trigger cleanup
        if self._shutdown_event:
            self._shutdown_event.set()

        # Cancel all running tasks
        for task in self._tasks:
            if not task.done():
                logger.info("Cancelling task: %s", task.get_name())
                task.cancel()

        if self._tasks:
            logger.info("Waiting for tasks to finish...")
            await asyncio.gather(*self._tasks, return_exceptions=True)

        # Stop WebSocket server
        if self.websocket_server:
            await self.websocket_server.shutdown()

        # Stop watcher service
        if self.watcher_service and self.watcher_service.running:
            self.watcher_service.stop()

        # Close database connection
        if self.db_manager:
            self.db_manager.close()

        logger.info("Cleanup complete, exiting...")

        loop = asyncio.get_running_loop()
        loop.stop()

    async def run(self):
        """Run the main application loop."""
        await self.setup()

        try:
            # # Start services
            # if self.watcher_service:
            #     self.watcher_service.start()

            # # Run main tasks
            # await asyncio.gather(
            #     self.websocket_server.start(),
            #     self.process_messages()
            # )
            # Create and track tasks
            websocket_task = asyncio.create_task(
                self.websocket_server.start(),
                name="websocket_server"
            )
            message_task = asyncio.create_task(
                self.process_messages(),
                name="message_processor"
            )

            self._tasks.add(websocket_task)
            self._tasks.add(message_task)

            # Start services
            if self.watcher_service:
                self.watcher_service.start()

            # Wait for shutdown event
            await self._shutdown_event.wait()
        except Exception as e:
            logger.error("Error in main loop: %s", str(e))
            raise
        finally:
            await self.cleanup()


def main():
    """Main entry point for NoteLens backend."""
    app = NoteLensApp()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        asyncio.run(app.run())
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error("Application error: %s", str(e))
        sys.exit(1)
    finally:
        logger.info("Closing event loop...")
        loop.close()
        logger.info("Application exited")
        sys.exit(0)


if __name__ == "__main__":
    main()
