"""
Database manager for the SQLite database.
"""
import struct
from pathlib import Path
from typing import List, Optional
import hashlib
import logging
import sqlite3
import sqlite_vec
import numpy as np

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


class FakeEmbeddingGenerator:
    """Generates deterministic fake embeddings for testing."""

    @staticmethod
    def generate_fake_embedding(text: str, dimension: int = 1536) -> List[float]:
        """
        Generate a deterministic fake embedding from text.

        Args:
            text: Input text to generate embedding for
            dimension: Desired embedding dimension

        Returns:
            List of floats representing the fake embedding
        """
        # Use text hash as random seed for reproducibility
        text_hash = hashlib.md5(text.encode()).hexdigest()
        seed = int(text_hash[:8], 16)
        np.random.seed(seed)

        # Generate normalized random vector
        vector = np.random.normal(size=dimension)
        normalized = vector / np.linalg.norm(vector)

        return normalized.tolist()


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
                    uuid TEXT NOT NULL,
                    title TEXT NOT NULL,
                    account_key INTEGER NOT NULL,
                    account TEXT NOT NULL,
                    folder_key INTEGER NOT NULL,
                    folder TEXT NOT NULL,
                    note_id INTEGER NOT NULL,
                    primary_key INTEGER NOT NULL,
                    creation_time TIMESTAMP NOT NULL,
                    modify_time TIMESTAMP NOT NULL,
                    cloudkit_creator_id TEXT,
                    cloudkit_modifier_id TEXT,
                    cloudkit_last_modified_device TEXT,
                    is_pinned BOOLEAN NOT NULL,
                    is_password_protected BOOLEAN NOT NULL,
                    plaintext TEXT NOT NULL,
                    html TEXT NOT NULL,
                    embedded_objects TEXT,
                    hashtags TEXT,
                    mentions TEXT
                )
            """)

    def _ensure_connection(self) -> sqlite3.Connection:
        """Ensure we have a working connection with extensions loaded."""
        if self._connection is None:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            conn.enable_load_extension(True)

            # Load extensions
            package_root = Path(__file__).parent.parent
            lib_dir = package_root / "lib"
            extension_path = lib_dir / "rembed0.dylib"

            # Verify the path exists
            extension_path = lib_dir / "rembed0.dylib"
            if not extension_path.exists():
                raise FileNotFoundError(
                    f"sqlite-rembed extension not found at {extension_path}. "
                    "Please ensure the extension file is in the correct location."
                )

            conn.load_extension(str(extension_path))
            sqlite_vec.load(conn)

            # Register client in temp table
            conn.execute("""
                INSERT INTO temp.rembed_clients(name, options)
                VALUES (?, ?)
            """, [config.embedding.model_name, config.embedding.client_name])

            # conn.enable_load_extension(False)
            self._connection = conn

        return self._connection

    def setup(self) -> None:
        """Initial database setup."""
        try:
            conn = self._ensure_connection()

            # Test the setup
            sqlite_version, vec_version = conn.execute(
                "SELECT sqlite_version(), vec_version()"
            ).fetchone()
            logger.info("Database setup successful. SQLite version: %s, "
                        "sqlite-vec version: %s", sqlite_version, vec_version)

            # Verify rembed extension is loaded properly
            rembed_version = conn.execute("SELECT rembed_version()").fetchone()
            logger.info("sqlite-rembed version: %s", rembed_version[0])

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

            # conn.enable_load_extension(False)
            # conn.close()
        except Exception as e:
            logger.error("Failed to setup database: %s", e)
            raise

    def get_connection(self):
        """Get the database connection."""
        return self._ensure_connection()

    def close(self):
        """Close the database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None

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
