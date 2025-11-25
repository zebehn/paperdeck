"""
Unit tests for PyMuPDFTextExtractor.

Following TDD approach: These tests are written FIRST and should FAIL initially.
Tests define the expected behavior of text extraction.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from paperdeck.extraction.text_extractor import PyMuPDFTextExtractor
from paperdeck.core.config import TextExtractionConfig
from paperdeck.models.extraction_result import ExtractionStatus, TextExtractionResult


class TestPyMuPDFTextExtractorBasic:
    """Tests for basic text extraction functionality."""

    @pytest.fixture
    def extractor(self):
        """Create a text extractor instance."""
        return PyMuPDFTextExtractor()

    @pytest.fixture
    def default_config(self):
        """Create default extraction config."""
        return TextExtractionConfig()

    @pytest.fixture
    def sample_pdf_path(self, tmp_path):
        """Create a sample PDF path."""
        pdf_file = tmp_path / "sample.pdf"
        # Note: Actual PDF creation would require reportlab or similar
        # For unit tests, we'll mock the PDF reading
        return pdf_file

    def test_extract_returns_success_status(self, extractor, default_config, sample_pdf_path):
        """Test that extract() returns SUCCESS status for valid PDF."""
        # This test will FAIL initially (PyMuPDFTextExtractor doesn't exist yet)

        # Mock fitz (PyMuPDF) to simulate PDF reading
        with patch('src.paperdeck.extraction.text_extractor.fitz') as mock_fitz:
            mock_doc = MagicMock()
            mock_page = MagicMock()
            mock_page.column_boxes.return_value = [MagicMock()]  # One column
            mock_page.get_text.return_value = "Sample text from PDF"
            mock_doc.__iter__.return_value = [mock_page]
            mock_doc.__len__.return_value = 1
            mock_fitz.open.return_value = mock_doc

            result = extractor.extract(sample_pdf_path, default_config)

            assert isinstance(result, TextExtractionResult)
            assert result.status == ExtractionStatus.SUCCESS
            assert result.text_content is not None
            assert len(result.text_content) > 0
            assert result.page_count > 0
            assert result.extraction_time_seconds >= 0

    def test_extract_handles_missing_file(self, extractor, default_config):
        """Test that extract() handles missing files gracefully."""
        # This test will FAIL initially

        missing_path = Path("/nonexistent/file.pdf")
        result = extractor.extract(missing_path, default_config)

        assert isinstance(result, TextExtractionResult)
        assert result.status == ExtractionStatus.FAILED
        assert result.error_message is not None
        assert "not found" in result.error_message.lower() or "no such file" in result.error_message.lower()

    def test_extract_handles_encrypted_pdf(self, extractor, default_config, sample_pdf_path):
        """Test that extract() handles encrypted PDFs gracefully."""
        # This test will FAIL initially

        with patch('src.paperdeck.extraction.text_extractor.fitz') as mock_fitz:
            # Simulate encrypted PDF error
            mock_fitz.open.side_effect = RuntimeError("PDF is encrypted")

            result = extractor.extract(sample_pdf_path, default_config)

            assert isinstance(result, TextExtractionResult)
            assert result.status == ExtractionStatus.FAILED
            assert result.error_message is not None
            assert "encrypted" in result.error_message.lower()


class TestPyMuPDFTextExtractorMultiColumn:
    """Tests for multi-column PDF extraction."""

    @pytest.fixture
    def extractor(self):
        return PyMuPDFTextExtractor()

    @pytest.fixture
    def default_config(self):
        return TextExtractionConfig()

    @pytest.fixture
    def sample_pdf_path(self, tmp_path):
        pdf_file = tmp_path / "multicolumn.pdf"
        return pdf_file

    def test_extract_detects_multi_column_layout(self, extractor, default_config, sample_pdf_path):
        """Test that extract() detects and handles multi-column layouts."""
        # This test will FAIL initially

        with patch('src.paperdeck.extraction.text_extractor.fitz') as mock_fitz:
            mock_doc = MagicMock()
            mock_page = MagicMock()

            # Simulate two-column layout
            column1_box = MagicMock()
            column2_box = MagicMock()
            mock_page.column_boxes.return_value = [column1_box, column2_box]

            # Each column returns different text
            mock_page.get_text.side_effect = [
                "Text from column 1",
                "Text from column 2"
            ]

            mock_doc.__iter__.return_value = [mock_page]
            mock_doc.__len__.return_value = 1
            mock_fitz.open.return_value = mock_doc

            result = extractor.extract(sample_pdf_path, default_config)

            assert result.status == ExtractionStatus.SUCCESS
            # Should have text from both columns
            assert "column 1" in result.text_content.lower()
            assert "column 2" in result.text_content.lower()

    def test_extract_uses_column_boxes_with_margins(self, extractor, sample_pdf_path):
        """Test that extract() passes margin config to column_boxes()."""
        # This test will FAIL initially

        config = TextExtractionConfig(
            header_margin=75,
            footer_margin=100,
            remove_image_text=False
        )

        with patch('src.paperdeck.extraction.text_extractor.fitz') as mock_fitz:
            mock_doc = MagicMock()
            mock_page = MagicMock()
            mock_page.column_boxes.return_value = [MagicMock()]
            mock_page.get_text.return_value = "Text"
            mock_doc.__iter__.return_value = [mock_page]
            mock_doc.__len__.return_value = 1
            mock_fitz.open.return_value = mock_doc

            result = extractor.extract(sample_pdf_path, config)

            # Verify column_boxes was called with correct margins
            mock_page.column_boxes.assert_called_once()
            call_kwargs = mock_page.column_boxes.call_args.kwargs
            assert call_kwargs.get('footer_margin') == 100 or call_kwargs.get('header_margin') == 75


class TestPyMuPDFTextExtractorPerformance:
    """Tests for extraction performance requirements."""

    @pytest.fixture
    def extractor(self):
        return PyMuPDFTextExtractor()

    @pytest.fixture
    def default_config(self):
        return TextExtractionConfig()

    @pytest.fixture
    def large_pdf_path(self, tmp_path):
        """Simulate a 50-page PDF."""
        pdf_file = tmp_path / "large_paper.pdf"
        return pdf_file

    def test_extract_completes_within_10_seconds_for_50_pages(
        self, extractor, default_config, large_pdf_path
    ):
        """Test that extraction meets SC-002: <10s for 50 pages."""
        # This test will FAIL initially

        import time

        with patch('src.paperdeck.extraction.text_extractor.fitz') as mock_fitz:
            mock_doc = MagicMock()

            # Simulate 50 pages
            pages = []
            for i in range(50):
                mock_page = MagicMock()
                mock_page.column_boxes.return_value = [MagicMock()]
                mock_page.get_text.return_value = f"Page {i} text content"
                pages.append(mock_page)

            mock_doc.__iter__.return_value = pages
            mock_doc.__len__.return_value = 50
            mock_fitz.open.return_value = mock_doc

            start_time = time.time()
            result = extractor.extract(large_pdf_path, default_config)
            elapsed_time = time.time() - start_time

            assert result.status == ExtractionStatus.SUCCESS
            assert result.page_count == 50
            assert elapsed_time < 10.0, f"Extraction took {elapsed_time:.2f}s, must be < 10s"
            assert result.extraction_time_seconds < 10.0

    def test_extract_reports_accurate_extraction_time(self, extractor, default_config, large_pdf_path):
        """Test that extraction_time_seconds is accurately recorded."""
        # This test will FAIL initially

        with patch('src.paperdeck.extraction.text_extractor.fitz') as mock_fitz:
            mock_doc = MagicMock()
            mock_page = MagicMock()
            mock_page.column_boxes.return_value = [MagicMock()]
            mock_page.get_text.return_value = "Text"
            mock_doc.__iter__.return_value = [mock_page]
            mock_doc.__len__.return_value = 1
            mock_fitz.open.return_value = mock_doc

            result = extractor.extract(large_pdf_path, default_config)

            assert result.extraction_time_seconds > 0
            assert result.extraction_time_seconds < 1.0  # Should be very fast for 1 page


class TestPyMuPDFTextExtractorTextContent:
    """Tests for text content extraction and quality."""

    @pytest.fixture
    def extractor(self):
        return PyMuPDFTextExtractor()

    @pytest.fixture
    def default_config(self):
        return TextExtractionConfig()

    @pytest.fixture
    def sample_pdf_path(self, tmp_path):
        return tmp_path / "sample.pdf"

    def test_extract_returns_non_empty_text_on_success(self, extractor, default_config, sample_pdf_path):
        """Test that successful extraction returns non-empty text."""
        # This test will FAIL initially

        with patch('src.paperdeck.extraction.text_extractor.fitz') as mock_fitz:
            mock_doc = MagicMock()
            mock_page = MagicMock()
            mock_page.column_boxes.return_value = [MagicMock()]
            mock_page.get_text.return_value = "Sample academic paper text with methodology and results."
            mock_doc.__iter__.return_value = [mock_page]
            mock_doc.__len__.return_value = 1
            mock_fitz.open.return_value = mock_doc

            result = extractor.extract(sample_pdf_path, default_config)

            assert result.status == ExtractionStatus.SUCCESS
            assert result.text_content is not None
            assert len(result.text_content) > 0
            assert result.raw_text_length > 0
            assert result.clean_text_length > 0

    def test_extract_combines_multi_page_text(self, extractor, default_config, sample_pdf_path):
        """Test that text from multiple pages is combined."""
        # This test will FAIL initially

        with patch('src.paperdeck.extraction.text_extractor.fitz') as mock_fitz:
            mock_doc = MagicMock()

            page1 = MagicMock()
            page1.column_boxes.return_value = [MagicMock()]
            page1.get_text.return_value = "Page 1 abstract"

            page2 = MagicMock()
            page2.column_boxes.return_value = [MagicMock()]
            page2.get_text.return_value = "Page 2 introduction"

            mock_doc.__iter__.return_value = [page1, page2]
            mock_doc.__len__.return_value = 2
            mock_fitz.open.return_value = mock_doc

            result = extractor.extract(sample_pdf_path, default_config)

            assert "Page 1 abstract" in result.text_content
            assert "Page 2 introduction" in result.text_content
            assert result.page_count == 2

    def test_extract_records_page_count(self, extractor, default_config, sample_pdf_path):
        """Test that page_count is accurately recorded."""
        # This test will FAIL initially

        with patch('src.paperdeck.extraction.text_extractor.fitz') as mock_fitz:
            mock_doc = MagicMock()

            pages = []
            for i in range(10):
                page = MagicMock()
                page.column_boxes.return_value = [MagicMock()]
                page.get_text.return_value = f"Page {i}"
                pages.append(page)

            mock_doc.__iter__.return_value = pages
            mock_doc.__len__.return_value = 10
            mock_fitz.open.return_value = mock_doc

            result = extractor.extract(sample_pdf_path, default_config)

            assert result.page_count == 10
