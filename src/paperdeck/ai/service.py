"""AI service interface and data contracts.

This module defines the abstract interface that all AI service providers must implement,
along with the request and response data structures.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class AIRequest:
    """Request data for AI content generation."""

    prompt: str
    model: str
    max_tokens: int = 4096
    temperature: float = 0.7
    system_instructions: Optional[str] = None

    def __post_init__(self):
        """Validate AI request parameters."""
        if not self.prompt:
            raise ValueError("prompt must not be empty")

        if self.max_tokens < 1:
            raise ValueError("max_tokens must be > 0")

        if self.max_tokens > 128000:
            raise ValueError("max_tokens must be <= 128000")

        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError("temperature must be in range [0.0, 2.0]")


@dataclass
class AIResponse:
    """Response from AI content generation."""

    content: str
    model: str
    tokens_used: Optional[int] = None
    finish_reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate AI response."""
        if not self.content:
            raise ValueError("content must not be empty for successful responses")


class AIService(ABC):
    """Abstract interface for AI service providers.

    All AI service adapters (OpenAI, Anthropic, Ollama, LMStudio) must implement
    this interface to ensure consistent behavior across providers.
    """

    @abstractmethod
    def generate(self, request: AIRequest) -> AIResponse:
        """Generate LaTeX presentation content from a paper.

        Args:
            request: AIRequest containing prompt and generation parameters

        Returns:
            AIResponse: Generated LaTeX code and metadata

        Raises:
            ServiceUnavailableError: Service is not accessible or offline
            RateLimitExceededError: Rate limit exceeded (429 error)
            AIServiceError: General service error (4xx, 5xx errors)
            ValidationError: Invalid request parameters
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the service is currently available.

        Returns:
            bool: True if service can be reached, False otherwise
        """
        pass

    @abstractmethod
    def validate_config(self) -> bool:
        """Validate service configuration (API keys, endpoints).

        Returns:
            bool: True if configuration is valid, False otherwise

        Raises:
            ConfigurationError: Invalid configuration detected
        """
        pass
