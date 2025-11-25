"""Unit tests for AI service implementations.

These tests verify that AI service adapters correctly implement the AIService
interface. Tests should FAIL until implementations are complete (TDD).
"""

import pytest
from unittest.mock import Mock, patch

from paperdeck.ai.service import AIRequest, AIResponse, AIService
from paperdeck.core.exceptions import (
    ServiceUnavailableError,
    RateLimitExceededError,
    AIServiceError,
)


class TestOpenAIAdapter:
    """Tests for OpenAI adapter implementation."""

    def test_openai_adapter_implements_ai_service(self):
        """Test that OpenAIAdapter implements AIService interface."""
        from paperdeck.ai.openai_adapter import OpenAIAdapter

        adapter = OpenAIAdapter(api_key="test-key")
        assert isinstance(adapter, AIService)

    def test_openai_generate_with_valid_request(self):
        """Test that OpenAI adapter generates content from valid request."""
        from paperdeck.ai.openai_adapter import OpenAIAdapter

        adapter = OpenAIAdapter(api_key="test-key")
        request = AIRequest(
            prompt="Generate a presentation",
            model="gpt-4",
            max_tokens=2048,
        )

        # This will FAIL until implementation uses mock/real API
        with patch("paperdeck.ai.openai_adapter.OpenAI") as mock_openai:
            # Mock the API response
            mock_client = Mock()
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = "\\documentclass{beamer}"
            mock_response.model = "gpt-4"
            mock_response.usage.total_tokens = 1500
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client

            response = adapter.generate(request)

            assert isinstance(response, AIResponse)
            assert response.content
            assert response.model == "gpt-4"

    def test_openai_is_available_returns_bool(self):
        """Test that is_available checks OpenAI service status."""
        from paperdeck.ai.openai_adapter import OpenAIAdapter

        adapter = OpenAIAdapter(api_key="test-key")
        result = adapter.is_available()

        assert isinstance(result, bool)

    def test_openai_validate_config_checks_api_key(self):
        """Test that validate_config checks for API key."""
        from paperdeck.ai.openai_adapter import OpenAIAdapter

        # Valid config
        adapter = OpenAIAdapter(api_key="test-key")
        assert adapter.validate_config() is True

        # Invalid config (no key) should be caught during init or validation
        with pytest.raises((ValueError, Exception)):
            OpenAIAdapter(api_key=None)

    def test_openai_handles_rate_limit_error(self):
        """Test that OpenAI adapter handles rate limit errors."""
        from paperdeck.ai.openai_adapter import OpenAIAdapter

        adapter = OpenAIAdapter(api_key="test-key")
        request = AIRequest(prompt="Test", model="gpt-4")

        with patch("paperdeck.ai.openai_adapter.OpenAI") as mock_openai:
            mock_client = Mock()
            # Simulate rate limit error
            mock_client.chat.completions.create.side_effect = Exception("Rate limit exceeded")
            mock_openai.return_value = mock_client

            # Should raise RateLimitExceededError or handle gracefully
            with pytest.raises((RateLimitExceededError, AIServiceError, Exception)):
                adapter.generate(request)


class TestRetryLogic:
    """Tests for retry logic with tenacity."""

    def test_retry_on_service_unavailable(self):
        """Test that requests retry on service unavailable errors."""
        from paperdeck.ai.retry_helpers import generate_with_retry

        # Create a mock service
        mock_service = Mock(spec=AIService)
        mock_service.generate.side_effect = [
            ServiceUnavailableError("Service down"),
            ServiceUnavailableError("Service down"),
            AIResponse(content="Success", model="test"),
        ]

        request = AIRequest(prompt="Test", model="test")

        # Should retry and eventually succeed
        response = generate_with_retry(mock_service, request)

        assert response.content == "Success"
        assert mock_service.generate.call_count == 3

    def test_retry_on_rate_limit(self):
        """Test that requests retry on rate limit errors."""
        from paperdeck.ai.retry_helpers import generate_with_retry

        mock_service = Mock(spec=AIService)
        mock_service.generate.side_effect = [
            RateLimitExceededError("Too many requests"),
            AIResponse(content="Success", model="test"),
        ]

        request = AIRequest(prompt="Test", model="test")

        response = generate_with_retry(mock_service, request)

        assert response.content == "Success"
        assert mock_service.generate.call_count == 2

    def test_retry_stops_after_max_attempts(self):
        """Test that retry stops after maximum attempts."""
        from paperdeck.ai.retry_helpers import generate_with_retry

        mock_service = Mock(spec=AIService)
        mock_service.generate.side_effect = ServiceUnavailableError("Always failing")

        request = AIRequest(prompt="Test", model="test")

        # Should raise after max attempts
        with pytest.raises(ServiceUnavailableError):
            generate_with_retry(mock_service, request)

        # Should have attempted multiple times (exact count depends on retry config)
        assert mock_service.generate.call_count > 1


class TestAIOrchestrator:
    """Tests for AI service orchestration."""

    def test_orchestrator_selects_correct_service(self):
        """Test that orchestrator selects service based on provider name."""
        from paperdeck.ai.orchestrator import AIOrchestrator
        from paperdeck.core.config import AIServiceConfiguration

        config = AIServiceConfiguration(
            default_provider="openai",
            openai_api_key="test-key",
        )

        orchestrator = AIOrchestrator(config)
        service = orchestrator.get_service("openai")

        assert service is not None
        assert isinstance(service, AIService)

    def test_orchestrator_raises_error_for_unknown_provider(self):
        """Test that orchestrator raises error for unknown provider."""
        from paperdeck.ai.orchestrator import AIOrchestrator
        from paperdeck.core.config import AIServiceConfiguration

        config = AIServiceConfiguration(default_provider="ollama")
        orchestrator = AIOrchestrator(config)

        with pytest.raises((KeyError, ValueError, Exception)):
            orchestrator.get_service("unknown_provider")

    def test_orchestrator_uses_default_provider(self):
        """Test that orchestrator uses default provider when none specified."""
        from paperdeck.ai.orchestrator import AIOrchestrator
        from paperdeck.core.config import AIServiceConfiguration

        config = AIServiceConfiguration(
            default_provider="openai",
            openai_api_key="test-key",
        )

        orchestrator = AIOrchestrator(config)
        service = orchestrator.get_default_service()

        assert service is not None
        assert isinstance(service, AIService)


class TestMockAIService:
    """Tests using a mock AI service for testing."""

    def test_mock_service_for_testing(self):
        """Test that we can create mock services for testing."""

        class MockAIService(AIService):
            def generate(self, request: AIRequest) -> AIResponse:
                return AIResponse(
                    content="\\documentclass{beamer}\n\\begin{document}\n\\end{document}",
                    model=request.model,
                    tokens_used=100,
                )

            def is_available(self) -> bool:
                return True

            def validate_config(self) -> bool:
                return True

        mock_service = MockAIService()
        request = AIRequest(prompt="Test", model="mock-model")

        response = mock_service.generate(request)

        assert response.content.startswith("\\documentclass{beamer}")
        assert response.model == "mock-model"
        assert mock_service.is_available() is True
        assert mock_service.validate_config() is True
