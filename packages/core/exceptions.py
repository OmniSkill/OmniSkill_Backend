"""Shared exception hierarchy for the UNMAPPED platform."""


class UnmappedError(Exception):
    """Base exception for all UNMAPPED errors."""


class ConfigValidationError(UnmappedError):
    """Raised when a country configuration file fails validation."""

    def __init__(self, context_id: str, details: str) -> None:
        self.context_id = context_id
        self.details = details
        super().__init__(f"Config validation failed for '{context_id}': {details}")


class DataSourceError(UnmappedError):
    """Raised when an external data source is unreachable or returns bad data."""


class LLMError(UnmappedError):
    """Raised when an LLM call fails after retries."""


class RepositoryError(UnmappedError):
    """Raised on data-access failures."""
