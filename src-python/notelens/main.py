"""
Main entry point for NoteLens Python backend.
"""
import logging
import json
from notelens.core.database import DatabaseManager
from notelens.core.models import Note
from notelens.notes.service import NotesService

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
        notes_service = NotesService(db_manager)

        # Load test data from a JSON file
        with open("test_data.json") as f:
            note_data = json.load(f)

        try:
            # Create a test note
            note = Note(**note_data)
            created_note = notes_service.create_note(note)
            logger.info("Created note: %s", created_note.title)

            # Test search functionality
            search_results = notes_service.search_notes("AI agent")
            logger.info("Search results: %d found", len(search_results))

            # Clean up
            notes_service.delete_note(created_note.uuid)
            logger.info("Deleted note: %s", created_note.title)
        except Exception as e:
            logger.error("Failed to create note: %s", e)
            raise

    except Exception as e:
        logger.error("Error during database setup: %s", e)
        raise

    finally:
        if db_manager:
            db_manager.close()


if __name__ == "__main__":
    main()
