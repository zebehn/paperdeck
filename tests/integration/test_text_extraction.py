"""
Integration tests for end-to-end text extraction flow.

Following TDD approach: These tests are written FIRST and should FAIL initially.
Tests verify the complete text extraction pipeline.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from paperdeck.extraction.text_extractor import PyMuPDFTextExtractor
from paperdeck.core.config import TextExtractionConfig
from paperdeck.models.extraction_result import ExtractionStatus


class TestTextExtractionIntegration:
    """Integration tests for complete text extraction workflow."""

    @pytest.fixture
    def extractor(self):
        """Create text extractor with sanitizer."""
        return PyMuPDFTextExtractor()

    @pytest.fixture
    def default_config(self):
        return TextExtractionConfig()

    @pytest.fixture
    def sample_pdf_path(self, tmp_path):
        return tmp_path / "paper.pdf"

    def test_end_to_end_extraction_with_sanitization(
        self, extractor, default_config, sample_pdf_path
    ):
        """Test complete flow: PDF → extraction → sanitization → result."""
        # This test will FAIL initially

        with patch('src.paperdeck.extraction.text_extractor.fitz') as mock_fitz:
            mock_doc = MagicMock()
            mock_page = MagicMock()
            mock_page.column_boxes.return_value = [MagicMock()]

            # Simulate raw PDF text with artifacts
            raw_text = """Abstract: This paper presents a novel approach.

1

DOI: 10.1234/example.2023

Introduction: Recent advances have shown...

2

