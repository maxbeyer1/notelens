"""
Database manager for the SQLite database.
"""
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
    """Utility class for serializing and deserializing vectors."""
    @staticmethod
    def serialize_vector(vector: List[float]) -> bytes:
        """
        Serializes a list of floats into a compact bytes format.

        Args:
            vector: List of floats to serialize.

        Returns:
            Serialized bytes.
        """
        return struct.pack(f"{len(vector)}f", *vector)


class DatabaseManager:
    """Manager class for the SQLite database."""

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

            conn.execute("PRAGMA debug_logic_error = true;")

            conn.enable_load_extension(True)

            # Get the package root directory (one level up from core)
            package_root = Path(__file__).parent.parent
            lib_dir = package_root / "lib"

            # Verify the path exists
            extension_path = lib_dir / "rembed0.dylib"
            if not extension_path.exists():
                raise FileNotFoundError(
                    f"SQLite extension not found at {extension_path}. "
                    "Please ensure the extension file is in the correct location."
                )

            conn.load_extension(str(extension_path))  # Load sqlite-rembed
            sqlite_vec.load(conn)  # Load sqlite-vec

            # Test the setup
            sqlite_version, vec_version = conn.execute(
                "SELECT sqlite_version(), vec_version()"
            ).fetchone()
            logger.info("Database setup successful. SQLite version: %s, "
                        "sqlite-vec version: %s", sqlite_version, vec_version)

            # Verify rembed extension is loaded properly
            rembed_version = conn.execute("SELECT rembed_version()").fetchone()
            logger.info("sqlite-rembed version: %s", rembed_version[0])

            # First, try to verify if the virtual table exists
            try:
                conn.execute("SELECT * FROM temp.rembed_clients LIMIT 1")
            except sqlite3.OperationalError:
                logger.warning(
                    "rembed_clients table not found, it should be created by the extension")
                raise

            # Now try to insert the client
            conn.execute("""
                INSERT INTO temp.rembed_clients(name, options)
                VALUES ('text-embedding-3-small', 'openai')
            """)

            # Verify the insertion worked
            client_check = conn.execute(
                "SELECT * FROM temp.rembed_clients WHERE name = 'text-embedding-3-small'"
            ).fetchone()
            if client_check:
                logger.info("Successfully registered embedding client")

            # Test the embedding generation with a separate query
            test_result = conn.execute("""
                SELECT rembed('text-embedding-3-small', 'This is a test sentence')
            """).fetchone()

            if test_result and test_result[0]:
                logger.info("Rembed extension test successful - generated embedding of length %d",
                            len(struct.unpack(f"{config.database.vector_dimension}f", test_result[0])))
            else:
                logger.error(
                    "Rembed extension test failed - result: %s", test_result)

            # Initialize the database schema
            self._init_database()

            conn.enable_load_extension(False)
            conn.close()
        except Exception as e:
            logger.error("Failed to setup database: %s", e)
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
            logger.error("Vector search test failed: %s", e)
            return False
