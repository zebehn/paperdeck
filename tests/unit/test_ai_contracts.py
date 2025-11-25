"""Unit tests for AI service data contracts."""

import pytest
from unittest.mock import Mock

from paperdeck.ai.service import AIRequest, AIResponse, AIService


class TestAIRequest:
    """Tests for AIRequest data contract."""

    def test_valid_ai_request(self):
        """Test creating a valid AI request."""
        request = AIRequest(
            prompt="Generate a presentation",
            model="gpt-4",
            max_tokens=2048,
            temperature=0.8,
        )
        assert request.prompt == "Generate a presentation"
        assert request.model == "gpt-4"
        assert request.max_tokens == 2048
        assert request.temperature == 0.8

    def test_default_values(self):
        """Test default request parameters."""
        request = AIRequest(
            prompt="Test prompt",
            model="gpt-4",
        )
        assert request.max_tokens == 4096
        assert request.temperature == 0.7
        assert request.system_instructions is None

    def test_empty_prompt_raises_error(self):
        """Test that empty prompt raises ValueError."""
        with pytest.raises(ValueError, match="prompt must not be empty"):
            AIRequest(prompt="", model="gpt-4")

    def test_invalid_max_tokens_raises_error(self):
        """Test that invalid max_tokens raises ValueError."""
        with pytest.raises(ValueError, match="max_tokens must be > 0"):
            AIRequest(
                prompt="Test",
                model="gpt-4",
                max_tokens=0,
            )

        with pytest.raises(ValueError, match="max_tokens must be > 0"):
            AIRequest(
                prompt="Test",
                model="gpt-4",
                max_tokens=-100,
            )

    def test_excessive_max_tokens_raises_error(self):
        """Test that max_tokens > 128000 raises ValueError."""
        with pytest.raises(ValueError, match="max_tokens must be <= 128000"):
            AIRequest(
                prompt="Test",
                model="gpt-4",
                max_tokens=200000,
            )

    def test_invalid_temperature_raises_error(self):
        """Test that invalid temperature raises ValueError."""
        with pytest.raises(ValueError, match="temperature must be in range"):
            AIRequest(
                prompt="Test",
                model="gpt-4",
                temperature=-0.1,
            )

        with pytest.raises(ValueError, match="temperature must be in range"):
            AIRequest(
                prompt="Test",
                model="gpt-4",
                temperature=2.5,
            )

    def test_with_system_instructions(self):
        """Test request with system instructions."""
        request = AIRequest(
            prompt="Test",
            model="gpt-4",
            system_instructions="You are a LaTeX expert",
        )
        assert request.system_instructions == "You are a LaTeX expert"


class TestAIResponse:
    """Tests for AIResponse data contract."""

    def test_valid_ai_response(self):
        """Test creating a valid AI response."""
        response = AIResponse(
            content="\\documentclass{beamer}",
            model="gpt-4",
            tokens_used=1500,
            finish_reason="stop",
        )
        assert response.content == "\\documentclass{beamer}"
        assert response.model == "gpt-4"
        assert response.tokens_used == 1500
        assert response.finish_reason == "stop"

    def test_default_values(self):
        """Test default response values."""
        response = AIResponse(
            content="Test content",
            model="gpt-4",
        )
        assert response.tokens_used is None
        assert response.finish_reason is None
        assert response.metadata == {}

    def test_empty_content_raises_error(self):
        """Test that empty content raises ValueError."""
        with pytest.raises(ValueError, match="content must not be empty"):
            AIResponse(content="", model="gpt-4")

    def test_with_metadata(self):
        """Test response with metadata."""
        response = AIResponse(
            content="Test",
            model="gpt-4",
            metadata={"provider": "openai", "version": "v1"},
        )
        assert response.metadata["provider"] == "openai"
        assert response.metadata["version"] == "v1"


class TestAIServiceInterface:
    """Tests for AIService abstract interface."""

    def test_cannot_instantiate_abstract_class(self):
        """Test that AIService cannot be instantiated directly."""
        with pytest.raises(TypeError):
            AIService()

    def test_concrete_implementation_requires_all_methods(self):
        """Test that concrete implementations must implement all abstract methods."""

        # Missing generate method
        class IncompleteService1(AIService):
            def is_available(self) -> bool:
                return True

            def validate_config(self) -> bool:
                return True

        with pytest.raises(TypeError):
            IncompleteService1()

        # Missing is_available method
        class IncompleteService2(AIService):
            def generate(self, request: AIRequest) -> AIResponse:
                return AIResponse(content="test", model="test")

            def validate_config(self) -> bool:
                return True

        with pytest.raises(TypeError):
            IncompleteService2()

        # Missing validate_config method
        class IncompleteService3(AIService):
            def generate(self, request: AIRequest) -> AIResponse:
                return AIResponse(content="test", model="test")

            def is_available(self) -> bool:
                return True

        with pytest.raises(TypeError):
            IncompleteService3()

    def test_complete_implementation_can_be_instantiated(self):
        """Test that complete implementations can be instantiated."""

        class CompleteService(AIService):
            def generate(self, request: AIRequest) -> AIResponse:
                return AIResponse(
                    content="\\documentclass{beamer}",
                    model=request.model,
                    tokens_used=100,
                )

            def is_available(self) -> bool:
                return True

            def validate_config(self) -> bool:
                return True

        service = CompleteService()
        assert isinstance(service, AIService)

        # Test that methods work
        request = AIRequest(prompt="Test", model="test-model")
        response = service.generate(request)
        assert response.content == "\\documentclass{beamer}"
        assert response.model == "test-model"
        assert service.is_available() is True
        assert service.validate_config() is True


class TestAIServiceContract:
    """Tests for AI service contract compliance."""

    def test_generate_returns_ai_response(self):
        """Test that generate returns AIResponse."""

        class TestService(AIService):
            def generate(self, request: AIRequest) -> AIResponse:
                return AIResponse(content="test content", model=request.model)

            def is_available(self) -> bool:
                return True

            def validate_config(self) -> bool:
                return True

        service = TestService()
        request = AIRequest(prompt="Test", model="test-model")
        response = service.generate(request)

        assert isinstance(response, AIResponse)
        assert response.content == "test content"
        assert response.model == "test-model"

    def test_is_available_returns_bool(self):
        """Test that is_available returns boolean."""

        class TestService(AIService):
            def __init__(self, available: bool):
                self.available = available

            def generate(self, request: AIRequest) -> AIResponse:
                return AIResponse(content="test", model="test")

            def is_available(self) -> bool:
                return self.available

            def validate_config(self) -> bool:
                return True

        available_service = TestService(available=True)
        assert available_service.is_available() is True

        unavailable_service = TestService(available=False)
        assert unavailable_service.is_available() is False

    def test_validate_config_returns_bool(self):
        """Test that validate_config returns boolean."""

        class TestService(AIService):
            def __init__(self, valid_config: bool):
                self.valid_config = valid_config

            def generate(self, request: AIRequest) -> AIResponse:
                return AIResponse(content="test", model="test")

            def is_available(self) -> bool:
                return True

            def validate_config(self) -> bool:
                return self.valid_config

        valid_service = TestService(valid_config=True)
        assert valid_service.validate_config() is True

        invalid_service = TestService(valid_config=False)
        assert invalid_service.validate_config() is False
