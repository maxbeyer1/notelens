"""
Main entry point for NoteLens Python backend.
"""
import logging
import json
from pathlib import Path
from notelens.core.database import DatabaseManager
from notelens.core.models import Note
from notelens.notes.service import NoteService
from notelens.notes.tracker import NoteTracker

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

        # Load test parser output from JSON file
        parser_output_path = Path(__file__).parent / "all_notes_1.json"
        with open(parser_output_path) as f:
            parser_data = json.load(f)

        try:
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

        except Exception as e:
            logger.error("Failed to process notes: %s", e)
            raise

    except Exception as e:
        logger.error("Error during database setup: %s", e)
        raise

    finally:
        if db_manager:
            db_manager.close()


if __name__ == "__main__":
    main()
