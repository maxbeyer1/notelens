"""Note tracking and processing functionality."""
import logging
import asyncio
from typing import Dict, Optional, Set

from .service import NoteService
from ..core.models import Note
from ..core.config import config
from ..core.setup_manager import SetupManager

logger = logging.getLogger(__name__)


class NoteTracker:
    """Tracks and processes changes to notes."""

    def __init__(self, note_service: NoteService, setup_manager: Optional[SetupManager] = None):
        """Initialize the note tracker.

        Args:
            note_service: NoteService instance.
        """
        self.note_service = note_service
        self.setup_manager = setup_manager
        logger.info("Note tracker initialized")

    def _get_trash_folder_id(self, parser_data: Dict) -> Optional[str]:
        """Get the folder ID for the Recently Deleted folder.

        Args:
            parser_data: The complete parser data dictionary.

        Returns:
            The trash folder ID if found, None otherwise.
        """
        for folder_id, folder in parser_data.get('folders', {}).items():
            if folder.get('uuid') == "TrashFolder-CloudKit":
                return str(folder_id)
        return None

    def _get_existing_note_uuids(self, current_notes: Dict[str, Dict]) -> Set[str]:
        """Get UUIDs of existing notes that match the current notes.

        Args:
            current_notes: Dictionary of current notes from parser

        Returns:
            Set of UUIDs for existing notes
        """
        existing_uuids = set()
        # Get all notes that exist in database
        if current_notes:
            note_uuids = [note_data['uuid']
                          for note_data in current_notes.values()]
            existing_notes = self.note_service.get_notes_by_uuids(note_uuids)
            existing_uuids = {note.uuid for note in existing_notes}

        return existing_uuids

    async def process_notes(self, parser_data: Dict) -> Dict:
        """Process notes from parser output.

        Args:
            parser_data: Dictionary containing the parsed notes data.

        Returns:
            Dictionary containing processing statistics.

        Raises:
            ValueError: If parser_data is invalid or missing required data.
        """
        if not parser_data or 'notes' not in parser_data:
            logger.warning("No notes data in parser output")
            raise ValueError("Invalid parser data: missing 'notes' key")

        notes_data = parser_data['notes']
        logger.info("Processing %d notes from parser", len(notes_data))

        # Initialize statistics
        stats = {
            'total': len(notes_data),
            'new': 0,
            'modified': 0,
            'unchanged': 0,
            'deleted': 0,
            'in_trash': 0,
            'errors': 0
        }

        # Get trash folder ID
        trash_folder_id = self._get_trash_folder_id(parser_data)
        if not trash_folder_id:
            logger.warning("Could not find Recently Deleted folder ID")
        else:
            logger.info("Trash folder ID: %s", trash_folder_id)

        # Process current notes (excluding trash)
        current_notes: Dict[str, Dict] = {}
        for id_key, note_data in notes_data.items():
            try:
                if not note_data.get('uuid'):
                    logger.warning("Skipping note without UUID")
                    continue

                # Skip notes in trash
                if trash_folder_id and str(note_data.get('folder_key')) == str(trash_folder_id):
                    stats['in_trash'] += 1
                    logger.debug("Skipping note in trash: %s",
                                 note_data.get('title'))
                    continue

                current_notes[note_data['uuid']] = note_data

                if self.setup_manager:
                    await self.setup_manager.set_total_notes(len(current_notes))

            except Exception as e:
                logger.error("Error processing note data: %s",
                             str(e), exc_info=True)
                stats['errors'] += 1
                continue

        try:
            # Get existing notes
            existing_uuids = self._get_existing_note_uuids(current_notes)
            print("existing_uuids:", existing_uuids)

            # Get current note items
            note_items = current_notes.items()

            # Process current notes with progress bar in DEV mode
            # if config.env_mode == "DEV":
            #     note_items = tqdm(
            #         note_items,
            #         total=len(current_notes),
            #         desc="Processing notes",
            #         unit="note"
            #     )

            # Process each current note
            for uuid, note_data in note_items:
                try:
                    note = Note(**note_data)
                    note_stats_update = {
                        'new': 0,
                        'modified': 0,
                        'unchanged': 0,
                        'errors': 0
                    }

                    if uuid not in existing_uuids:
                        # New note
                        self.note_service.create_note(note)
                        note_stats_update['new'] = 1
                        stats['new'] += 1
                        logger.debug("Created new note: %s", note.title)
                    else:
                        # Check if note needs updating
                        existing_note = self.note_service.get_note(uuid)
                        if existing_note and note.modify_time > existing_note.modify_time:
                            self.note_service.update_note(note)
                            note_stats_update['modified'] = 1
                            stats['modified'] += 1
                            logger.debug("Updated note: %s", note.title)
                        else:
                            note_stats_update['unchanged'] = 1
                            stats['unchanged'] += 1
                            logger.debug("Note unchanged: %s", note.title)

                    # Update progress manager
                    if self.setup_manager:
                        self.setup_manager.update_note_progress(
                            note.title, note_stats_update)

                    await asyncio.sleep(0)

                except Exception as e:
                    logger.error("Error processing note %s: %s", uuid, str(e))
                    stats['errors'] += 1
                    if self.setup_manager:
                        await self.setup_manager.update_note_progress(
                            note_data.get('title', 'Unknown'),
                            {'errors': 1}
                        )
                    continue

            # Process deletions by comparing sets of UUIDs
            deleted_uuids = existing_uuids - set(current_notes.keys())
            for uuid in deleted_uuids:
                try:
                    self.note_service.delete_note(uuid)
                    stats['deleted'] += 1
                    logger.info("Deleted note: %s", uuid)
                except Exception as e:
                    logger.error("Error deleting note %s: %s", uuid, str(e))
                    stats['errors'] += 1

        except Exception as e:
            logger.error("Error in note processing: %s", str(e), exc_info=True)
            raise

        # Log summary
        logger.info("Note processing complete:")
        logger.info("  Total notes seen: %d", stats['total'])
        logger.info("  Notes in trash: %d", stats['in_trash'])
        logger.info("  Notes processed: %d", len(current_notes))
        logger.info("  New notes: %d", stats['new'])
        logger.info("  Modified notes: %d", stats['modified'])
        logger.info("  Unchanged notes: %d", stats['unchanged'])
        logger.info("  Deleted notes: %d", stats['deleted'])
        logger.info("  Errors encountered: %d", stats['errors'])

        return stats
