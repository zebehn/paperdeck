"""
Unit tests for TextExtractionResult and ExtractionStatus models.

Following TDD approach: These tests define expected behavior before implementation.
"""

import pytest
from paperdeck.models.extraction_result import (
    ExtractionStatus,
    TextExtractionResult,
    validate_extraction_result,
)


class TestExtractionStatus:
    """Tests for ExtractionStatus enum."""

    def test_enum_values_exist(self):
        """Test that all required status values exist."""
        assert ExtractionStatus.SUCCESS
        assert ExtractionStatus.PARTIAL
        assert ExtractionStatus.FAILED
        assert ExtractionStatus.NOT_ATTEMPTED

    def test_enum_values_are_strings(self):
        """Test that enum values are strings."""
        assert ExtractionStatus.SUCCESS.value == "success"
        assert ExtractionStatus.PARTIAL.value == "partial"
        assert ExtractionStatus.FAILED.value == "failed"
        assert ExtractionStatus.NOT_ATTEMPTED.value == "not_attempted"


class TestTextExtractionResult:
    """Tests for TextExtractionResult dataclass."""

    def test_successful_extraction_result(self):
        """Test creating a successful extraction result."""
        result = TextExtractionResult(
            status=ExtractionStatus.SUCCESS,
            text_content="Abstract: This paper presents...",
            raw_text_length=5000,
            clean_text_length=4500,
            page_count=10,
            extraction_time_seconds=0.25,
        )

        assert result.status == ExtractionStatus.SUCCESS
        assert result.text_content == "Abstract: This paper presents..."
        assert result.raw_text_length == 5000
        assert result.clean_text_length == 4500
        assert result.page_count == 10
        assert result.extraction_time_seconds == 0.25
        assert result.error_message is None
        assert result.warnings == []

    def test_failed_extraction_result(self):
        """Test creating a failed extraction result."""
        result = TextExtractionResult(
            status=ExtractionStatus.FAILED,
            text_content=None,
            raw_text_length=0,
            clean_text_length=0,
            page_count=5,
            extraction_time_seconds=0.1,
            error_message="PDF is encrypted",
        )

        assert result.status == ExtractionStatus.FAILED
        assert result.text_content is None
        assert result.error_message == "PDF is encrypted"

    def test_partial_extraction_with_warnings(self):
        """Test extraction result with warnings."""
        result = TextExtractionResult(
            status=ExtractionStatus.PARTIAL,
            text_content="Some text extracted...",
            raw_text_length=1000,
            clean_text_length=800,
            page_count=10,
            extraction_time_seconds=0.5,
            warnings=["Unusual layout detected on pages 5-7"],
        )

        assert result.status == ExtractionStatus.PARTIAL
        assert len(result.warnings) == 1
        assert "Unusual layout" in result.warnings[0]

    def test_is_successful_property_for_success(self):
        """Test is_successful property returns True for SUCCESS status."""
        result = TextExtractionResult(
            status=ExtractionStatus.SUCCESS,
            text_content="text",
            raw_text_length=100,
            clean_text_length=90,
            page_count=5,
            extraction_time_seconds=0.1,
        )

        assert result.is_successful is True

    def test_is_successful_property_for_partial(self):
        """Test is_successful property returns True for PARTIAL status."""
        result = TextExtractionResult(
            status=ExtractionStatus.PARTIAL,
            text_content="text",
            raw_text_length=100,
            clean_text_length=90,
            page_count=5,
            extraction_time_seconds=0.1,
        )

        assert result.is_successful is True

    def test_is_successful_property_for_failed(self):
        """Test is_successful property returns False for FAILED status."""
        result = TextExtractionResult(
            status=ExtractionStatus.FAILED,
            text_content=None,
            raw_text_length=0,
            clean_text_length=0,
            page_count=5,
            extraction_time_seconds=0.1,
            error_message="Error",
        )

        assert result.is_successful is False

    def test_sanitization_reduction_pct_calculation(self):
        """Test sanitization reduction percentage calculation."""
        result = TextExtractionResult(
            status=ExtractionStatus.SUCCESS,
            text_content="text",
            raw_text_length=1000,
            clean_text_length=800,
            page_count=10,
            extraction_time_seconds=0.25,
        )

        # (1000 - 800) / 1000 * 100 = 20%
        assert result.sanitization_reduction_pct == 20.0

    def test_sanitization_reduction_pct_zero_raw_length(self):
        """Test sanitization reduction with zero raw length."""
        result = TextExtractionResult(
            status=ExtractionStatus.FAILED,
            text_content=None,
            raw_text_length=0,
            clean_text_length=0,
            page_count=0,
            extraction_time_seconds=0.0,
            error_message="Error",
        )

        assert result.sanitization_reduction_pct == 0.0


class TestValidateExtractionResult:
    """Tests for extraction result validation."""

    def test_validation_passes_for_valid_success_result(self):
        """Test validation passes for valid SUCCESS result."""
        result = TextExtractionResult(
            status=ExtractionStatus.SUCCESS,
            text_content="text",
            raw_text_length=100,
            clean_text_length=90,
            page_count=10,
            extraction_time_seconds=0.25,
        )

        errors = validate_extraction_result(result)
        assert len(errors) == 0

    def test_validation_fails_success_without_text_content(self):
        """Test validation fails for SUCCESS status without text_content."""
        result = TextExtractionResult(
            status=ExtractionStatus.SUCCESS,
            text_content=None,
            raw_text_length=100,
            clean_text_length=90,
            page_count=10,
            extraction_time_seconds=0.25,
        )

        errors = validate_extraction_result(result)
        assert len(errors) > 0
        assert any("text_content" in error for error in errors)

    def test_validation_fails_failed_without_error_message(self):
        """Test validation fails for FAILED status without error_message."""
        result = TextExtractionResult(
            status=ExtractionStatus.FAILED,
            text_content=None,
            raw_text_length=0,
            clean_text_length=0,
            page_count=5,
            extraction_time_seconds=0.1,
            error_message=None,
        )

        errors = validate_extraction_result(result)
        assert len(errors) > 0
        assert any("error_message" in error for error in errors)

    def test_validation_fails_negative_extraction_time(self):
        """Test validation fails for negative extraction_time_seconds."""
        result = TextExtractionResult(
            status=ExtractionStatus.SUCCESS,
            text_content="text",
            raw_text_length=100,
            clean_text_length=90,
            page_count=10,
            extraction_time_seconds=-0.5,
        )

        errors = validate_extraction_result(result)
        assert len(errors) > 0
        assert any("extraction_time_seconds" in error for error in errors)

    def test_validation_fails_clean_exceeds_raw_length(self):
        """Test validation fails when clean_text_length > raw_text_length."""
        result = TextExtractionResult(
            status=ExtractionStatus.SUCCESS,
            text_content="text",
            raw_text_length=100,
            clean_text_length=200,  # Invalid: exceeds raw
            page_count=10,
            extraction_time_seconds=0.25,
        )

        errors = validate_extraction_result(result)
        assert len(errors) > 0
        assert any("clean_text_length" in error and "exceed" in error for error in errors)
