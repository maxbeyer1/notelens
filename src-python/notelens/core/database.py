import struct
from pathlib import Path
from typing import List, Optional
from contextlib import contextmanager
import logging
import sqlite3
import sqlite_vec

from .config import config

logger = logging.getLogger(__name__)

class VectorUtils:
    @staticmethod
    def serialize_vector(vector: List[float]) -> bytes:
        """Serializes a list of floats into a compact bytes format."""
        return struct.pack(f"{len(vector)}f", *vector)

class DatabaseManager:
    def __init__(self, db_path: Optional[Path] = None):
        """Initialize the database manager.
        
        Args:
            db_path: Optional path to the database file. If None, uses the default from config.
        """
        self.db_path = db_path or config.database.db_path
        self._connection: Optional[sqlite3.Connection] = None

    def _init_database(self) -> None:
        """Initialize the database schema."""
        with self.get_connection() as conn:
            # Create the vector table for embeddings
            conn.execute(f"""
                CREATE VIRTUAL TABLE IF NOT EXISTS note_embeddings 
                USING vec0(
                    embedding float[{config.database.vector_dimension}]
                )
            """)
            
            # Create the notes table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

    def setup(self) -> None:
        """Set up the database with required extensions and schema."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.enable_load_extension(True)
            sqlite_vec.load(conn)
            conn.enable_load_extension(False)
            
            # Test the setup
            sqlite_version, vec_version = conn.execute(
                "SELECT sqlite_version(), vec_version()"
            ).fetchone()
            logger.info(f"Database setup successful. SQLite version: {sqlite_version}, "
                       f"sqlite-vec version: {vec_version}")
            
            self._init_database()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to setup database: {e}")
            raise

    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = None
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.enable_load_extension(True)
            sqlite_vec.load(conn)
            conn.enable_load_extension(False)
            yield conn
        finally:
            if conn:
                conn.close()

    def test_vector_search(self) -> bool:
        """Test vector search functionality."""
        try:
            with self.get_connection() as conn:
                # Test data
                test_items = [
                    (1, [0.1] * config.database.vector_dimension),
                    (2, [0.2] * config.database.vector_dimension),
                    (3, [0.3] * config.database.vector_dimension),
                ]
                
                # Insert test data
                for item_id, vector in test_items:
                    conn.execute(
                        "INSERT INTO note_embeddings(rowid, embedding) VALUES (?, ?)",
                        [item_id, VectorUtils.serialize_vector(vector)]
                    )
                
                # Test query
                query_vector = [0.2] * config.database.vector_dimension
                rows = conn.execute("""
                    SELECT rowid, distance
                    FROM note_embeddings
                    WHERE embedding MATCH ?
                    ORDER BY distance
                    LIMIT 1
                """, [VectorUtils.serialize_vector(query_vector)]).fetchall()
                
                # Clean up test data
                conn.execute("DELETE FROM note_embeddings")
                
                return len(rows) > 0
        except Exception as e:
            logger.error(f"Vector search test failed: {e}")
            return False
