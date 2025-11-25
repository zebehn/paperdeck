"""
Unit tests for enhanced Paper model with text extraction fields.

Following TDD approach: These tests define expected behavior for new text extraction features.
"""

import pytest
from pathlib import Path
from src.paperdeck.core.models import Paper
from src.paperdeck.models.extraction_result import (
    ExtractionStatus,
    TextExtractionResult,
)


# Note: These tests focus on the NEW text extraction fields added in Feature 002
# Tests for existing Paper fields should exist elsewhere


class TestPaperTextContentFields:
    """Tests for new text content fields in Paper model."""

    @pytest.fixture
    def sample_pdf_path(self, tmp_path):
        """Create a temporary PDF file for testing."""
        pdf_file = tmp_path / "test_paper.pdf"
        pdf_file.write_text("dummy pdf content")
        return pdf_file

    def test_paper_with_no_text_content(self, sample_pdf_path):
        """Test Paper without text extraction (backward compatibility)."""
        paper = Paper(file_path=sample_pdf_path)

        assert paper.text_content is None
        assert paper.text_extraction_result is None
        assert paper.token_count is None
        assert paper.was_truncated is False

    def test_paper_with_text_content(self, sample_pdf_path):
        """Test Paper with extracted text content."""
        extraction_result = TextExtractionResult(
            status=ExtractionStatus.SUCCESS,
            text_content="Abstract: This paper presents...",
            raw_text_length=5000,
            clean_text_length=4500,
            page_count=10,
            extraction_time_seconds=0.25,
        )

        paper = Paper(
            file_path=sample_pdf_path,
            text_content="Abstract: This paper presents...",
            text_extraction_result=extraction_result,
            token_count=1200,
            was_truncated=False,
        )

        assert paper.text_content == "Abstract: This paper presents..."
        assert paper.text_extraction_result.status == ExtractionStatus.SUCCESS
        assert paper.token_count == 1200
        assert paper.was_truncated is False

    def test_paper_with_truncated_text(self, sample_pdf_path):
        """Test Paper with truncated text content."""
        extraction_result = TextExtractionResult(
            status=ExtractionStatus.SUCCESS,
            text_content="Truncated text...",
            raw_text_length=50000,
            clean_text_length=6000,
            page_count=50,
            extraction_time_seconds=0.5,
        )

        paper = Paper(
            file_path=sample_pdf_path,
            text_content="Truncated text...",
            text_extraction_result=extraction_result,
            token_count=6000,
            was_truncated=True,
        )

        assert paper.was_truncated is True
        assert paper.token_count == 6000

    def test_has_text_content_property_true(self, sample_pdf_path):
        """Test has_text_content property returns True when text extracted successfully."""
        extraction_result = TextExtractionResult(
            status=ExtractionStatus.SUCCESS,
            text_content="Some text",
            raw_text_length=1000,
            clean_text_length=900,
            page_count=10,
            extraction_time_seconds=0.1,
        )

        paper = Paper(
            file_path=sample_pdf_path,
            text_content="Some text",
            text_extraction_result=extraction_result,
        )

        assert paper.has_text_content is True

    def test_has_text_content_property_false_no_result(self, sample_pdf_path):
        """Test has_text_content returns False when no extraction result."""
        paper = Paper(
            file_path=sample_pdf_path,
            text_content=None,
            text_extraction_result=None,
        )

        assert paper.has_text_content is False

    def test_has_text_content_property_false_failed_extraction(self, sample_pdf_path):
        """Test has_text_content returns False when extraction failed."""
        extraction_result = TextExtractionResult(
            status=ExtractionStatus.FAILED,
            text_content=None,
            raw_text_length=0,
            clean_text_length=0,
            page_count=5,
            extraction_time_seconds=0.1,
            error_message="PDF is encrypted",
        )

        paper = Paper(
            file_path=sample_pdf_path,
            text_content=None,
            text_extraction_result=extraction_result,
        )

        assert paper.has_text_content is False

    def test_has_text_content_property_false_empty_text(self, sample_pdf_path):
        """Test has_text_content returns False when text is empty string."""
        extraction_result = TextExtractionResult(
            status=ExtractionStatus.SUCCESS,
            text_content="",
            raw_text_length=0,
            clean_text_length=0,
            page_count=0,
            extraction_time_seconds=0.0,
        )

        paper = Paper(
            file_path=sample_pdf_path,
            text_content="",
            text_extraction_result=extraction_result,
        )

        assert paper.has_text_content is False

    def test_has_text_content_property_true_partial_extraction(self, sample_pdf_path):
        """Test has_text_content returns True for PARTIAL extraction status."""
        extraction_result = TextExtractionResult(
            status=ExtractionStatus.PARTIAL,
            text_content="Partially extracted text",
            raw_text_length=1000,
            clean_text_length=500,
            page_count=10,
            extraction_time_seconds=0.5,
            warnings=["Some warnings"],
        )

        paper = Paper(
            file_path=sample_pdf_path,
            text_content="Partially extracted text",
            text_extraction_result=extraction_result,
        )

        assert paper.has_text_content is True

    def test_text_extraction_status_property_not_attempted(self, sample_pdf_path):
        """Test text_extraction_status returns NOT_ATTEMPTED when no result."""
        paper = Paper(
            file_path=sample_pdf_path,
            text_extraction_result=None,
        )

        assert paper.text_extraction_status == ExtractionStatus.NOT_ATTEMPTED

    def test_text_extraction_status_property_success(self, sample_pdf_path):
        """Test text_extraction_status returns SUCCESS status."""
        extraction_result = TextExtractionResult(
            status=ExtractionStatus.SUCCESS,
            text_content="text",
            raw_text_length=100,
            clean_text_length=90,
            page_count=5,
            extraction_time_seconds=0.1,
        )

        paper = Paper(
            file_path=sample_pdf_path,
            text_extraction_result=extraction_result,
        )

        assert paper.text_extraction_status == ExtractionStatus.SUCCESS

    def test_text_extraction_status_property_failed(self, sample_pdf_path):
        """Test text_extraction_status returns FAILED status."""
        extraction_result = TextExtractionResult(
            status=ExtractionStatus.FAILED,
            text_content=None,
            raw_text_length=0,
            clean_text_length=0,
            page_count=0,
            extraction_time_seconds=0.0,
            error_message="Error",
        )

        paper = Paper(
            file_path=sample_pdf_path,
            text_extraction_result=extraction_result,
        )

        assert paper.text_extraction_status == ExtractionStatus.FAILED

    def test_text_extraction_status_property_partial(self, sample_pdf_path):
        """Test text_extraction_status returns PARTIAL status."""
        extraction_result = TextExtractionResult(
            status=ExtractionStatus.PARTIAL,
            text_content="text",
            raw_text_length=100,
            clean_text_length=90,
            page_count=5,
            extraction_time_seconds=0.1,
            warnings=["Warning"],
        )

        paper = Paper(
            file_path=sample_pdf_path,
            text_extraction_result=extraction_result,
        )

        assert paper.text_extraction_status == ExtractionStatus.PARTIAL


