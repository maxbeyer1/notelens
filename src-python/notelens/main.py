"""
Main entry point for NoteLens Python backend.
"""
import logging
from notelens.core.database import DatabaseManager
from notelens.notes.service import NoteService
from notelens.notes.tracker import NoteTracker
from notelens.notes.parser.parser import NotesParser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for testing the database setup."""
    db_manager = None

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

        # Initialize and test the parser
        try:
            parser = NotesParser()
            logger.info("Parser initialized successfully")

            # Parse the Notes database
            parser_data = parser.parse_database()
            if parser_data:
                logger.info("Successfully parsed Notes database")

                # Process notes using the tracker
                stats = note_tracker.process_notes(parser_data)

                # Log the results
                logger.info("Note processing test complete!")
                logger.info("Processing statistics:")
                logger.info("  Total notes: %d", stats['total'])
                logger.info("  New notes: %d", stats['new'])
                logger.info("  Modified notes: %d", stats['modified'])
                logger.info("  Deleted notes: %d", stats['deleted'])
                logger.info("  Notes in trash: %d", stats['in_trash'])
                logger.info("  Errors: %d", stats['errors'])
            else:
                logger.error("Parser returned no data")

            # Test search functionality
            search_results = note_service.search_notes("test")

            if search_results:
                logger.info("Search test successful, found %d notes",
                            len(search_results))
            else:
                logger.error("Search test failed!")

        except Exception as e:
            logger.error("Parser test failed: %s", str(e))
            raise

    except Exception as e:
        logger.error("Error during database setup: %s", e)
        raise

    finally:
        if db_manager:
            db_manager.close()


if __name__ == "__main__":
    main()
