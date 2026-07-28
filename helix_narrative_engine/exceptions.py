"""Public exception hierarchy for Helix Narrative Engine."""


class NarrativeEngineError(Exception):
    """Base class for expected engine failures."""


class ConfigurationError(NarrativeEngineError):
    """Raised when provider or runtime configuration is missing or invalid."""


class InputValidationError(NarrativeEngineError, ValueError):
    """Raised before any provider call when user input is invalid."""


class BudgetExceededError(NarrativeEngineError):
    """Raised before generation when a workflow exceeds configured limits."""


class ProviderError(NarrativeEngineError):
    """A sanitized provider failure that does not expose credentials or content."""

    def __init__(self, provider: str, reason: str) -> None:
        self.provider = provider
        self.reason = reason
        super().__init__(f"{provider} provider request failed ({reason})")


class OutputError(NarrativeEngineError):
    """Raised when CLI output cannot be written safely."""
