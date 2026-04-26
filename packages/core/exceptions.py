"""Shared exception hierarchy for the UNMAPPED platform."""


class UnmappedError(Exception):
    """Base exception for all UNMAPPED errors."""


class ConfigValidationError(UnmappedError):
    """Raised when a country configuration file fails validation."""

    def __init__(self, context_id: str, details: str) -> None:
        self.context_id = context_id
        self.details = details
        super().__init__(f"Config validation failed for '{context_id}': {details}")


class ConfigNotFoundError(UnmappedError):
    """Raised when a requested country context does not exist."""

    def __init__(self, context_id: str) -> None:
        self.context_id = context_id
        super().__init__(f"Country context '{context_id}' not found")


class AgentError(UnmappedError):
    """Raised when a LangGraph agent fails during execution."""

    def __init__(self, agent_name: str, details: str) -> None:
        self.agent_name = agent_name
        self.details = details
        super().__init__(f"Agent '{agent_name}' failed: {details}")


class DataSourceError(UnmappedError):
    """Raised when an external data source is unreachable or returns bad data."""


class LLMError(UnmappedError):
    """Raised when an LLM call fails after retries."""


class RepositoryError(UnmappedError):
    """Raised on data-access failures."""


class AuthenticationError(UnmappedError):
    """Raised on authentication failures."""


class AuthorizationError(UnmappedError):
    """Raised when a user lacks the required role/permission."""
