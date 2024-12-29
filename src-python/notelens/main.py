import logging
from notelens.core.database import DatabaseManager

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
            
    except Exception as e:
        logger.error(f"Error during database setup: {e}")
        raise

if __name__ == "__main__":
    main()
