"""
Custom exceptions for the Notes Parser.
"""


class NotesParserError(Exception):
    """Base exception for all parser-related errors."""

    def __init__(self, message: str, original_error: Exception = None):
        super().__init__(message)
        self.original_error = original_error


class ParserNotFoundError(NotesParserError):
    """Raised when apple_cloud_notes_parser is not found or incorrectly installed."""


class RubyEnvironmentError(NotesParserError):
    """Raised when Ruby environment is not properly configured."""


class ParserExecutionError(NotesParserError):
    """Raised when parser execution fails."""


class DatabaseAccessError(NotesParserError):
    """Raised when database cannot be accessed."""


class OutputError(NotesParserError):
    """Raised when parser output cannot be processed."""
