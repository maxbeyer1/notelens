"""Message bus for inter-component communication.

Provides a centralized message bus for all application communications.
Prevents SQLite concurrency issues by serializing database operations
and ensuring that only one operation is processed at a time.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, Optional, TypeVar, Union, Generic
from asyncio import Queue, QueueEmpty
import uuid


class SystemAction(Enum):
    """Available system control actions."""
    START = auto()
    STOP = auto()


class SetupStage(Enum):
    """Available setup stages."""
    INITIALIZING = auto()     # Database initialization
    PARSING = auto()          # Running the Ruby parser
    PROCESSING = auto()       # Processing notes into database


@dataclass(kw_only=True)
class MessageBase:
    """Base class for all message payloads.

    Attributes:
        message_id (str): Unique identifier for the message.
        timestamp (float): Timestamp of when the message was created.
        needs_response (bool): Whether a response is expected.
    """
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(
        default_factory=lambda: datetime.now().timestamp())
    needs_response: bool = False


# Database Messages
@dataclass(kw_only=True)
class SearchMessage(MessageBase):
    """Message for database search requests.

    Attributes:
        query (str): SQL query to execute.
        limit (int): Maximum number of results to return.
    """
    query: str
    limit: int
    needs_response: bool = True


@dataclass(kw_only=True)
class DatabaseUpdateMessage(MessageBase):
    """Message for database updates.

    Attributes:
        table (str): Name of the database table to update.
        values (Dict[str, Any]): Key-value pairs to update in the table.
    """
    table: str
    values: Dict[str, Any]


# Watcher Messages
@dataclass(kw_only=True)
class WatcherChangeMessage(MessageBase):
    """Message for file system changes."""
    path: str


# System Messages
@dataclass(kw_only=True)
class SystemControlMessage(MessageBase):
    """Message for system control operations."""
    action: SystemAction
    needs_response: bool = True


@dataclass(kw_only=True)
class SystemStatusMessage(MessageBase):
    """Message for system status updates."""
    status: str
    details: Optional[Dict[str, Any]] = None


# Setup Messages
@dataclass(kw_only=True)
class SetupStartMessage(MessageBase):
    """Message to initiate setup process."""
    needs_response: bool = True


@dataclass(kw_only=True)
class SetupProgressMessage(MessageBase):
    """Message for setup progress updates."""
    stage: SetupStage
    status: str
    total_notes: Optional[int] = None
    processed_notes: Optional[int] = None
    current_note: Optional[str] = None  # Title or identifier of current note
    stats: Optional[Dict[str, int]] = None  # Running statistics


@dataclass(kw_only=True)
class SetupCompleteMessage(MessageBase):
    """Message for setup completion notification."""
    success: bool
    stats: Optional[Dict[str, int]] = None  # Final statistics
    error: Optional[str] = None


# Type union of all possible messages
MessageType = Union[
    SearchMessage,
    DatabaseUpdateMessage,
    WatcherChangeMessage,
    SystemControlMessage,
    SystemStatusMessage,
    SetupStartMessage,
    SetupProgressMessage,
    SetupCompleteMessage,
]

T = TypeVar('T')


@dataclass
class Message(Generic[T]):
    """Container for messages with type information."""
    payload: T
    reply_queue: Optional[Queue] = None


class MessageBus:
    """
    Centralized message bus for all application communications.

    Attributes:
        main_queue (Queue[Message]): Main message queue
        _response_queues (Dict[str, Queue]): Response queues for message replies
    """

    def __init__(self):
        self.main_queue: Queue[Message] = Queue()
        self.priority_queue: Queue[Message] = Queue()
        self._response_queues: Dict[str, Queue] = {}

    def _is_priority_message(self, payload: MessageType) -> bool:
        """Determine if a message should be handled with priority."""
        return isinstance(payload, (
            SetupProgressMessage,
            SystemStatusMessage
        ))

    async def send(self, payload: MessageType) -> Optional[Any]:
        """Send a message and optionally wait for response.

        Args:
            payload (MessageType): The message payload to send

        Returns:
            Optional[Any]: The response payload if a response was received
        """
        reply_queue = Queue() if payload.needs_response else None

        message = Message(
            payload=payload,
            reply_queue=reply_queue
        )

        if reply_queue:
            self._response_queues[payload.message_id] = reply_queue

        # Route to appropriate queue
        if self._is_priority_message(payload):
            await self.priority_queue.put(message)
        else:
            await self.main_queue.put(message)

        if reply_queue:
            try:
                response = await reply_queue.get()
                return response
            finally:
                del self._response_queues[payload.message_id]

        return None

    async def get_next_message(self) -> Message:
        """Get the next message to process, prioritizing the priority queue.

        This method is used to get messages in the correct order.
        Priority messages are always processed before main queue messages.

        Returns:
            The next message to process, if any
        """
        # Always check priority queue first
        try:
            return self.priority_queue.get_nowait()
        except QueueEmpty:
            # If priority queue is empty, check main queue
            return await self.main_queue.get()

    def task_done(self, was_priority: bool):
        """Mark a task as done in the appropriate queue."""
        if was_priority:
            self.priority_queue.task_done()
        else:
            self.main_queue.task_done()

    def handle_message(self, message: Message) -> None:
        """Message handler type hint helper.

        This method serves as a type hint helper for implementing message handlers.
        Actual handlers should use pattern matching or isinstance checks.

        Example:
            async def handle_message(self, message: Message):
                payload = message.payload

                if isinstance(payload, SearchMessage):
                    results = await self.perform_search(payload.query, payload.limit)
                    if message.reply_queue:
                        await message.reply_queue.put(results)

                elif isinstance(payload, SystemControlMessage):
                    if payload.action == SystemAction.START:
                        await self.start_system()
                    # ...
        """
