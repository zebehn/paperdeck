"""Custom exceptions for PaperDeck.

This module defines the exception hierarchy used throughout the application
for consistent error handling and reporting.
"""


class PaperDeckError(Exception):
    """Base exception for all paperdeck errors."""

    pass


class ConfigurationError(PaperDeckError):
    """Invalid configuration or setup."""

    pass


class ValidationError(PaperDeckError):
    """Data validation failed."""

    pass


class ExtractionError(PaperDeckError):
    """PDF element extraction failed."""

    pass


class AIServiceError(PaperDeckError):
    """AI service communication failed."""

    pass


class ServiceUnavailableError(AIServiceError):
    """AI service is not available."""

    pass


class RateLimitExceededError(AIServiceError):
    """AI service rate limit exceeded."""

    pass


class PromptError(PaperDeckError):
    """Prompt template error."""

    pass


class GenerationError(PaperDeckError):
    """Presentation generation failed."""

    pass


class CompilationError(GenerationError):
    """LaTeX compilation failed."""

    pass
