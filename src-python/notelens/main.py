"""
Main entry point for NoteLens Python backend.
"""
import logging
import signal
import sys
import asyncio
from functools import partial

from notelens.core.message_bus import (
    MessageBus, SystemAction, SearchMessage,
    WatcherChangeMessage, SystemControlMessage
)
from notelens.core.config import config
from notelens.core.database import DatabaseManager
from notelens.core.watcher import WatcherService
from notelens.notes.service import NoteService
from notelens.notes.tracker import NoteTracker
from notelens.notes.parser.parser import NotesParser
from notelens.websocket.server import NoteLensWebSocket

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
        self.message_bus = MessageBus()
        self.db_manager = None
        self.watcher_service = None
        self.note_service = None
        self.note_tracker = None
        self.websocket_server = None
        self._shutdown_event = asyncio.Event()
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

        except Exception as e:
            logger.error("Failed to setup services: %s", e)
            await self.cleanup()
            raise

    async def process_messages(self):
        """Process messages from the message bus."""
        try:
            while not self._shutdown_event.is_set():
                try:
                    message = await self.message_bus.main_queue.get()
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
                        logger.info("Received database change notification")

                        try:
                            parser = NotesParser()
                            parser_data = parser.parse_database()
                            if parser_data:
                                stats = self.note_tracker.process_notes(
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

                    else:
                        logger.warning("Unknown message type: %s",
                                       type(payload))

                except asyncio.CancelledError:
                    logger.debug("Message processing cancelled")
                    break
                except Exception as e:
                    logger.error("Error processing message: %s",
                                 e, exc_info=True)
                    continue

        finally:
            logger.debug("Message processing stopped")

    async def cleanup(self, sig=None):
        """Cleanup function to handle graceful shutdown."""
        if sig:
            logger.info("Received exit signal %s, shutting down...", sig)

        logger.info("Starting cleanup...")

        # Set shutdown event to trigger cleanup
        if self._shutdown_event:
            logger.info("Setting shutdown event...")
            self._shutdown_event.set()

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
            websocket_task = asyncio.create_task(
                self.websocket_server.start(),
                name="websocket_server"
            )
            self._tasks.add(websocket_task)

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
