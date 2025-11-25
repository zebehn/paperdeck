"""AI service orchestration and selection.

This module provides the AIOrchestrator class that manages multiple AI service
providers and handles service selection.
"""

from typing import Dict, Optional

from .service import AIService
from ..core.config import AIServiceConfiguration
from ..core.exceptions import ConfigurationError


class AIOrchestrator:
    """Orchestrates AI service selection and management."""

    def __init__(self, config: AIServiceConfiguration):
        """Initialize orchestrator with configuration.

        Args:
            config: AIServiceConfiguration with provider settings
        """
        self.config = config
        self._services: Dict[str, AIService] = {}

    def get_service(self, provider: str) -> AIService:
        """Get AI service for specified provider.

        Args:
            provider: Provider name (openai, anthropic, ollama, lmstudio)

        Returns:
            AIService: Service instance for the provider

        Raises:
            KeyError: If provider is unknown
            ConfigurationError: If provider is not properly configured
        """
        # Return cached service if available
        if provider in self._services:
            return self._services[provider]

        # Validate provider configuration
        try:
            self.config.validate_provider(provider)
        except ValueError as e:
            raise ConfigurationError(str(e))

        # Create service based on provider
        if provider == "openai":
            service = self._create_openai_service()
        elif provider == "anthropic":
            service = self._create_anthropic_service()
        elif provider == "ollama":
            service = self._create_ollama_service()
        elif provider == "lmstudio":
            service = self._create_lmstudio_service()
        else:
            raise KeyError(f"Unknown AI provider: {provider}")

        # Cache and return
        self._services[provider] = service
        return service

    def get_default_service(self) -> AIService:
        """Get the default AI service based on configuration.

        Returns:
            AIService: Default service instance
        """
        return self.get_service(self.config.default_provider)

    def _create_openai_service(self) -> AIService:
        """Create OpenAI service instance."""
        from .openai_adapter import OpenAIAdapter

        if not self.config.openai_api_key:
            raise ConfigurationError("OpenAI API key not configured")

        return OpenAIAdapter(api_key=self.config.openai_api_key)

    def _create_anthropic_service(self) -> AIService:
        """Create Anthropic service instance."""
        # Placeholder for future implementation
        raise NotImplementedError("Anthropic adapter not yet implemented")

    def _create_ollama_service(self) -> AIService:
        """Create Ollama service instance."""
        # Placeholder for future implementation
        raise NotImplementedError("Ollama adapter not yet implemented")

    def _create_lmstudio_service(self) -> AIService:
        """Create LMStudio service instance."""
        # Placeholder for future implementation
        raise NotImplementedError("LMStudio adapter not yet implemented")
