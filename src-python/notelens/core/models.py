"""
Models for NoteLens data objects.
"""
from datetime import datetime
from typing import List, Optional, Dict
import json
from pydantic import BaseModel, Field, field_validator


class Note(BaseModel):
    """
    Unified Note model for both validation and database operations.
    Handles both input validation and database serialization.
    """
    account_key: int
    account: str
    folder_key: int
    folder: str
    note_id: int
    uuid: str
    primary_key: int
    creation_time: datetime
    modify_time: datetime
    cloudkit_creator_id: Optional[str] = None
    cloudkit_modifier_id: Optional[str] = None
    cloudkit_last_modified_device: Optional[str] = None
    is_pinned: bool = False
    is_password_protected: bool = False
    title: str
    plaintext: str
    html: str
    embedded_objects: List[Dict] = Field(default_factory=list)
    hashtags: List[str] = Field(default_factory=list)
    mentions: List[str] = Field(default_factory=list)

    @field_validator('creation_time', 'modify_time', mode='before')
    @classmethod
    def parse_datetime(cls, value: str | datetime) -> datetime:
        """Convert string timestamps to datetime objects"""
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                # First try the original format
                return datetime.strptime(value, "%Y-%m-%d %H:%M:%S %z")
            except ValueError:
                try:
                    # Then try ISO format
                    return datetime.fromisoformat(value)
                except ValueError as e:
                    raise ValueError(f"Invalid datetime format: {e}") from e
        raise ValueError(f"Expected string or datetime, got {type(value)}")

    def to_db_dict(self) -> dict:
        """Convert note to a database-friendly dictionary"""
        data = self.model_dump()
        # Convert datetime objects to ISO format strings
        data['creation_time'] = self.creation_time.isoformat()
        data['modify_time'] = self.modify_time.isoformat()
        # Serialize lists and dicts to JSON strings for SQLite storage
        data['embedded_objects'] = json.dumps(self.embedded_objects)
        data['hashtags'] = ','.join(self.hashtags)
        data['mentions'] = ','.join(self.mentions)
        return data

    @classmethod
    def from_db_dict(cls, db_dict: dict) -> 'Note':
        """Create a Note instance from a database dictionary"""
        # Create a copy to avoid modifying the original
        db_dict = db_dict.copy()

        # Convert stored JSON string to list of dicts
        if isinstance(db_dict.get('embedded_objects'), str):
            try:
                db_dict['embedded_objects'] = json.loads(
                    db_dict['embedded_objects'])
            except json.JSONDecodeError as e:
                raise ValueError(
                    f"Invalid JSON in embedded_objects: {e}") from e

        # Convert comma-separated strings to lists
        if isinstance(db_dict.get('hashtags'), str):
            db_dict['hashtags'] = [
                tag.strip()
                for tag in db_dict['hashtags'].split(',')
                if tag.strip()
            ]

        if isinstance(db_dict.get('mentions'), str):
            db_dict['mentions'] = [
                mention.strip()
                for mention in db_dict['mentions'].split(',')
                if mention.strip()
            ]

        return cls(**db_dict)

    model_config = {
        "validate_assignment": True,
        "arbitrary_types_allowed": True,
        "frozen": True  # Makes instances immutable for better safety
    }
