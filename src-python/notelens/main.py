"""
Main entry point for NoteLens Python backend.
"""
import logging
import json
from notelens.core.database import DatabaseManager
from notelens.core.models import Note

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for testing the database setup."""
    try:
        # Initialize and setup database
        db_manager = DatabaseManager()
        db_manager.setup()

        # Test vector search functionality
        if db_manager.test_vector_search():
            logger.info("Vector search test successful!")
        else:
            logger.error("Vector search test failed!")

        # Test Note model

        # Load test data from a JSON file
        with open("test_data.json") as f:
            note_data = json.load(f)

        try:
            note = Note(**note_data)
            logger.info("Parsed note sucessfully: %s", note.title)
        except Exception as e:
            logger.error("Failed to parse note: %s", e)
            raise

        # Convert note to a database-friendly dictionary
        db_dict = note.to_db_dict()
        if db_dict:
            logger.info("Note converted to database dictionary sucessfully.")

        # Convert database dictionary back to a Note object
        note_from_db = Note.from_db_dict(db_dict)
        if note_from_db:
            logger.info("Note created from database dictionary sucessfully.")

    except Exception as e:
        logger.error(f"Error during database setup: {e}")
        raise


if __name__ == "__main__":
    main()
