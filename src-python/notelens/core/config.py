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
class EmbeddingConfig:
    """Configuration for remote embeddings."""
    # Remote embeddings settings
    # API key defined in .env file
    client_name: str = "openai"
    model_name: str = "text-embedding-3-small"


@dataclass
class Config:
    """Global configuration for the application."""
    # Environment mode
    # DEV: Development mode (increase logging, etc.)
    # PROD: Production mode (minimal output, highest efficiency)
    env_mode = "DEV"

    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)

    def __post_init__(self):
        # Ensure the database directory exists
        self.database.db_path.parent.mkdir(parents=True, exist_ok=True)


# Global config instance
config = Config()
