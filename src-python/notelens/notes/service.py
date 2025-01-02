"""
Service layer for managing notes and vector search operations.
"""
from typing import List, Optional, Dict
import logging
from datetime import datetime
from contextlib import contextmanager

from ..core.models import Note
from ..core.database import DatabaseManager, VectorUtils
from ..core.config import config

logger = logging.getLogger(__name__)


class NotesService:
    """Service class for managing notes and performing vector searches."""

    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize the notes service.

        Args:
            db_manager: Database manager instance.
        """
        self.db_manager = db_manager

    def create_note(self, note: Note) -> Note:
        """
        Create a new note and generate its embedding.

        Args:
            note: Note object to create

        Returns:
            Created note with updated database ID
        """
        with self.db_manager.get_connection() as conn:
            try:
                # Convert note to database-friendly dictionary
                note_data = note.to_db_dict()

                # Insert note data
                cursor = conn.execute("""
                    INSERT INTO notes (uuid, title, account_key, account, folder_key, folder, note_id, primary_key, creation_time, modify_time, cloudkit_creator_id, cloudkit_modifier_id, cloudkit_last_modified_device, is_pinned, is_password_protected, plaintext, html, embedded_objects, hashtags, mentions)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (note_data["uuid"], note_data["title"], note_data["account_key"], note_data["account"], note_data["folder_key"], note_data["folder"], note_data["note_id"], note_data["primary_key"], note_data["creation_time"], note_data["modify_time"], note_data["cloudkit_creator_id"], note_data["cloudkit_modifier_id"], note_data["cloudkit_last_modified_device"], note_data["is_pinned"], note_data["is_password_protected"], note_data["plaintext"], note_data["html"], note_data["embedded_objects"], note_data["hashtags"], note_data["mentions"]))

                note_id = cursor.lastrowid

                # Generate and store embedding
                embedding = conn.execute(
                    "SELECT rembed(?, ?)",
                    [config.embedding.model_name, note_data["plaintext"]]
                ).fetchone()[0]

                # Store embedding
                conn.execute(
                    "INSERT INTO note_embeddings (rowid, embedding) VALUES (?, ?)",
                    [note_id, embedding]
                )

                conn.commit()
                return self.get_note(note_id)

            except Exception as e:
                conn.rollback()
                logger.error("Failed to create note: %s", e)
                raise

    def get_note(self, note_id: int) -> Optional[Note]:
        """
        Retrieve a note by its ID.

        Args:
            note_id: ID of the note to retrieve

        Returns:
            Note object if found, None otherwise
        """
        with self.db_manager.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM notes WHERE id = ?",
                [note_id]
            ).fetchone()

            if row:
                return Note.from_db_dict(dict(row))
            return None

    def update_note(self, note_id: int, note: Note) -> Optional[Note]:
        """
        Update an existing note and its embedding.

        Args:
            note_id: ID of the note to update
            note: Updated note data

        Returns:
            Updated note if successful, None if note not found
        """
        with self.db_manager.get_connection() as conn:
            # Update note data
            result = conn.execute("""
                UPDATE notes
                SET title = ?, content = ?, updated_at = ?
                WHERE id = ?
            """, (note.title, note.plaintext, datetime.now(), note_id))

            if result.rowcount == 0:
                return None

            # Update embedding
            embedding = conn.execute(
                f"SELECT rembed('{config.embedding.model_name}', ?)",
                [note.plaintext]
            ).fetchone()[0]

            conn.execute("""
                INSERT OR REPLACE INTO note_embeddings (rowid, embedding)
                VALUES (?, ?)
            """, [note_id, embedding])

            conn.commit()
            return self.get_note(note_id)

    def delete_note(self, note_uuid: int) -> bool:
        """
        Delete a note and its embedding.

        Args:
            note_uuid: UUID of the note to delete

        Returns:
            True if note was deleted, False if note not found
        """
        with self.db_manager.get_connection() as conn:
            result = conn.execute(
                "DELETE FROM notes WHERE uuid = ?", [note_uuid])
            if result.rowcount > 0:
                conn.execute(
                    "DELETE FROM note_embeddings WHERE rowid = ?", [result.lastrowid])

                conn.commit()
                return True

            return False

    def search_notes(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Perform semantic search on notes.

        Args:
            query: Search query text
            limit: Maximum number of results to return

        Returns:
            List of notes with their similarity scores
        """
        with self.db_manager.get_connection() as conn:
            # Generate embedding for the query
            query_embedding = conn.execute(
                f"SELECT rembed('{config.embedding.model_name}', ?)",
                [query]
            ).fetchone()[0]

            # Perform vector search
            results = conn.execute("""
                WITH matches AS (
                    SELECT rowid, distance
                    FROM note_embeddings
                    WHERE embedding MATCH ?
                    ORDER BY distance
                    LIMIT ?
                )
                SELECT n.*, m.distance
                FROM matches m
                JOIN notes n ON n.id = m.rowid
                ORDER BY m.distance
            """, [query_embedding, limit]).fetchall()

            return [
                {
                    **dict(row),
                    # Convert distance to similarity
                    'similarity_score': 1 - row['distance']
                }
                for row in results
            ]

    def find_similar_notes(self, note_id: int, limit: int = 5) -> List[Dict]:
        """
        Find notes similar to a given note.

        Args:
            note_id: ID of the reference note
            limit: Maximum number of similar notes to return

        Returns:
            List of similar notes with their similarity scores
        """
        with self.db_manager.get_connection() as conn:
            # Get the embedding for the reference note
            ref_embedding = conn.execute("""
                SELECT embedding FROM note_embeddings WHERE rowid = ?
            """, [note_id]).fetchone()

            if not ref_embedding:
                return []

            # Find similar notes
            results = conn.execute("""
                WITH matches AS (
                    SELECT rowid, distance
                    FROM note_embeddings
                    WHERE embedding MATCH ?
                    AND rowid != ?
                    ORDER BY distance
                    LIMIT ?
                )
                SELECT n.*, m.distance
                FROM matches m
                JOIN notes n ON n.id = m.rowid
                ORDER BY m.distance
            """, [ref_embedding[0], note_id, limit]).fetchall()

            return [
                {
                    **dict(row),
                    'similarity_score': 1 - row['distance']
                }
                for row in results
            ]
