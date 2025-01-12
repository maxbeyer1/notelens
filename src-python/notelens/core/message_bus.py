"""Message bus for inter-component communication.

Provides a centralized message bus for all application communications.
Prevents SQLite concurrency issues by serializing database operations 
and ensuring that only one operation is processed at a time.

Typical usage example:

    message_bus = MessageBus()
    await message_bus.send(MessageType.DB_SEARCH, payload={"query": "SELECT * FROM notes"})

"""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from asyncio import Queue
import uuid


class MessageType(Enum):
    """Enum for message types used in the message bus."""
    # Database operations
    DB_SEARCH = "db_search"
    DB_UPDATE = "db_update"
    # Watcher operations
    WATCHER_CHANGE = "watcher_change"
    # System operations
    SYSTEM_CONTROL = "system_control"
    # ... other message types


@dataclass
class Message:
    """
    Data class for messages sent through the message bus.

    Attributes:
        type (MessageType): The message type
        payload (Dict[str, Any]): The message payload
        reply_queue (Optional[Queue]): Optional reply queue for responses
        message_id (str): Unique message ID
        timestamp (float): Message timestamp
    """
    type: MessageType
    payload: Dict[str, Any]
    reply_queue: Optional[Queue] = None  # For responses if needed
    message_id: str = None
    timestamp: float = None

    def __post_init__(self):
        if self.message_id is None:
            self.message_id = str(uuid.uuid4())  # Generate a unique ID
        if self.timestamp is None:
            self.timestamp = datetime.now().timestamp()  # Current timestamp


class MessageBus:
    """
    Centralized message bus for all application communications.

    Attributes:
        main_queue (Queue[Message]): Main message queue
        _response_queues (Dict[str, Queue]): Response queues for message replies
    """

    def __init__(self):
        self.main_queue: Queue[Message] = Queue()
        self._response_queues: Dict[str, Queue] = {}

    async def send(self, message_type: MessageType, payload: Dict[str, Any]) -> Optional[Any]:
        """Send a message and optionally wait for response.

        Args:
            message_type (MessageType): The message type
            payload (Dict[str, Any]): The message payload

        Returns:
            Optional[Any]: The response payload if a response was received
        """
        reply_queue = Queue() if payload.get('needs_response', False) else None

        message = Message(
            type=message_type,
            payload=payload,
            reply_queue=reply_queue
        )

        if reply_queue:
            self._response_queues[message.message_id] = reply_queue

        await self.main_queue.put(message)

        if reply_queue:
            try:
                response = await reply_queue.get()
                return response
            finally:
                del self._response_queues[message.message_id]

        return None
