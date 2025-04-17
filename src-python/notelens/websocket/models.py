"""
Type definitions for WebSocket messages.
"""
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Generic, TypeVar
from pydantic import BaseModel, Field


class MessageType(str, Enum):
    """Available WebSocket message types."""
    SEARCH_REQUEST = "search_request"
    SEARCH_RESULTS = "search_results"
    SETUP_START = "setup_start"
    SETUP_PROGRESS = "setup_progress"
    SETUP_COMPLETE = "setup_complete"
    ERROR = "error"
    PING = "ping"
    PONG = "pong"


class MessageStatus(str, Enum):
    """Message status values."""
    SUCCESS = "success"
    ERROR = "error"
    IN_PROGRESS = "in_progress"


class SetupStage(str, Enum):
    """Setup process stages."""
    INITIALIZING = "initializing"
    PARSING = "parsing"
    PROCESSING = "processing"


class SetupStatusType(str, Enum):
    """Specific status types for each setup stage."""
    # Initializing stage
    STARTING = "starting"
    CHECKING_SERVICES = "checking_services"
    SERVICES_READY = "services_ready"

    # Parsing stage
    READING_DATABASE = "reading_database"
    DATABASE_READ = "database_read"

    # Processing stage
    PREPARING_NOTES = "preparing_notes"
    PROCESSING_NOTES = "processing_notes"
    CLEANING_UP = "cleaning_up"

    # General statuses
    COMPLETED = "completed"
    FAILED = "failed"


class ErrorDetails(BaseModel):
    """Error details model."""
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


class BaseMessage(BaseModel):
    """Base class for all WebSocket messages."""
    type: MessageType
    request_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    status: MessageStatus


T = TypeVar("T")


class Response(BaseModel, Generic[T]):
    """Generic response wrapper."""
    type: MessageType
    request_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    status: MessageStatus
    payload: T


# Setup-specific models
class SetupStats(BaseModel):
    """Statistics for setup process."""
    total: Optional[int] = None
    new: int = 0
    modified: int = 0
    unchanged: int = 0
    deleted: int = 0
    in_trash: int = 0
    errors: int = 0


class SetupProgressPayload(BaseModel):
    """Payload for setup progress updates."""
    stage: SetupStage
    status_type: SetupStatusType
    processing: Optional[dict] = Field(default_factory=lambda: {
        "total_notes": None,
        "processed_notes": None,
        "current_note": None
    })
    stats: Optional[SetupStats] = None


class SetupCompletePayload(BaseModel):
    """Payload for setup completion message."""
    success: bool
    stats: Optional[SetupStats] = None
    error: Optional[str] = None


# Search-specific models
class SearchResultItem(BaseModel):
    """Individual search result item."""
    id: int
    title: str
    plaintext: str
    similarity_score: float
    # Add other fields as needed, matching Note model
    # but only including what's necessary for search results


class SearchResultsPayload(BaseModel):
    """Payload for search results."""
    results: List[SearchResultItem]


# Error response
class ErrorPayload(BaseModel):
    """Payload for error messages."""
    error: ErrorDetails


# Type aliases for common responses
SearchResponse = Response[SearchResultsPayload]
SetupProgressResponse = Response[SetupProgressPayload]
SetupCompleteResponse = Response[SetupCompletePayload]
ErrorResponse = Response[ErrorPayload]
