"""
Configuration module for the application.
"""
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class DatabaseConfig:
    """Configuration for the database."""
    # Using the standard macOS Application Support directory
    db_path: Path = Path.home() / "Library" / "Application Support" / \
        "NoteLens" / "notelens.db"
    vector_dimension: int = 1536  # OpenAI's default embedding dimension


@dataclass
class Config:
    """Global configuration for the application."""
    database: DatabaseConfig = field(default_factory=DatabaseConfig)

    def __post_init__(self):
        # Ensure the database directory exists
        self.database.db_path.parent.mkdir(parents=True, exist_ok=True)


# Global config instance
config = Config()
