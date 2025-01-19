"""Setup management for NoteLens."""
import logging
import asyncio
from typing import Dict, Any, Optional

from .message_bus import MessageBus, SetupStage, SetupProgressMessage
from ..websocket.server import NoteLensWebSocket

logger = logging.getLogger(__name__)


class SetupManager:
    """Manages the setup process and progress tracking."""

    def __init__(self, message_bus: MessageBus, websocket_server: NoteLensWebSocket):
        self.message_bus = message_bus
        self.websocket_server = websocket_server

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

        # Get event loop for broadcasting
        self._loop = asyncio.get_event_loop()

    async def start_stage(self, stage: SetupStage, status: str):
        """Start a new setup stage."""
        self.current_stage = stage
        await self._send_progress(status)
        logger.info("Starting setup stage: %s - %s", stage.name, status)

    async def set_total_notes(self, total: int):
        """Set the total number of notes to be processed."""
        self.total_notes = total
        await self._send_progress("Starting note processing")

    def update_note_progress(self, note_title: str, stats_update: Dict[str, int]):
        """Update progress for a single processed note."""
        self.processed_notes += 1
        # Update running statistics
        for key, value in stats_update.items():
            if key in self.current_stats:
                self.current_stats[key] += value

        # await self._send_progress(
        #     f"Processing note: {note_title}",
        #     note_title
        # )

        # Create a fire-and-forget task for the progress update
        # asyncio.create_task(
        #     self.websocket_server.broadcast({
        #         "type": "setup_progress",
        #         "stage": "processing",
        #         "status": f"Processing note: {note_title}",
        #         "current_note": note_title,
        #         "processed_notes": self.processed_notes,
        #         "total_notes": self.total_notes,
        #         "stats": self.current_stats.copy()  # Send a copy to avoid race conditions
        #     })
        # )

        # Create the message
        message = {
            "type": "setup_progress",
            "stage": "processing",
            "status": f"Processing note: {note_title}",
            "current_note": note_title,
            "processed_notes": self.processed_notes,
            "total_notes": self.total_notes,
            "stats": self.current_stats.copy()  # Send a copy to avoid race conditions
        }

        try:
            # Schedule the broadcast in the event loop without awaiting
            future = asyncio.run_coroutine_threadsafe(
                self.websocket_server.broadcast(message),
                self._loop
            )
            # Optional: Add callback to handle any errors
            future.add_done_callback(lambda f:
                                     logger.error(f"Broadcast error: {
                                                  f.exception()}") if f.exception() else None
                                     )
        except Exception as e:
            logger.error(f"Failed to schedule broadcast: {e}")

    async def complete_stage(self, status: str):
        """Mark the current stage as complete."""
        await self._send_progress(status)
        logger.info("Completed setup stage: %s - %s",
                    self.current_stage.name, status)

    async def _send_progress(self, status: str, current_note: Optional[str] = None):
        """Send progress update through the message bus."""
        logger.debug("Sending setup progress: %s", status)
        # await self.message_bus.send(SetupProgressMessage(
        #     stage=self.current_stage,
        #     status=status,
        #     total_notes=self.total_notes,
        #     processed_notes=self.processed_notes,
        #     current_note=current_note,
        #     stats=self.current_stats.copy() if self.current_stats else None
        # ))

        # Send progress update to WebSocket clients
        await self.websocket_server.broadcast(
            {
                "type": "setup_progress",
                "stage": self.current_stage.name.lower(),
                "status": status,
                "total_notes": self.total_notes,
                "processed_notes": self.processed_notes,
                "current_note": current_note,
                "stats": self.current_stats.copy() if self.current_stats else None
            }
        )