class TestPaperBackwardCompatibility:
    """Tests to ensure backward compatibility with existing Paper usage."""

    @pytest.fixture
    def sample_pdf_path(self, tmp_path):
        """Create a temporary PDF file for testing."""
        pdf_file = tmp_path / "test_paper.pdf"
        pdf_file.write_text("dummy pdf content")
        return pdf_file

    def test_paper_creation_without_new_fields(self, sample_pdf_path):
        """Test creating Paper without specifying new text extraction fields."""
        paper = Paper(
            file_path=sample_pdf_path,
            title="Test Paper",
            authors=["Author A", "Author B"],
            abstract="This is a test abstract.",
        )

        # New fields should have default values
        assert paper.text_content is None
        assert paper.text_extraction_result is None
        assert paper.token_count is None
        assert paper.was_truncated is False

        # Existing fields should work as before
        assert paper.title == "Test Paper"
        assert len(paper.authors) == 2
        assert paper.abstract == "This is a test abstract."

    def test_paper_properties_safe_when_no_extraction(self, sample_pdf_path):
        """Test that new properties don't break when no extraction performed."""
        paper = Paper(file_path=sample_pdf_path)

        # Should not raise exceptions
        assert paper.has_text_content is False
        assert paper.text_extraction_status == ExtractionStatus.NOT_ATTEMPTED
