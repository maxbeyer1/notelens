"""
Basic parser implementation for apple_cloud_notes_parser integration.
"""
import json
import logging
import subprocess
import os
from datetime import datetime
import shutil
from pathlib import Path
from typing import Dict, Optional

from ...core.config import config
from .exceptions import (DatabaseAccessError,
                         OutputError, ParserExecutionError,
                         ParserNotFoundError, RubyEnvironmentError)

logger = logging.getLogger(__name__)


class NotesParser:
    """
    Handles interaction with apple_cloud_notes_parser Ruby script.
    """
    # Constants
    PARSER_TIMEOUT = 60  # seconds
    MAX_RETRIES = 3
    REQUIRED_GEMS = ['sqlite3', 'json']
    MIN_RUBY_VERSION = (3, 0, 0)

    def __init__(self):
        """
        Initialize the parser with configuration from the global config.
        """
        self.ruby_path = config.ruby.ruby_path
        self.ruby_script_path = config.ruby.script_path
        self.parser_dir = self.ruby_script_path.parent

        # Setup and verify environment
        self._setup_ruby_environment()
        self._verify_installations()

        # Create temp directory if it doesn't exist
        self.temp_base.mkdir(parents=True, exist_ok=True)

    @property
    def temp_base(self) -> Path:
        """Base directory for temporary files."""
        temp_dir = Path.home() / "Library" / "Application Support" / "NoteLens" / "temp"
        temp_dir.mkdir(parents=True, exist_ok=True)
        return temp_dir

    def _verify_installations(self) -> None:
        """Verify Ruby and parser installations."""
        if not self.ruby_script_path.exists():
            raise ParserNotFoundError(
                f"Parser not found at: {self.ruby_script_path}")

        # Check Ruby version
        try:
            result = subprocess.run(
                [self.ruby_path, '--version'],
                capture_output=True,
                text=True,
                check=True
            )
            version_str = result.stdout.split()[1]
            version = tuple(map(int, version_str.split('.')))

            if version < self.MIN_RUBY_VERSION:
                raise RubyEnvironmentError(
                    f"Ruby version {version_str} is below minimum required {
                        '.'.join(map(str, self.MIN_RUBY_VERSION))}"
                )
        except subprocess.CalledProcessError as e:
            raise RubyEnvironmentError(
                f"Failed to get Ruby version: {e}") from e

    def _setup_ruby_environment(self) -> None:
        """Setup Ruby environment variables and paths."""
        # Setup environment variables
        self.ruby_env = os.environ.copy()
        self.ruby_env.update({
            'BUNDLE_PATH': str(self.parser_dir / 'vendor' / 'bundle'),
            'GEM_PATH': str(self.parser_dir / 'vendor' / 'bundle' / 'ruby'),
        })

    def parse_database(self, retries: int = MAX_RETRIES) -> Optional[Dict]:
        """
        Parse the Notes database using apple_cloud_notes_parser.

        Args:
            retries: Number of retries if parsing fails (default: MAX_RETRIES)

        Returns:
            Dict containing the parsed JSON data or None if parsing fails

        Raises:
            DatabaseAccessError: If database access fails
            ParserExecutionError: If parser execution fails
            OutputError: If parser output cannot be processed
        """
        db_path = config.apple_notes.db_path
        if not db_path.exists():
            raise DatabaseAccessError(f"Database not found at: {db_path}")

        logger.info("Attempting to parse database: %s", db_path.parent)

        # Create unique temporary directory
        temp_dir = self.temp_base / datetime.now().strftime('%Y%m%d_%H%M%S')
        temp_dir.mkdir(parents=True, exist_ok=True)

        # Attempt to parse the database with retries
        try:
            for attempt in range(retries):
                try:
                    return self._execute_parser(db_path, temp_dir)
                except (ParserExecutionError, OutputError) as e:
                    if attempt == retries - 1:
                        raise
                    logger.warning(
                        "Parser attempt %d failed: %s", attempt + 1, e)
                    continue
        finally:
            # Cleanup temporary directory
            if temp_dir.exists():
                shutil.rmtree(temp_dir)

    def _execute_parser(self, db_path: Path, temp_dir: Path) -> Dict:
        """Execute the Ruby parser and process output."""
        try:
            # Prepare command with proper bundle environment
            command = [
                str(self.ruby_path),  # Ruby executable
                '-S',           # Search for the command in PATH
                'bundle',       # Run bundler
                'exec',         # Execute with bundle environment
                'ruby',         # Run ruby with bundle environment
                str(self.ruby_script_path.name),  # The actual script
                "-m",
                str(db_path.parent),
                "-g",
                "-o",
                str(temp_dir)
            ]

            if config.env_mode == "DEV":
                logger.debug("Executing parser command: %s", " ".join(command))
                logger.debug("Working directory: %s", self.parser_dir)
                logger.debug("Environment: %s",
                             {k: v for k, v in self.ruby_env.items()
                              if k in ['BUNDLE_PATH', 'GEM_PATH']})

            # Run the Ruby parser
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True,
                cwd=str(self.parser_dir),
                env=self.ruby_env,
                timeout=self.PARSER_TIMEOUT
            )

            # Log outputs based on environment mode
            if config.env_mode == "DEV":
                logger.debug("Parser stdout: %s", result.stdout)
                if result.stderr:
                    logger.warning("Parser stderr: %s", result.stderr)

            # Find and read the JSON output file
            json_file = temp_dir / 'notes_rip' / 'json' / 'all_notes_1.json'

            if not json_file.exists():
                logger.error("JSON output file not found at expected location")
                if config.env_mode == "DEV":
                    logger.debug("Contents of temp directory:")
                    for path in temp_dir.rglob('*'):
                        logger.debug("  %s", path)
                raise OutputError("JSON output file not found")

            try:
                with json_file.open() as f:
                    data = json.load(f)
                    logger.info("Successfully loaded JSON data")
            except json.JSONDecodeError as e:
                raise OutputError(f"Failed to parse JSON output: {e}") from e
            except Exception as e:
                raise OutputError(f"Failed to read JSON file: {e}") from e

            # Validate basic structure
            if not self._validate_json_structure(data):
                raise OutputError("Invalid JSON structure in parser output")

            # Print summary in dev mode
            if config.env_mode == "DEV":
                self._print_truncated_json(data)

            return data

        except subprocess.TimeoutExpired as e:
            raise ParserExecutionError(
                f"Parser execution timed out after {
                    self.PARSER_TIMEOUT} seconds"
            ) from e
        except subprocess.CalledProcessError as e:
            raise ParserExecutionError(
                f"Parser execution failed: {e.stderr}"
            ) from e
        except Exception as e:
            raise ParserExecutionError(
                f"Unexpected error during parsing: {str(e)}"
            ) from e

    def _validate_json_structure(self, data: Dict) -> bool:
        """
        Validate the basic structure of the parser output JSON.

        Args:
            data: Dictionary containing parsed JSON data

        Returns:
            bool indicating if the structure is valid
        """
        required_keys = {'version', 'notes', 'folders', 'accounts'}
        if not all(key in data for key in required_keys):
            logger.error("Missing required keys in JSON output")
            return False

        # Validate notes structure
        for note_id, note in data.get('notes', {}).items():
            if not isinstance(note, dict):
                logger.error("Invalid note structure for note_id: %s", note_id)
                return False

            required_note_keys = {
                'title', 'creation_time', 'modify_time',
                'folder_key', 'account_key'
            }
            if not all(key in note for key in required_note_keys):
                logger.error("Missing required keys in note: %s", note_id)
                return False

        return True

    def _print_truncated_json(self, data: Dict) -> None:
        """Print a truncated version of the JSON for testing/validation."""
        # Get basic stats
        num_notes = len(data.get('notes', {}))
        num_folders = len(data.get('folders', {}))

        # Create truncated version
        truncated = {
            'version': data.get('version'),
            'stats': {
                'total_notes': num_notes,
                'total_folders': num_folders
            },
            'sample_note': next(iter(data.get('notes', {}).values()), None)
        }

        logger.info("Parser Output Summary:")
        logger.info(json.dumps(truncated, indent=2))
