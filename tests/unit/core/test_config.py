"""
Unit tests for TextExtractionConfig.

Following TDD approach: These tests define expected behavior before full implementation.
"""

import pytest
from paperdeck.core.config import TextExtractionConfig


class TestTextExtractionConfig:
    """Tests for TextExtractionConfig dataclass."""

    def test_default_configuration(self):
        """Test default configuration values."""
        config = TextExtractionConfig()

        assert config.enabled is True
        assert config.header_margin == 50
        assert config.footer_margin == 50
        assert config.remove_image_text is True
        assert config.remove_page_numbers is True
        assert config.remove_headers_footers is True
        assert config.min_line_length == 3
        assert config.max_tokens is None
        assert config.reserve_output_fraction == 0.25
        assert config.truncation_strategy == "end"
        assert config.timeout_seconds == 30.0
        assert config.cache_extracted_text is False

    def test_custom_configuration(self):
        """Test creating config with custom values."""
        config = TextExtractionConfig(
            enabled=False,
            header_margin=75,
            footer_margin=75,
            remove_image_text=False,
            reserve_output_fraction=0.30,
            truncation_strategy="priority_sections",
            timeout_seconds=60.0,
        )

        assert config.enabled is False
        assert config.header_margin == 75
        assert config.footer_margin == 75
        assert config.reserve_output_fraction == 0.30
        assert config.truncation_strategy == "priority_sections"
        assert config.timeout_seconds == 60.0

    def test_available_input_fraction_property(self):
        """Test available_input_fraction property calculation."""
        config = TextExtractionConfig(reserve_output_fraction=0.25)
        assert config.available_input_fraction == 0.75

        config2 = TextExtractionConfig(reserve_output_fraction=0.30)
        assert config2.available_input_fraction == 0.70

    def test_validation_passes_for_valid_config(self):
        """Test validation passes for valid configuration."""
        config = TextExtractionConfig()
        errors = config.validate()
        assert len(errors) == 0

    def test_validation_fails_negative_margins(self):
        """Test validation fails for negative margins."""
        config = TextExtractionConfig(header_margin=-10)
        errors = config.validate()
        assert len(errors) > 0
        assert any("Margins" in error for error in errors)

        config2 = TextExtractionConfig(footer_margin=-5)
        errors2 = config2.validate()
        assert len(errors2) > 0

    def test_validation_fails_invalid_reserve_fraction(self):
        """Test validation fails for invalid reserve_output_fraction."""
        # Too high (>= 1)
        config = TextExtractionConfig(reserve_output_fraction=1.5)
        errors = config.validate()
        assert len(errors) > 0
        assert any("Reserve fraction" in error for error in errors)

        # Too low (<= 0)
        config2 = TextExtractionConfig(reserve_output_fraction=0.0)
        errors2 = config2.validate()
        assert len(errors2) > 0

        config3 = TextExtractionConfig(reserve_output_fraction=-0.1)
        errors3 = config3.validate()
        assert len(errors3) > 0

    def test_validation_fails_invalid_truncation_strategy(self):
        """Test validation fails for invalid truncation_strategy."""
        config = TextExtractionConfig(truncation_strategy="invalid_strategy")
        errors = config.validate()
        assert len(errors) > 0
        assert any("truncation strategy" in error for error in errors)

    def test_validation_fails_invalid_timeout(self):
        """Test validation fails for non-positive timeout."""
        config = TextExtractionConfig(timeout_seconds=0.0)
        errors = config.validate()
        assert len(errors) > 0
        assert any("Timeout" in error for error in errors)

        config2 = TextExtractionConfig(timeout_seconds=-5.0)
        errors2 = config2.validate()
        assert len(errors2) > 0

    def test_validation_fails_negative_min_line_length(self):
        """Test validation fails for negative min_line_length."""
        config = TextExtractionConfig(min_line_length=-1)
        errors = config.validate()
        assert len(errors) > 0
        assert any("min_line_length" in error for error in errors)

    def test_validation_returns_multiple_errors(self):
        """Test validation can return multiple errors."""
        config = TextExtractionConfig(
            header_margin=-10,
            reserve_output_fraction=1.5,
            truncation_strategy="invalid",
            timeout_seconds=-1.0,
        )

        errors = config.validate()
        assert len(errors) >= 4  # Should have at least 4 errors

    def test_valid_truncation_strategies(self):
        """Test all valid truncation strategies are accepted."""
        for strategy in ["end", "middle", "priority_sections"]:
            config = TextExtractionConfig(truncation_strategy=strategy)
            errors = config.validate()
            assert len(errors) == 0, f"Strategy '{strategy}' should be valid"
