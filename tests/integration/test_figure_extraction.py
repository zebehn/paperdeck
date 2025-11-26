"""
Integration tests for figure and table extraction.

Tests the complete extraction workflow with DocScalpel adapter.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from paperdeck.extraction.docscalpel_adapter import DocScalpelAdapter
from paperdeck.extraction.element_processor import ElementProcessor
from paperdeck.core.models import ElementType
from paperdeck.core.config import ExtractionConfiguration


class TestFigureExtractionIntegration:
    """Integration tests for figure extraction workflow."""

    @pytest.fixture
    def output_dir(self, tmp_path):
        """Create temporary output directory."""
        return tmp_path / "extracted"

    @pytest.fixture
    def adapter(self):
        """Create DocScalpel adapter."""
        return DocScalpelAdapter()

    @pytest.fixture
    def processor(self, output_dir):
        """Create element processor."""
        return ElementProcessor(output_dir)

    def test_extraction_without_docscalpel_installed(self, adapter, tmp_path):
        """Test extraction gracefully skips when DocScalpel not installed."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("dummy pdf content")

        # Force docscalpel unavailable
        adapter.docscalpel_available = False

        results = adapter.extract(pdf_file, [ElementType.FIGURE])

        assert results == []

    def test_element_processor_saves_to_correct_directory(self, processor, output_dir):
        """Test element processor creates files in correct directory."""
        figure_data = b"test figure data"

        result_path = processor.save_figure(figure_data, 1)

        assert result_path.parent == output_dir
        assert result_path.exists()


class TestTableExtractionIntegration:
    """Integration tests for table extraction workflow."""

    @pytest.fixture
    def output_dir(self, tmp_path):
        """Create temporary output directory."""
        return tmp_path / "extracted"

    @pytest.fixture
    def processor(self, output_dir):
        """Create element processor."""
        return ElementProcessor(output_dir)

    def test_table_processor_saves_to_correct_directory(self, processor, output_dir):
        """Test table processor creates files in correct directory."""
        table_data = b"test table data"

        result_path = processor.save_table(table_data, 1)

        assert result_path.parent == output_dir
        assert result_path.exists()


class TestEndToEndExtraction:
    """End-to-end extraction workflow tests."""

    @pytest.fixture
    def extraction_config(self):
        """Create extraction configuration."""
        return ExtractionConfiguration(
            confidence_threshold=0.75,
            element_types=[ElementType.FIGURE, ElementType.TABLE],
        )

    def test_full_extraction_workflow_stub(self, tmp_path, extraction_config):
        """Test complete extraction workflow (stub for now)."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("dummy pdf")
        output_dir = tmp_path / "extracted"

        # Create components
        adapter = DocScalpelAdapter(extraction_config)
        processor = ElementProcessor(output_dir)

        # Extract (will return empty for now)
        elements = adapter.extract(pdf_file, extraction_config.element_types)

        # Verify output directory was created
        assert output_dir.exists()

        # For now, just verify no errors occurred
        assert isinstance(elements, list)
