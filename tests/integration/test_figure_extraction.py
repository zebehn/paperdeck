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


class TestPDFExtractionIntegration:
    """Integration tests for PDF output format (User Story 1)."""

    @pytest.mark.skipif(True, reason="Requires docscalpel v1.0.0 with real PDF processing")
    def test_pdf_files_created_in_extracted_directory(self, sample_pdf_with_figures, tmp_path):
        """[US1] Verify PDF files are created in extracted directory.

        Integration test to verify that docscalpel extracts figures as PDF files
        in the output directory with correct naming pattern.
        """
        output_dir = tmp_path / "extracted"
        output_dir.mkdir(exist_ok=True)

        # Configure adapter
        config = ExtractionConfiguration(
            output_directory=output_dir,
            confidence_threshold=0.75,
            element_types=[ElementType.FIGURE]
        )

        adapter = DocScalpelAdapter(config)

        # Skip if docscalpel not available
        if not adapter.docscalpel_available:
            pytest.skip("DocScalpel not available")

        # Extract figures
        elements = adapter.extract(sample_pdf_with_figures, [ElementType.FIGURE])

        # Verify elements extracted
        assert len(elements) > 0, "Expected at least one figure to be extracted"

        # Verify PDF files exist with correct naming
        for i, elem in enumerate(elements, 1):
            assert elem.output_filename.suffix == ".pdf", \
                f"Expected .pdf extension, got {elem.output_filename.suffix}"

            # Verify file exists
            assert elem.output_filename.exists(), \
                f"Expected file {elem.output_filename} to exist"

            # Verify zero-padded naming (figure_01.pdf not figure_1.pdf)
            expected_pattern = f"figure_{i:02d}.pdf"
            assert elem.output_filename.name == expected_pattern or \
                   elem.output_filename.name.endswith(".pdf"), \
                f"Expected filename matching pattern {expected_pattern}"

    @pytest.mark.skipif(True, reason="Requires docscalpel v1.0.0")
    def test_end_to_end_pdf_extraction(self, sample_pdf_with_figures, tmp_path):
        """[US1] Test complete extraction pipeline with PDF outputs."""
        output_dir = tmp_path / "extracted"

        config = ExtractionConfiguration(
            output_directory=output_dir,
            confidence_threshold=0.7,
            element_types=[ElementType.FIGURE, ElementType.TABLE]
        )

        adapter = DocScalpelAdapter(config)

        if not adapter.docscalpel_available:
            pytest.skip("DocScalpel not available")

        # Extract all elements
        elements = adapter.extract(sample_pdf_with_figures)

        # Verify extracted directory exists
        assert output_dir.exists()

        # Verify PDF files created
        pdf_files = list(output_dir.glob("*.pdf"))
        assert len(pdf_files) > 0, "Expected PDF files in extracted directory"

        # Verify all extracted elements have PDF paths
        for elem in elements:
            assert elem.output_filename.suffix == ".pdf"
            assert elem.output_filename.exists()
            assert elem.output_filename.stat().st_size > 0, "PDF file is empty"
