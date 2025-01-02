"""
Service layer for managing notes and vector search operations.
"""
from typing import List, Optional, Dict
import logging
from datetime import datetime

from ..core.models import Note
from ..core.database import DatabaseManager
from ..core.config import config

logger = logging.getLogger(__name__)


class NoteService:
    """Service class for managing notes and performing vector searches."""

    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize the notes service.

        Args:
            db_manager: Database manager instance.
        """
        self.db_manager = db_manager
        logger.info("Note service initialized")

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
                # Insert note data
                cursor = conn.execute(
                    """
                    INSERT INTO notes (
                        uuid, title, account_key, account, folder_key, folder,
                        note_id, primary_key, creation_time, modify_time,
                        cloudkit_creator_id, cloudkit_modifier_id,
                        cloudkit_last_modified_device, is_pinned,
                        is_password_protected, plaintext, html,
                        embedded_objects, hashtags, mentions
                    ) VALUES (
                        :uuid, :title, :account_key, :account, :folder_key, 
                        :folder, :note_id, :primary_key, :creation_time,
                        :modify_time, :cloudkit_creator_id, :cloudkit_modifier_id,
                        :cloudkit_last_modified_device, :is_pinned,
                        :is_password_protected, :plaintext, :html,
                        :embedded_objects, :hashtags, :mentions
                    )
                    """,
                    note.to_db_dict()
                )

                note_id = cursor.lastrowid

                # Generate and store embedding
                embedding = conn.execute(
                    "SELECT rembed(?, ?)",
                    [config.embedding.model_name, note.plaintext]
                ).fetchone()[0]

                # Store embedding
                conn.execute(
                    "INSERT INTO note_embeddings (rowid, embedding) VALUES (?, ?)",
                    [note_id, embedding]
                )

                # conn.commit()
                return self.get_note(note_id)

            except Exception as e:
                # conn.rollback()
                logger.error("Failed to create note: %s", e)
                raise

    def update_note(self, note: Note) -> None:
        """
        Update an existing note and its embedding.

        Args:
            note: Updated note data

        Returns:
            Updated note if successful, None if note not found
        """
        try:
            with self.db_manager.get_connection() as conn:
                # Update note data
                cursor = conn.execute(
                    """
                        UPDATE notes SET
                            title = :title,
                            account_key = :account_key,
                            account = :account,
                            folder_key = :folder_key,
                            folder = :folder,
                            note_id = :note_id,
                            primary_key = :primary_key,
                            creation_time = :creation_time,
                            modify_time = :modify_time,
                            cloudkit_creator_id = :cloudkit_creator_id,
                            cloudkit_modifier_id = :cloudkit_modifier_id,
                            cloudkit_last_modified_device = :cloudkit_last_modified_device,
                            is_pinned = :is_pinned,
                            is_password_protected = :is_password_protected,
                            plaintext = :plaintext,
                            html = :html,
                            embedded_objects = :embedded_objects,
                            hashtags = :hashtags,
                            mentions = :mentions
                        WHERE uuid = :uuid
                        """,
                    note.to_db_dict()
                )

                if cursor.rowcount == 0:
                    raise ValueError(f"Note with UUID {note.uuid} not found")

                # Update embedding
                note_id = conn.execute(
                    "SELECT id FROM notes WHERE uuid = ?",
                    [note.uuid]
                ).fetchone()[0]

                embedding = conn.execute(
                    "SELECT rembed(?, ?)",
                    [config.embedding.model_name, note.plaintext]
                ).fetchone()[0]

                conn.execute(
                    "UPDATE note_embeddings SET embedding = ? WHERE rowid = ?",
                    [embedding, note_id]
                )

                # conn.commit()
                # return self.get_note(note_id)
                logger.info("Updated note: %s", note.title)
        except Exception as e:
            # conn.rollback()
            logger.error("Failed to update note: %s", e)
            raise

    def delete_note(self, uuid: int) -> bool:
        """
        Delete a note and its embedding.

        Args:
            uuid: UUID of the note to delete

        Returns:
            True if note was deleted, False if note not found
        """
        try:
            with self.db_manager.get_connection() as conn:
                # Get note ID first
                result = conn.execute(
                    "SELECT id FROM notes WHERE uuid = ?",
                    [uuid]
                ).fetchone()

                if not result:
                    raise ValueError(f"Note with UUID {uuid} not found")

                note_id = result[0]

                # Delete note and its embedding
                conn.execute("DELETE FROM notes WHERE id = ?", [note_id])
                conn.execute(
                    "DELETE FROM note_embeddings WHERE rowid = ?", [note_id])

                logger.info("Deleted note with UUID: %s", uuid)

        except Exception as e:
            logger.error("Failed to delete note: %s", e)
            raise

    def get_note(self, uuid: str) -> Optional[Note]:
        """
        Retrieve a note by its UUID.

        Args:
            uuid: UUID of the note to retrieve

        Returns:
            Note object if found, None otherwise
        """
        try:
            with self.db_manager.get_connection() as conn:
                row = conn.execute(
                    "SELECT * FROM notes WHERE uuid = ?",
                    [uuid]
                ).fetchone()

                if row:
                    return Note.from_db_dict(dict(row))
                return None
        except Exception as e:
            logger.error("Failed to retrieve note: %s", str(e))
            raise

    def get_notes_by_uuids(self, uuids: List[str]) -> List[Note]:
        """Retrieve multiple notes by their UUIDs.

        Args:
            uuids: List of UUIDs to retrieve

        Returns:
            List of Note objects
        """
        try:
            with self.db_manager.get_connection() as conn:
                placeholders = ','.join('?' * len(uuids))
                rows = conn.execute(
                    f"SELECT * FROM notes WHERE uuid IN ({placeholders})",
                    uuids
                ).fetchall()

                return [Note.from_db_dict(dict(row)) for row in rows]
        except Exception as e:
            logger.error("Error retrieving notes: %s", str(e))
            raise

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
