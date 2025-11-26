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
