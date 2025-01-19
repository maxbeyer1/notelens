"""
Watchdog-based file system watcher for the Apple Notes SQLite database.
"""
import logging
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable
from watchdog.events import FileSystemEventHandler, FileModifiedEvent
from watchdog.observers import Observer

from .config import config
from .message_bus import MessageBus, WatcherChangeMessage

logger = logging.getLogger(__name__)


class NotesDBEventHandler(FileSystemEventHandler):
    """
    Handles file system events for the Notes SQLite database with debouncing.
    Only processes MODIFIED events and implements cooldown period to prevent
    rapid successive processing.
    """

    def __init__(self, callback: Callable[[], None], cooldown_seconds: int = 2):
        self.callback = callback
        self.last_processed = datetime.min
        self.cooldown = timedelta(seconds=cooldown_seconds)

    def on_modified(self, event: FileModifiedEvent) -> None:
        """
        Handle modified events for the Notes database file.
        Implements debouncing to prevent rapid successive processing.
        """
        if not event.is_directory:
            now = datetime.now()
            if (now - self.last_processed) > self.cooldown:
                logger.info("File modified in Notes directory: %s",
                            event.src_path)
                self.callback()
                self.last_processed = now


class WatcherService:
    """
    Service for watching the Apple Notes SQLite database for changes.
    Integrates with the existing service architecture and maintains
    consistent configuration patterns.
    """

    def __init__(self, message_bus: MessageBus):
        """
        Initialize the watcher service.

        Args:
            message_bus (MessageBus): The message bus instance from the main app.
        """
        self.message_bus = message_bus
        self.observer = Observer()
        self.running = False

        # Verify database exists
        if not config.apple_notes.db_path.exists():
            raise FileNotFoundError(
                f"Notes database not found at: {config.apple_notes.db_path}")

        # Create event handler
        self.event_handler = NotesDBEventHandler(
            callback=self._handle_change,
            cooldown_seconds=config.watcher.cooldown_seconds
        )

    def _handle_change(self) -> None:
        """Handle database changes by sending a message on the bus."""
        try:
            asyncio.create_task(
                self.message_bus.send(WatcherChangeMessage(
                    # TODO: update with event src path
                    path=str(config.apple_notes.db_path)
                ))
            )
        except Exception as e:
            logger.error("Error handling database change: %s",
                         str(e), exc_info=True)

    def start(self) -> None:
        """Start watching for changes."""
        if self.running:
            logger.warning("Watcher already running")
            return

        logger.info("Starting Notes database watcher for: %s",
                    config.apple_notes.db_path)

        # Watch the directory containing the database
        self.observer.schedule(
            self.event_handler,
            str(config.apple_notes.db_path.parent),
            recursive=False
        )

        self.observer.start()
        self.running = True

    async def stop(self) -> None:
        """Stop watching for changes."""
        if not self.running:
            logger.warning("Watcher not running")
            return

        logger.info("Stopping Notes database watcher")
        self.observer.stop()
        # Run the blocking join in a thread pool
        await asyncio.get_event_loop().run_in_executor(None, self.observer.join)
        self.running = False

    def is_available(self) -> bool:
        """Check if the watcher is available."""
        return self.running and self.observer.is_alive()

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
