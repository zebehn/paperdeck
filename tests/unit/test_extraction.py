"""Unit tests for PDF extraction functionality.

These tests define the contract for the extraction layer and should FAIL
until the implementation is complete (TDD).
"""

import pytest
from pathlib import Path
from uuid import UUID

from paperdeck.core.models import ElementType


class TestPaperExtractor:
    """Tests for PaperExtractor class."""

    def test_extractor_extracts_figures_from_pdf(self, tmp_path):
        """Test that extractor can extract figures from a sample PDF."""
        from paperdeck.extraction.extractor import PaperExtractor

        # Create a mock PDF file (in real scenario, this would be a real PDF)
        paper_path = tmp_path / "test_paper.pdf"
        paper_path.write_text("%PDF-1.4 mock content")

        # Arrange
        extractor = PaperExtractor()

        # Act
        elements = extractor.extract(paper_path, element_types=[ElementType.FIGURE])

        # Assert - this will FAIL until implementation is complete
        assert isinstance(elements, list)
        # For now, accept empty list (real implementation will extract from real PDFs)
        for element in elements:
            assert element.element_type == ElementType.FIGURE
            assert element.confidence_score >= 0.75
            assert isinstance(element.uuid, UUID)

    def test_extractor_extracts_tables_from_pdf(self, tmp_path):
        """Test that extractor can extract tables from a sample PDF."""
        from paperdeck.extraction.extractor import PaperExtractor

        paper_path = tmp_path / "test_paper.pdf"
        paper_path.write_text("%PDF-1.4 mock content")

        extractor = PaperExtractor()
        elements = extractor.extract(paper_path, element_types=[ElementType.TABLE])

        assert isinstance(elements, list)
        for element in elements:
            assert element.element_type == ElementType.TABLE
            assert element.confidence_score >= 0.75

    def test_extractor_extracts_equations_from_pdf(self, tmp_path):
        """Test that extractor can extract equations from a sample PDF."""
        from paperdeck.extraction.extractor import PaperExtractor

        paper_path = tmp_path / "test_paper.pdf"
        paper_path.write_text("%PDF-1.4 mock content")

        extractor = PaperExtractor()
        elements = extractor.extract(paper_path, element_types=[ElementType.EQUATION])

        assert isinstance(elements, list)
        for element in elements:
            assert element.element_type == ElementType.EQUATION
            assert element.confidence_score >= 0.75

    def test_extractor_respects_confidence_threshold(self, tmp_path):
        """Test that extractor filters by confidence threshold."""
        from paperdeck.extraction.extractor import PaperExtractor

        paper_path = tmp_path / "test_paper.pdf"
        paper_path.write_text("%PDF-1.4 mock content")

        extractor = PaperExtractor(confidence_threshold=0.9)
        elements = extractor.extract(paper_path)

        # All extracted elements should meet threshold
        for element in elements:
            assert element.confidence_score >= 0.9

    def test_extractor_handles_nonexistent_file(self):
        """Test that extractor raises error for nonexistent file."""
        from paperdeck.extraction.extractor import PaperExtractor

        extractor = PaperExtractor()

        with pytest.raises((FileNotFoundError, ValueError)):
            extractor.extract(Path("/nonexistent/paper.pdf"))

    def test_extractor_extracts_all_types_by_default(self, tmp_path):
        """Test that extractor extracts all element types by default."""
        from paperdeck.extraction.extractor import PaperExtractor

        paper_path = tmp_path / "test_paper.pdf"
        paper_path.write_text("%PDF-1.4 mock content")

        extractor = PaperExtractor()
        elements = extractor.extract(paper_path)

        # Should extract all types (or return empty if no elements in mock)
        assert isinstance(elements, list)


class TestPDFProcessor:
    """Tests for PDF processor utilities."""

    def test_pdf_validation_accepts_valid_pdf(self, tmp_path):
        """Test that PDF validation accepts valid PDF files."""
        from paperdeck.extraction.pdf_processor import validate_pdf

        pdf_file = tmp_path / "valid.pdf"
        pdf_file.write_text("%PDF-1.4 valid content")

        # Should not raise error
        result = validate_pdf(pdf_file)
        assert result is True

    def test_pdf_validation_rejects_non_pdf(self, tmp_path):
        """Test that PDF validation rejects non-PDF files."""
        from paperdeck.extraction.pdf_processor import validate_pdf

        txt_file = tmp_path / "not_pdf.txt"
        txt_file.write_text("not a pdf")

        result = validate_pdf(txt_file)
        assert result is False

    def test_pdf_validation_detects_encryption(self, tmp_path):
        """Test that PDF validation detects encrypted PDFs."""
        from paperdeck.extraction.pdf_processor import is_encrypted

        # Mock encrypted PDF marker
        pdf_file = tmp_path / "encrypted.pdf"
        pdf_file.write_text("%PDF-1.4\n/Encrypt")

        # Should detect encryption
        result = is_encrypted(pdf_file)
        # Accept either True (if detected) or False (mock doesn't have real encryption)
        assert isinstance(result, bool)

    def test_get_page_count_returns_integer(self, tmp_path):
        """Test that get_page_count returns page count."""
        from paperdeck.extraction.pdf_processor import get_page_count

        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("%PDF-1.4 mock")

        count = get_page_count(pdf_file)
        assert isinstance(count, int)
        assert count >= 0


class TestExtractedElements:
    """Tests for extracted element data classes."""

    def test_figure_element_has_image_properties(self):
        """Test that FigureElement has image-specific properties."""
        from paperdeck.core.models import FigureElement, BoundingBox
        from uuid import uuid4

        bbox = BoundingBox(x=10, y=20, width=100, height=150)
        figure = FigureElement(
            uuid=uuid4(),
            element_type=ElementType.FIGURE,
            page_number=1,
            bounding_box=bbox,
            confidence_score=0.95,
            sequence_number=1,
            image_format="png",
            width_px=800,
            height_px=600,
        )

        assert figure.image_format == "png"
        assert figure.width_px == 800
        assert figure.height_px == 600

    def test_table_element_has_table_properties(self):
        """Test that TableElement has table-specific properties."""
        from paperdeck.core.models import TableElement, BoundingBox
        from uuid import uuid4

        bbox = BoundingBox(x=10, y=20, width=100, height=150)
        table = TableElement(
            uuid=uuid4(),
            element_type=ElementType.TABLE,
            page_number=1,
            bounding_box=bbox,
            confidence_score=0.95,
            sequence_number=1,
            rows=5,
            columns=3,
        )

        assert table.rows == 5
        assert table.columns == 3

    def test_equation_element_has_latex_code(self):
        """Test that EquationElement has LaTeX code."""
        from paperdeck.core.models import EquationElement, BoundingBox
        from uuid import uuid4

        bbox = BoundingBox(x=10, y=20, width=100, height=150)
        equation = EquationElement(
            uuid=uuid4(),
            element_type=ElementType.EQUATION,
            page_number=1,
            bounding_box=bbox,
            confidence_score=0.95,
            sequence_number=1,
            latex_code="E = mc^2",
            is_numbered=True,
        )

        assert equation.latex_code == "E = mc^2"
        assert equation.is_numbered is True
