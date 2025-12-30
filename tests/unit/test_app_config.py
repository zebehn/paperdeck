"""Unit tests for configuration models."""

import pytest
from pathlib import Path

from paperdeck.core.config import (
    AIServiceConfiguration,
    AppConfiguration,
    ExtractionConfiguration,
)
from paperdeck.core.models import ElementType


class TestExtractionConfiguration:
    """Tests for ExtractionConfiguration model."""

    def test_valid_extraction_config(self):
        """Test creating a valid extraction configuration."""
        config = ExtractionConfiguration(
            confidence_threshold=0.8,
            element_types=[ElementType.FIGURE, ElementType.TABLE],
            boundary_padding=10,
        )
        assert config.confidence_threshold == 0.8
        assert len(config.element_types) == 2
        assert config.boundary_padding == 10

    def test_default_values(self):
        """Test default configuration values."""
        config = ExtractionConfiguration()
        assert config.confidence_threshold == 0.75
        assert len(config.element_types) == 3  # All types by default
        assert config.boundary_padding == 5
        assert config.overwrite_existing is False

    def test_invalid_confidence_threshold(self):
        """Test that invalid confidence threshold raises ValueError."""
        with pytest.raises(ValueError, match="confidence_threshold must be in range"):
            ExtractionConfiguration(confidence_threshold=1.5)

        with pytest.raises(ValueError, match="confidence_threshold must be in range"):
            ExtractionConfiguration(confidence_threshold=-0.1)

    def test_empty_element_types(self):
        """Test that empty element types raises ValueError."""
        with pytest.raises(ValueError, match="element_types must not be empty"):
            ExtractionConfiguration(element_types=[])

    def test_invalid_boundary_padding(self):
        """Test that negative boundary padding raises ValueError."""
        with pytest.raises(ValueError, match="boundary_padding must be >= 0"):
            ExtractionConfiguration(boundary_padding=-5)

    def test_invalid_max_pages(self):
        """Test that invalid max_pages raises ValueError."""
        with pytest.raises(ValueError, match="max_pages must be > 0"):
            ExtractionConfiguration(max_pages=0)

        with pytest.raises(ValueError, match="max_pages must be > 0"):
            ExtractionConfiguration(max_pages=-5)

    def test_string_output_directory_converted_to_path(self):
        """Test that string output_directory is converted to Path."""
        config = ExtractionConfiguration(output_directory="./test_output")
        assert isinstance(config.output_directory, Path)
        assert config.output_directory == Path("./test_output")


class TestAIServiceConfiguration:
    """Tests for AIServiceConfiguration model."""

    def test_valid_ai_service_config(self):
        """Test creating a valid AI service configuration."""
        config = AIServiceConfiguration(
            default_provider="openai",
            openai_api_key="test-key-123",
            max_retries=5,
            timeout_seconds=120,
        )
        assert config.default_provider == "openai"
        assert config.openai_api_key == "test-key-123"
        assert config.max_retries == 5
        assert config.timeout_seconds == 120

    def test_default_values(self):
        """Test default configuration values."""
        config = AIServiceConfiguration(
            default_provider="ollama"  # Local provider doesn't need API key
        )
        assert config.default_provider == "ollama"
        assert config.ollama_base_url == "http://localhost:11434"
        assert config.lmstudio_base_url == "http://localhost:1234"
        assert config.max_retries == 3
        assert config.timeout_seconds == 60

    def test_invalid_provider(self):
        """Test that invalid provider raises ValueError."""
        with pytest.raises(ValueError, match="default_provider must be in"):
            AIServiceConfiguration(default_provider="invalid")

    def test_cloud_provider_requires_api_key(self):
        """Test that cloud providers require API keys."""
        with pytest.raises(ValueError, match="API key required"):
            AIServiceConfiguration(
                default_provider="openai",
                openai_api_key=None,
            )

        with pytest.raises(ValueError, match="API key required"):
            AIServiceConfiguration(
                default_provider="anthropic",
                anthropic_api_key=None,
            )

    def test_local_provider_no_api_key_required(self):
        """Test that local providers don't require API keys."""
        config1 = AIServiceConfiguration(default_provider="ollama")
        assert config1.default_provider == "ollama"

        config2 = AIServiceConfiguration(default_provider="lmstudio")
        assert config2.default_provider == "lmstudio"

    def test_invalid_max_retries(self):
        """Test that negative max_retries raises ValueError."""
        with pytest.raises(ValueError, match="max_retries must be >= 0"):
            AIServiceConfiguration(
                default_provider="ollama",
                max_retries=-1,
            )

    def test_invalid_timeout(self):
        """Test that invalid timeout raises ValueError."""
        with pytest.raises(ValueError, match="timeout_seconds must be > 0"):
            AIServiceConfiguration(
                default_provider="ollama",
                timeout_seconds=0,
            )


