"""WebSocket handler for initializing setup"""
import json
from datetime import datetime
from typing import Dict, Any
from websockets.asyncio.server import ServerConnection

from .base import WebSocketHandler
from ...core.message_bus import SetupStartMessage


class SetupHandler(WebSocketHandler):
    """Handler for setup messages."""

    async def handle(self, websocket: ServerConnection, data: Dict[str, Any]) -> None:
        """Handle a setup message.

        This handler sends a setup start message to the message bus
        and returns the results to the client.

        Args:
            websocket (ServerConnection): The WebSocket connection.
            data (Dict): The message data
        """
        response = await self.message_bus.send(SetupStartMessage())

        if response["status"] == "success":
            await websocket.send(json.dumps({
                "type": "setup_results",
                "requestId": data["requestId"],
                "timestamp": datetime.now().timestamp(),
                "status": "success",
                "payload": {
                    "results": response
                }
            }))
        else:
            await websocket.send(json.dumps({
                "type": "setup_results",
                "requestId": data["requestId"],
                "timestamp": datetime.now().timestamp(),
                "status": "error",
                "payload": {
                    "results": response
                }
            }))
