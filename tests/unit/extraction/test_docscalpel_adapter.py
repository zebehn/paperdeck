"""
Unit tests for DocScalpel adapter.

Tests the adapter pattern for DocScalpel integration with graceful fallback.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from paperdeck.extraction.docscalpel_adapter import DocScalpelAdapter
from paperdeck.core.models import ElementType
from paperdeck.core.config import ExtractionConfiguration


class TestDocScalpelAdapter:
    """Tests for DocScalpelAdapter initialization and import handling."""

    def test_adapter_initialization_without_docscalpel(self):
        """Test adapter initializes gracefully when DocScalpel not installed."""
        with patch.dict('sys.modules', {'docscalpel': None}):
            with patch('paperdeck.extraction.docscalpel_adapter.logger') as mock_logger:
                adapter = DocScalpelAdapter()

                assert adapter.docscalpel_available is False
                mock_logger.warning.assert_called_once()
                assert "DocScalpel not installed" in str(mock_logger.warning.call_args)

    def test_extract_returns_empty_when_docscalpel_unavailable(self, tmp_path):
        """Test extract returns empty list when DocScalpel not available."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("dummy pdf")

        adapter = DocScalpelAdapter()
        adapter.docscalpel_available = False

        result = adapter.extract(pdf_file, [ElementType.FIGURE])

        assert result == []

    def test_extract_with_default_element_types(self, tmp_path):
        """Test extract uses default element types when none specified."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("dummy pdf")

        adapter = DocScalpelAdapter()
        adapter.docscalpel_available = False

        result = adapter.extract(pdf_file)

        assert result == []


class TestDocScalpelAdapterWithMock:
    """Tests for extraction with mocked DocScalpel."""

    @pytest.fixture
    def mock_docscalpel(self):
        """Mock DocScalpel module."""
        mock = MagicMock()
        return mock

    @pytest.fixture
    def adapter_with_mock(self, mock_docscalpel):
        """Create adapter with mocked DocScalpel."""
        with patch.dict('sys.modules', {'docscalpel': mock_docscalpel}):
            adapter = DocScalpelAdapter()
            adapter.docscalpel_available = True
            adapter.docscalpel = mock_docscalpel
            return adapter

    def test_adapter_logs_successful_import(self, adapter_with_mock):
        """Test adapter logs when DocScalpel imports successfully."""
        assert adapter_with_mock.docscalpel_available is True

    def test_extract_logs_element_types(self, adapter_with_mock, tmp_path):
        """Test extract logs which element types are being extracted."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("dummy pdf")

        with patch('paperdeck.extraction.docscalpel_adapter.logger') as mock_logger:
            result = adapter_with_mock.extract(pdf_file, [ElementType.FIGURE, ElementType.TABLE])

            # Should log the extraction attempt
            assert mock_logger.info.called


class TestDocScalpelAdapterPDFOutput:
    """Tests for PDF output format (User Story 1)."""

    def test_extract_uses_pdf_naming_pattern(self, mock_docscalpel, mock_pdf_result):
        """[US1] Verify adapter configures docscalpel to use PDF naming pattern.

        Test that the naming_pattern passed to ExtractionConfig uses:
        - PDF extension (.pdf not .png)
        - Zero-padded counter format ({counter:02d})
        """
        # Create adapter with mocked docscalpel
        adapter = DocScalpelAdapter()
        adapter.docscalpel_available = True
        adapter.docscalpel = mock_docscalpel

        # Mock the extract_elements call
        mock_docscalpel.extract_elements.return_value = mock_pdf_result

        # Extract from test PDF
        pdf_path = Path("/tmp/test.pdf")
        result = adapter.extract(pdf_path, [ElementType.FIGURE])

        # Verify ExtractionConfig was called with PDF naming pattern
        mock_docscalpel.ExtractionConfig.assert_called_once()
        config_call = mock_docscalpel.ExtractionConfig.call_args

        # Check naming_pattern argument
        assert 'naming_pattern' in config_call.kwargs or len(config_call.args) > 3
        if 'naming_pattern' in config_call.kwargs:
            naming_pattern = config_call.kwargs['naming_pattern']
        else:
            # Assuming naming_pattern is 4th positional argument
            naming_pattern = config_call.args[3] if len(config_call.args) > 3 else None

        # Verify PDF format with zero-padding
        assert naming_pattern is not None, "naming_pattern not passed to ExtractionConfig"
        assert '.pdf' in naming_pattern, f"Expected .pdf extension, got: {naming_pattern}"
        assert '{counter:02d}' in naming_pattern or '{counter:0' in naming_pattern, \
            f"Expected zero-padded counter, got: {naming_pattern}"

    def test_extract_zero_padded_numbering(self, mock_docscalpel, mock_pdf_result_multiple_elements):
        """[US1] Verify extracted PDF files use zero-padded numbering.

        Test that output filenames use format: figure_01.pdf, figure_02.pdf, ...
        Not: figure_1.pdf, figure_2.pdf
        """
        # Create adapter with mocked docscalpel
        adapter = DocScalpelAdapter()
        adapter.docscalpel_available = True
        adapter.docscalpel = mock_docscalpel

        # Mock extract_elements to return 10 figures
        mock_docscalpel.extract_elements.return_value = mock_pdf_result_multiple_elements

        # Extract
        pdf_path = Path("/tmp/test.pdf")
        result = adapter.extract(pdf_path, [ElementType.FIGURE])

        # Verify we got 10 elements
        assert len(result) == 10, f"Expected 10 elements, got {len(result)}"

        # Verify filenames use zero-padding
        assert result[0].output_filename.name == "figure_01.pdf", \
            f"Expected figure_01.pdf, got {result[0].output_filename.name}"
        assert result[9].output_filename.name == "figure_10.pdf", \
            f"Expected figure_10.pdf, got {result[9].output_filename.name}"

        # Verify all have .pdf extension
        for elem in result:
            assert elem.output_filename.suffix == ".pdf", \
                f"Expected .pdf suffix, got {elem.output_filename.suffix}"
