"""Unit tests for exception hierarchy."""

import pytest

from paperdeck.core.exceptions import (
    AIServiceError,
    CompilationError,
    ConfigurationError,
    ExtractionError,
    GenerationError,
    PaperDeckError,
    PromptError,
    RateLimitExceededError,
    ServiceUnavailableError,
    ValidationError,
)


class TestExceptionHierarchy:
    """Tests for exception inheritance structure."""

    def test_base_exception(self):
        """Test that PaperDeckError is the base exception."""
        error = PaperDeckError("Base error")
        assert isinstance(error, Exception)
        assert str(error) == "Base error"

    def test_configuration_error_inherits_from_base(self):
        """Test that ConfigurationError inherits from PaperDeckError."""
        error = ConfigurationError("Config error")
        assert isinstance(error, PaperDeckError)
        assert isinstance(error, Exception)

    def test_validation_error_inherits_from_base(self):
        """Test that ValidationError inherits from PaperDeckError."""
        error = ValidationError("Validation error")
        assert isinstance(error, PaperDeckError)
        assert isinstance(error, Exception)

    def test_extraction_error_inherits_from_base(self):
        """Test that ExtractionError inherits from PaperDeckError."""
        error = ExtractionError("Extraction error")
        assert isinstance(error, PaperDeckError)
        assert isinstance(error, Exception)

    def test_ai_service_error_inherits_from_base(self):
        """Test that AIServiceError inherits from PaperDeckError."""
        error = AIServiceError("AI service error")
        assert isinstance(error, PaperDeckError)
        assert isinstance(error, Exception)

    def test_service_unavailable_error_inherits_from_ai_service(self):
        """Test that ServiceUnavailableError inherits from AIServiceError."""
        error = ServiceUnavailableError("Service unavailable")
        assert isinstance(error, AIServiceError)
        assert isinstance(error, PaperDeckError)
        assert isinstance(error, Exception)

    def test_rate_limit_exceeded_error_inherits_from_ai_service(self):
        """Test that RateLimitExceededError inherits from AIServiceError."""
        error = RateLimitExceededError("Rate limit exceeded")
        assert isinstance(error, AIServiceError)
        assert isinstance(error, PaperDeckError)
        assert isinstance(error, Exception)

    def test_prompt_error_inherits_from_base(self):
        """Test that PromptError inherits from PaperDeckError."""
        error = PromptError("Prompt error")
        assert isinstance(error, PaperDeckError)
        assert isinstance(error, Exception)

    def test_generation_error_inherits_from_base(self):
        """Test that GenerationError inherits from PaperDeckError."""
        error = GenerationError("Generation error")
        assert isinstance(error, PaperDeckError)
        assert isinstance(error, Exception)

    def test_compilation_error_inherits_from_generation(self):
        """Test that CompilationError inherits from GenerationError."""
        error = CompilationError("Compilation error")
        assert isinstance(error, GenerationError)
        assert isinstance(error, PaperDeckError)
        assert isinstance(error, Exception)


class TestExceptionUsage:
    """Tests for practical exception usage."""

    def test_catch_base_exception_catches_all(self):
        """Test that catching PaperDeckError catches all custom exceptions."""
        with pytest.raises(PaperDeckError):
            raise ConfigurationError("Config error")

        with pytest.raises(PaperDeckError):
            raise ValidationError("Validation error")

        with pytest.raises(PaperDeckError):
            raise ExtractionError("Extraction error")

        with pytest.raises(PaperDeckError):
            raise AIServiceError("AI error")

        with pytest.raises(PaperDeckError):
            raise PromptError("Prompt error")

        with pytest.raises(PaperDeckError):
            raise GenerationError("Generation error")

    def test_catch_ai_service_error_catches_subclasses(self):
        """Test that catching AIServiceError catches its subclasses."""
        with pytest.raises(AIServiceError):
            raise ServiceUnavailableError("Service unavailable")

        with pytest.raises(AIServiceError):
            raise RateLimitExceededError("Rate limit exceeded")

    def test_catch_generation_error_catches_compilation(self):
        """Test that catching GenerationError catches CompilationError."""
        with pytest.raises(GenerationError):
            raise CompilationError("Compilation failed")

    def test_specific_exception_catching(self):
        """Test catching specific exception types."""
        with pytest.raises(RateLimitExceededError):
            raise RateLimitExceededError("Rate limit")

        with pytest.raises(CompilationError):
            raise CompilationError("Compilation failed")

    def test_exception_messages_preserved(self):
        """Test that exception messages are preserved."""
        try:
            raise ConfigurationError("Invalid API key")
        except ConfigurationError as e:
            assert str(e) == "Invalid API key"

        try:
            raise RateLimitExceededError("Too many requests")
        except RateLimitExceededError as e:
            assert str(e) == "Too many requests"


class TestExceptionRaising:
    """Tests for raising exceptions in different scenarios."""

    def test_raise_configuration_error(self):
        """Test raising ConfigurationError."""

        def bad_config():
            raise ConfigurationError("Missing API key")

        with pytest.raises(ConfigurationError, match="Missing API key"):
            bad_config()

    def test_raise_extraction_error(self):
        """Test raising ExtractionError."""

        def failed_extraction():
            raise ExtractionError("Failed to extract figures")

        with pytest.raises(ExtractionError, match="Failed to extract"):
            failed_extraction()

    def test_raise_service_unavailable(self):
        """Test raising ServiceUnavailableError."""

        def service_down():
            raise ServiceUnavailableError("OpenAI service is down")

        with pytest.raises(ServiceUnavailableError, match="service is down"):
            service_down()

    def test_raise_rate_limit_exceeded(self):
        """Test raising RateLimitExceededError."""

        def rate_limited():
            raise RateLimitExceededError("Rate limit: 20 requests/minute")

        with pytest.raises(RateLimitExceededError, match="Rate limit"):
            rate_limited()

    def test_raise_compilation_error(self):
        """Test raising CompilationError."""

        def latex_compile_failed():
            raise CompilationError("pdflatex failed with exit code 1")

        with pytest.raises(CompilationError, match="pdflatex failed"):
            latex_compile_failed()