Author et al. - Paper Title"""

            mock_page.get_text.return_value = raw_text
            mock_doc.__iter__.return_value = [mock_page]
            mock_doc.__len__.return_value = 1
            mock_fitz.open.return_value = mock_doc

            result = extractor.extract(sample_pdf_path, default_config)

            # Should succeed
            assert result.status == ExtractionStatus.SUCCESS

            # Should have extracted and sanitized text
            assert result.text_content is not None
            assert len(result.text_content) > 0

            # Artifacts should be removed by sanitization
            assert "DOI:" not in result.text_content
            # Page numbers should be removed
            assert "\n1\n" not in result.text_content

            # Content should be preserved
            assert "Abstract" in result.text_content
            assert "Introduction" in result.text_content

            # Metadata should be accurate
            assert result.page_count == 1
            assert result.raw_text_length > result.clean_text_length  # Sanitization removed text
            assert result.extraction_time_seconds >= 0

    def test_extraction_flow_with_multi_page_document(
        self, extractor, default_config, sample_pdf_path
    ):
        """Test extraction flow with multiple pages."""
        # This test will FAIL initially

        with patch('src.paperdeck.extraction.text_extractor.fitz') as mock_fitz:
            mock_doc = MagicMock()

            # Page 1: Abstract
            page1 = MagicMock()
            page1.column_boxes.return_value = [MagicMock()]
            page1.get_text.return_value = "Abstract: We propose a new method.\n1"

            # Page 2: Introduction
            page2 = MagicMock()
            page2.column_boxes.return_value = [MagicMock()]
            page2.get_text.return_value = "Introduction: Background information.\n2"

            # Page 3: Results
            page3 = MagicMock()
            page3.column_boxes.return_value = [MagicMock()]
            page3.get_text.return_value = "Results: Our experiments show improvements.\n3"

            mock_doc.__iter__.return_value = [page1, page2, page3]
            mock_doc.__len__.return_value = 3
            mock_fitz.open.return_value = mock_doc

            result = extractor.extract(sample_pdf_path, default_config)

            # Should succeed with all pages
            assert result.status == ExtractionStatus.SUCCESS
            assert result.page_count == 3

            # Should contain text from all pages
            assert "Abstract" in result.text_content
            assert "Introduction" in result.text_content
            assert "Results" in result.text_content

            # Page numbers should be sanitized
            assert "\n1" not in result.text_content or "1" not in result.text_content.split()[0]
            assert "\n2" not in result.text_content or "2" not in result.text_content.split()[0]
            assert "\n3" not in result.text_content or "3" not in result.text_content.split()[0]

    def test_extraction_flow_with_two_column_layout(
        self, extractor, default_config, sample_pdf_path
    ):
        """Test extraction flow with two-column academic paper."""
        # This test will FAIL initially

        with patch('src.paperdeck.extraction.text_extractor.fitz') as mock_fitz:
            mock_doc = MagicMock()
            mock_page = MagicMock()

            # Simulate two columns
            column1 = MagicMock()
            column2 = MagicMock()
            mock_page.column_boxes.return_value = [column1, column2]

            # Text flows across columns
            mock_page.get_text.side_effect = [
                "Left column: Abstract and introduction text...",
                "Right column: Methodology and results text..."
            ]

            mock_doc.__iter__.return_value = [mock_page]
            mock_doc.__len__.return_value = 1
            mock_fitz.open.return_value = mock_doc

            result = extractor.extract(sample_pdf_path, default_config)

            # Should succeed
            assert result.status == ExtractionStatus.SUCCESS

            # Should have text from both columns
            assert "Left column" in result.text_content
            assert "Right column" in result.text_content

    def test_extraction_flow_handles_failure_gracefully(
        self, extractor, default_config
    ):
        """Test that extraction flow handles failures gracefully."""
        # This test will FAIL initially

        missing_pdf = Path("/definitely/does/not/exist.pdf")

        result = extractor.extract(missing_pdf, default_config)

        # Should return FAILED status, not crash
        assert result.status == ExtractionStatus.FAILED
        assert result.error_message is not None
        assert result.text_content is None or len(result.text_content) == 0

        # Metadata should still be populated
        assert result.extraction_time_seconds >= 0
        assert result.raw_text_length == 0
        assert result.clean_text_length == 0

    def test_extraction_flow_respects_configuration(
        self, extractor, sample_pdf_path
    ):
        """Test that extraction flow respects all configuration options."""
        # This test will FAIL initially

        custom_config = TextExtractionConfig(
            header_margin=100,
            footer_margin=100,
            remove_page_numbers=True,
            remove_headers_footers=True,
            min_line_length=5
        )

        with patch('src.paperdeck.extraction.text_extractor.fitz') as mock_fitz:
            mock_doc = MagicMock()
            mock_page = MagicMock()
            mock_page.column_boxes.return_value = [MagicMock()]
            mock_page.get_text.return_value = "Good content here\na\nbb\nccc\ndddd\neeeee"
            mock_doc.__iter__.return_value = [mock_page]
            mock_doc.__len__.return_value = 1
            mock_fitz.open.return_value = mock_doc

            result = extractor.extract(sample_pdf_path, custom_config)

            assert result.status == ExtractionStatus.SUCCESS

            # Very short lines (< 5 chars) should be removed
            assert "a" not in result.text_content or len(result.text_content.split()) > 5
            assert "bb" not in result.text_content or len(result.text_content.split()) > 5

            # Longer content should remain
            assert "Good content" in result.text_content or "content here" in result.text_content


class TestTextExtractionIntegrationPerformance:
    """Integration tests for extraction performance."""

    @pytest.fixture
    def extractor(self):
        return PyMuPDFTextExtractor()

    @pytest.fixture
    def default_config(self):
        return TextExtractionConfig()

    def test_extraction_flow_completes_quickly_for_typical_paper(
        self, extractor, default_config, tmp_path
    ):
        """Test that extraction completes quickly for typical 10-page paper."""
        # This test will FAIL initially

        import time

        pdf_path = tmp_path / "typical_paper.pdf"

        with patch('src.paperdeck.extraction.text_extractor.fitz') as mock_fitz:
            mock_doc = MagicMock()

            # Simulate 10-page paper
            pages = []
            for i in range(10):
                page = MagicMock()
                page.column_boxes.return_value = [MagicMock()]
                page.get_text.return_value = f"Page {i} with typical academic content. " * 50
                pages.append(page)

            mock_doc.__iter__.return_value = pages
            mock_doc.__len__.return_value = 10
            mock_fitz.open.return_value = mock_doc

            start = time.time()
            result = extractor.extract(pdf_path, default_config)
            elapsed = time.time() - start

            assert result.status == ExtractionStatus.SUCCESS
            assert elapsed < 2.0, f"Should complete in < 2s for 10 pages, took {elapsed:.2f}s"

    def test_extraction_metrics_are_consistent(
        self, extractor, default_config, tmp_path
    ):
        """Test that extraction metrics (raw vs clean length) are consistent."""
        # This test will FAIL initially

        pdf_path = tmp_path / "paper.pdf"

        with patch('src.paperdeck.extraction.text_extractor.fitz') as mock_fitz:
            mock_doc = MagicMock()
            mock_page = MagicMock()
            mock_page.column_boxes.return_value = [MagicMock()]

            # Raw text with artifacts
            mock_page.get_text.return_value = "Content\n1\nDOI: 10.1234\nMore content"

            mock_doc.__iter__.return_value = [mock_page]
            mock_doc.__len__.return_value = 1
            mock_fitz.open.return_value = mock_doc

            result = extractor.extract(pdf_path, default_config)

            # Metrics should be consistent
            assert result.raw_text_length >= result.clean_text_length
            assert result.clean_text_length == len(result.text_content)
            assert result.sanitization_reduction_pct >= 0
            assert result.sanitization_reduction_pct <= 100
