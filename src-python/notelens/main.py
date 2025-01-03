"""
Main entry point for NoteLens Python backend.
"""
import logging
import signal
import sys
import time
from queue import Queue, Empty
from datetime import datetime

from notelens.core.database import DatabaseManager
from notelens.core.watcher import WatcherService
from notelens.notes.service import NoteService
from notelens.notes.tracker import NoteTracker
from notelens.notes.parser.parser import NotesParser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Global variables
db_manager = None  # pylint: disable=invalid-name
watcher_service = None  # pylint: disable=invalid-name
note_service = None  # pylint: disable=invalid-name
note_tracker = None  # pylint: disable=invalid-name
change_queue = Queue()


def handle_db_change() -> None:
    """Handle database changes by running the parser and processing notes."""
    change_queue.put(datetime.now())


def process_db_change() -> None:
    """Process database changes in main thread."""
    try:
        parser = NotesParser()
        parser_data = parser.parse_database()

        if parser_data:
            logger.info("Successfully parsed Notes database after change")

            # Process notes using the tracker
            stats = note_tracker.process_notes(parser_data)

            # Log the results
            logger.info("Note processing complete!")
            logger.info("Processing statistics:")
            logger.info("  Total notes: %d", stats['total'])
            logger.info("  New notes: %d", stats['new'])
            logger.info("  Modified notes: %d", stats['modified'])
            logger.info("  Deleted notes: %d", stats['deleted'])
            logger.info("  Notes in trash: %d", stats['in_trash'])
            logger.info("  Errors: %d", stats['errors'])

    except Exception as e:
        logger.error("Error processing database change: %s",
                     str(e), exc_info=True)


def cleanup(signum=None, frame=None):
    """Cleanup function to handle graceful shutdown."""
    logger.info("Cleaning up...")
    if watcher_service and watcher_service.running:
        watcher_service.stop()
    if db_manager:
        db_manager.close()
    sys.exit(0)


def main():
    """Main entry point for testing the database setup."""
    # pylint: disable=global-statement
    global db_manager, watcher_service, note_service, note_tracker

    try:
        # Initialize and setup database
        db_manager = DatabaseManager()
        db_manager.setup()

        # Test vector search functionality
        if db_manager.test_vector_search():
            logger.info("Vector search test successful!")
        else:
            logger.error("Vector search test failed!")

        # Initialize the notes service
        note_service = NoteService(db_manager)
        note_tracker = NoteTracker(note_service)

        # Initialize and start watcher
        watcher_service = WatcherService(handle_db_change)

        # Register signal handlers for cleanup
        signal.signal(signal.SIGINT, cleanup)
        signal.signal(signal.SIGTERM, cleanup)

        # Start watching
        logger.info("Starting watcher service...")
        watcher_service.start()

        # Keep the main thread alive
        while True:
            try:
                # Process any pending changes
                latest_change = change_queue.get_nowait()
                logger.info("Processing database change at: %s", latest_change)
                process_db_change()

            except Empty:
                # No changes to process, sleep briefly
                time.sleep(1)  # Shorter sleep to stay responsive

    except Exception as e:
        logger.error("Error running main loop: %s", str(e))
        cleanup()
        raise


if __name__ == "__main__":
    main()
