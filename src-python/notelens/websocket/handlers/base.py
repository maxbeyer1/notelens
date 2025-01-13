"""Base class for WebSocket message handlers."""
from abc import ABC, abstractmethod
from typing import Dict, Any
from websockets.asyncio.server import ServerConnection

from ...core.message_bus import MessageBus


class WebSocketHandler(ABC):
    """Base class for WebSocket message handlers."""

    def __init__(self, message_bus: MessageBus):
        self.message_bus = message_bus

    @abstractmethod
    async def handle(self, websocket: ServerConnection, data: Dict[str, Any]) -> None:
        """Handle a message."""
        pass
