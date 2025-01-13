"""Handler for ping messages (mainly used for debugging)."""
import json
from datetime import datetime
from typing import Dict, Any
from websockets.asyncio.server import ServerConnection

from .base import WebSocketHandler


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
