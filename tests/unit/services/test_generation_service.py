"""
Unit tests for GenerationService.

Tests the orchestration of text extraction within the generation workflow.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from src.paperdeck.services.generation_service import GenerationService
from src.paperdeck.core.config import AppConfiguration, TextExtractionConfig
from src.paperdeck.models.extraction_result import ExtractionStatus, TextExtractionResult


class TestGenerationServicePaperPreparation:
    """Tests for prepare_paper method."""

    @pytest.fixture
    def app_config(self):
        """Create app configuration with text extraction enabled."""
        config = AppConfiguration()
        config.text_extraction = TextExtractionConfig(enabled=True)
        return config

    @pytest.fixture
    def service(self, app_config):
        """Create generation service instance."""
        return GenerationService(app_config)

    @pytest.fixture
    def sample_pdf_path(self, tmp_path):
        """Create a temporary PDF path."""
        pdf_file = tmp_path / "test_paper.pdf"
        pdf_file.write_text("dummy pdf")
        return pdf_file

    def test_prepare_paper_with_successful_extraction(self, service, sample_pdf_path):
        """Test that prepare_paper populates Paper with extracted text."""
        # Mock successful extraction
        mock_result = TextExtractionResult(
            status=ExtractionStatus.SUCCESS,
            text_content="Abstract: This paper presents novel methods...",
            raw_text_length=5000,
            clean_text_length=4500,
            page_count=10,
            extraction_time_seconds=0.5,
        )

        with patch.object(service.text_extractor, 'extract', return_value=mock_result):
            paper = service.prepare_paper(sample_pdf_path)

            assert paper.file_path == sample_pdf_path
            assert paper.text_content == "Abstract: This paper presents novel methods..."
            assert paper.text_extraction_result == mock_result
            assert paper.has_text_content is True

    def test_prepare_paper_with_failed_extraction(self, service, sample_pdf_path):
        """Test graceful fallback when extraction fails."""
        # Mock failed extraction
        mock_result = TextExtractionResult(
            status=ExtractionStatus.FAILED,
            text_content=None,
            raw_text_length=0,
            clean_text_length=0,
            page_count=0,
            extraction_time_seconds=0.1,
            error_message="PDF is encrypted",
        )

        with patch.object(service.text_extractor, 'extract', return_value=mock_result):
            paper = service.prepare_paper(sample_pdf_path)

            # Should return Paper without text content (graceful fallback)
            assert paper.file_path == sample_pdf_path
            assert paper.text_content is None
            assert paper.has_text_content is False

    def test_prepare_paper_with_extraction_disabled(self, sample_pdf_path):
        """Test that extraction is skipped when disabled."""
        config = AppConfiguration()
        config.text_extraction = TextExtractionConfig(enabled=False)
        service = GenerationService(config)

        # Should not call extract when disabled
        with patch.object(service.text_extractor, 'extract') as mock_extract:
            paper = service.prepare_paper(sample_pdf_path)

            mock_extract.assert_not_called()
            assert paper.text_content is None

    def test_prepare_paper_with_extraction_exception(self, service, sample_pdf_path):
        """Test graceful fallback when extraction raises exception."""
        # Mock extraction raising exception
        with patch.object(
            service.text_extractor, 'extract', side_effect=RuntimeError("Unexpected error")
        ):
            # Should NOT raise exception - should fall back gracefully
            paper = service.prepare_paper(sample_pdf_path)

            assert paper.file_path == sample_pdf_path
            assert paper.text_content is None
            assert paper.has_text_content is False

    def test_prepare_paper_uses_custom_extraction_config(self, service, sample_pdf_path):
        """Test that custom extraction config is passed to extractor."""
        custom_config = TextExtractionConfig(
            enabled=True,
            header_margin=100,
            footer_margin=100,
            remove_page_numbers=False,
        )

        mock_result = TextExtractionResult(
            status=ExtractionStatus.SUCCESS,
            text_content="Text with page numbers",
            raw_text_length=100,
            clean_text_length=100,
            page_count=5,
            extraction_time_seconds=0.2,
        )

        with patch.object(service.text_extractor, 'extract', return_value=mock_result) as mock_extract:
            paper = service.prepare_paper(sample_pdf_path, extraction_config=custom_config)

            # Verify extract was called with custom config
            mock_extract.assert_called_once_with(sample_pdf_path, custom_config)
            assert paper.text_content == "Text with page numbers"


class TestGenerationServiceLogging:
    """Tests for logging functionality."""

    @pytest.fixture
    def app_config(self):
        """Create app configuration."""
        config = AppConfiguration()
        config.text_extraction = TextExtractionConfig(enabled=True)
        return config

    @pytest.fixture
    def service(self, app_config):
        """Create generation service instance."""
        return GenerationService(app_config)

    @pytest.fixture
    def sample_pdf_path(self, tmp_path):
        """Create a temporary PDF path."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("dummy")
        return pdf_file

    def test_logging_on_successful_extraction(self, service, sample_pdf_path, caplog):
        """Test that successful extraction is logged."""
        mock_result = TextExtractionResult(
            status=ExtractionStatus.SUCCESS,
            text_content="Text content",
            raw_text_length=1000,
            clean_text_length=900,
            page_count=5,
            extraction_time_seconds=0.3,
        )

        with patch.object(service.text_extractor, 'extract', return_value=mock_result):
            with caplog.at_level('INFO'):
                paper = service.prepare_paper(sample_pdf_path)

                # Check that success is logged
                assert "Text extraction successful" in caplog.text
                assert "5 pages" in caplog.text
                assert "900 characters" in caplog.text

    def test_logging_on_failed_extraction(self, service, sample_pdf_path, caplog):
        """Test that failed extraction is logged with warning."""
        mock_result = TextExtractionResult(
            status=ExtractionStatus.FAILED,
            text_content=None,
            raw_text_length=0,
            clean_text_length=0,
            page_count=0,
            extraction_time_seconds=0.1,
            error_message="File corrupted",
        )

        with patch.object(service.text_extractor, 'extract', return_value=mock_result):
            with caplog.at_level('WARNING'):
                paper = service.prepare_paper(sample_pdf_path)

                # Check that failure and fallback are logged
                assert "Text extraction failed" in caplog.text
                assert "Falling back to metadata-only mode" in caplog.text
                assert "File corrupted" in caplog.text

    def test_logging_on_extraction_exception(self, service, sample_pdf_path, caplog):
        """Test that exceptions are logged with error level."""
        with patch.object(
            service.text_extractor, 'extract', side_effect=ValueError("Bad input")
        ):
            with caplog.at_level('WARNING'):  # Capture WARNING and above
                paper = service.prepare_paper(sample_pdf_path)

                # Check that error and fallback are logged
                assert "Unexpected error during text extraction" in caplog.text
                assert "Falling back to metadata-only mode" in caplog.text
