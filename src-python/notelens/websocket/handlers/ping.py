import json
from datetime import datetime
from typing import Dict, Any
from websockets.asyncio.server import ServerConnection

from .base import WebSocketHandler
from ...core.message_bus import MessageBus


class PingHandler(WebSocketHandler):
    """Handler for ping messages."""

    async def handle(self, websocket: ServerConnection, data: Dict[str, Any]) -> None:
        """Handle a ping message."""
        await websocket.send(json.dumps({
            "type": "pong",
            "requestId": data.get("requestId"),
            "timestamp": datetime.now().timestamp(),
            "payload": None,
            "status": "success"
        }))
