"""WebSocket handler for search-related messages."""
import json
from datetime import datetime
from typing import Dict, Any
from websockets.asyncio.server import ServerConnection

from .base import WebSocketHandler
from ...core.message_bus import MessageType


class SearchHandler(WebSocketHandler):
    """Handler for search-related messages."""

    async def handle(self, websocket: ServerConnection, data: Dict[str, Any]) -> None:
        """Handle a search message.

        This handler sends a search query to the database via the message bus
        and returns the results to the client.

        Args:
            websocket (ServerConnection): The WebSocket connection.
            data (Dict): The message data
        """
        response = await self.message_bus.send(
            MessageType.DB_SEARCH,
            {
                "needs_response": True,
                "query": data["payload"]["query"],
                "limit": data["payload"].get("limit", 10),
                "websocket_request_id": data["requestId"]
            }
        )

        await websocket.send(json.dumps({
            "type": "search_results",
            "requestId": data["requestId"],
            "timestamp": datetime.now().timestamp(),
            "status": "success",
            "payload": {
                "results": response
            }
        }))