class TestAppConfiguration:
    """Tests for AppConfiguration model."""

    def test_valid_app_config(self, tmp_path):
        """Test creating a valid application configuration."""
        prompt_lib = tmp_path / "prompts"
        prompt_lib.mkdir()

        config = AppConfiguration(
            prompt_library_path=prompt_lib,
            default_prompt="technical",
            default_theme="Berkeley",
            log_level="DEBUG",
        )
        assert config.prompt_library_path == prompt_lib
        assert config.default_prompt == "technical"
        assert config.default_theme == "Berkeley"
        assert config.log_level == "DEBUG"

    def test_default_values(self):
        """Test default configuration values."""
        config = AppConfiguration()
        assert config.default_prompt == "default"
        assert config.default_theme == "Madrid"
        assert config.log_level == "INFO"

    def test_string_paths_converted(self, tmp_path):
        """Test that string paths are converted to Path objects."""
        prompt_lib = tmp_path / "prompts"
        prompt_lib.mkdir()

        config = AppConfiguration(
            prompt_library_path=str(prompt_lib),
            output_directory=str(tmp_path / "output"),
        )
        assert isinstance(config.prompt_library_path, Path)
        assert isinstance(config.output_directory, Path)

    def test_user_path_expansion(self):
        """Test that user paths (~) are expanded."""
        config = AppConfiguration(
            prompt_library_path=Path("~/.paperdeck/prompts")
        )
        assert "~" not in str(config.prompt_library_path)

    def test_invalid_log_level(self):
        """Test that invalid log level raises ValueError."""
        with pytest.raises(ValueError, match="log_level must be in"):
            AppConfiguration(log_level="INVALID")

    def test_log_level_normalized_to_uppercase(self):
        """Test that log level is normalized to uppercase."""
        config = AppConfiguration(log_level="debug")
        assert config.log_level == "DEBUG"

    def test_validate_with_nonexistent_prompt_library(self):
        """Test validation fails for nonexistent prompt library."""
        config = AppConfiguration(
            prompt_library_path=Path("/nonexistent/path")
        )
        errors = config.validate()
        assert len(errors) > 0
        assert any("Prompt library path does not exist" in err for err in errors)

    def test_validate_with_invalid_output_directory(self, tmp_path):
        """Test validation fails for invalid output directory."""
        # Create a file where output directory should be
        invalid_path = tmp_path / "output_file"
        invalid_path.write_text("not a directory")

        config = AppConfiguration(output_directory=invalid_path)
        errors = config.validate()
        assert len(errors) > 0
        assert any("not a directory" in err for err in errors)

    def test_validate_passes_with_valid_config(self, tmp_path):
        """Test validation passes with valid configuration."""
        prompt_lib = tmp_path / "prompts"
        prompt_lib.mkdir()
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        config = AppConfiguration(
            prompt_library_path=prompt_lib,
            output_directory=output_dir,
        )
        config.extraction_config.output_directory = tmp_path / "extracted"
        config.extraction_config.output_directory.mkdir()

        errors = config.validate()
        assert len(errors) == 0

    def test_load_from_file_placeholder(self):
        """Test load_from_file returns default config (placeholder)."""
        config = AppConfiguration.load_from_file(Path("test.yaml"))
        assert isinstance(config, AppConfiguration)

    def test_save_to_file_placeholder(self, tmp_path):
        """Test save_to_file doesn't raise errors (placeholder)."""
        config = AppConfiguration()
        config.save_to_file(tmp_path / "config.yaml")
        # Should not raise any errors
