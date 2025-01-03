"""
Configuration module for the application.
"""
from pathlib import Path
from dataclasses import dataclass, field
import sys


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

    # Testing configuration
    use_fake_embeddings: bool = True  # Toggle for fake embeddings
    fake_embedding_dim: int = 1536     # Match OpenAI's dimension


@dataclass
class RubyConfig:
    """Configuration for Ruby parser."""
    # Default to rbenv for now, should probably default to system Ruby for release
    ruby_path: Path = Path("~/.rbenv/shims/ruby").expanduser()

    # Default location for parser script
    # During development, this will point to vendor/apple_cloud_notes_parser
    # In production, PyInstaller will bundle this appropriately
    script_path: Path = field(default_factory=lambda: (
        # Check if running as bundled app
        Path(__file__).parent.parent.parent.parent / "vendor" / \
        "apple_cloud_notes_parser" / "notes_cloud_ripper.rb"
        if not getattr(sys, 'frozen', False)
        else Path(sys._MEIPASS) / "apple_cloud_notes_parser" / "notes_cloud_ripper.rb"  # pylint: disable=protected-access, no-member
        # TODO: Check above path after bundling
    ))

    def __post_init__(self):
        # Ensure the script exists during development
        if not self.script_path.exists() and not getattr(sys, 'frozen', False):
            raise FileNotFoundError(
                f"Ruby parser script not found at {self.script_path}. "
                "Please ensure the apple_cloud_notes_parser is cloned into the vendor directory."
            )


@dataclass
class AppleNotesConfig:
    """Configuration for Apple Notes database"""
    # Default Apple Notes database location on macOS
    db_path: Path = Path.home() / "Library" / "Group Containers" / \
        "group.com.apple.notes" / "NoteStore.sqlite"


@dataclass
class Config:
    """Global configuration for the application."""
    # Environment mode
    # DEV: Development mode (increase logging, etc.)
    # PROD: Production mode (minimal output, highest efficiency)
    env_mode: str = "DEV"

    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    ruby: RubyConfig = field(default_factory=RubyConfig)
    apple_notes: AppleNotesConfig = field(default_factory=AppleNotesConfig)

    def __post_init__(self):
        # Ensure the database directory exists
        self.database.db_path.parent.mkdir(parents=True, exist_ok=True)


# Global config instance
config = Config()
