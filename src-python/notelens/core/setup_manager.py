"""Setup management for NoteLens."""
import logging
from typing import Dict, Any, Optional

from .message_bus import SetupStage, SetupProgressMessage

logger = logging.getLogger(__name__)


class SetupManager:
    """Manages the setup process and progress tracking."""

    def __init__(self, message_bus):
        self.message_bus = message_bus
        self.current_stage: Optional[SetupStage] = None
        self.total_notes: Optional[int] = None
        self.processed_notes = 0
        self.current_stats: Dict[str, int] = {
            'new': 0,
            'modified': 0,
            'unchanged': 0,
            'deleted': 0,
            'in_trash': 0,
            'errors': 0
        }

    async def start_stage(self, stage: SetupStage, status: str):
        """Start a new setup stage."""
        self.current_stage = stage
        await self._send_progress(status)
        logger.info("Starting setup stage: %s - %s", stage.name, status)

    async def set_total_notes(self, total: int):
        """Set the total number of notes to be processed."""
        self.total_notes = total
        await self._send_progress("Starting note processing")

    async def update_note_progress(self, note_title: str, stats_update: Dict[str, int]):
        """Update progress for a single processed note."""
        self.processed_notes += 1
        # Update running statistics
        for key, value in stats_update.items():
            if key in self.current_stats:
                self.current_stats[key] += value

        await self._send_progress(
            f"Processing note: {note_title}",
            note_title
        )

    async def complete_stage(self, status: str):
        """Mark the current stage as complete."""
        await self._send_progress(status)
        logger.info("Completed setup stage: %s - %s",
                    self.current_stage.name, status)

    async def _send_progress(self, status: str, current_note: Optional[str] = None):
        """Send progress update through the message bus."""
        await self.message_bus.send(SetupProgressMessage(
            stage=self.current_stage,
            status=status,
            total_notes=self.total_notes,
            processed_notes=self.processed_notes,
            current_note=current_note,
            stats=self.current_stats.copy() if self.current_stats else None
        ))
