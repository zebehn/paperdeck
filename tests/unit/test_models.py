"""Unit tests for core data models."""

import pytest
from pathlib import Path
from uuid import uuid4

from paperdeck.core.models import (
    BoundingBox,
    CompilationStatus,
    ElementType,
    EquationElement,
    ExtractedElement,
    FigureElement,
    Paper,
    PaperSection,
    Presentation,
    Slide,
    SlideContentType,
    TableElement,
)


class TestBoundingBox:
    """Tests for BoundingBox model."""

    def test_valid_bounding_box(self):
        """Test creating a valid bounding box."""
        bbox = BoundingBox(x=10.0, y=20.0, width=100.0, height=150.0)
        assert bbox.x == 10.0
        assert bbox.y == 20.0
        assert bbox.width == 100.0
        assert bbox.height == 150.0

    def test_negative_coordinates_raise_error(self):
        """Test that negative coordinates raise ValueError."""
        with pytest.raises(ValueError, match="non-negative"):
            BoundingBox(x=-10.0, y=20.0, width=100.0, height=150.0)

        with pytest.raises(ValueError, match="non-negative"):
            BoundingBox(x=10.0, y=-20.0, width=100.0, height=150.0)

        with pytest.raises(ValueError, match="non-negative"):
            BoundingBox(x=10.0, y=20.0, width=-100.0, height=150.0)

        with pytest.raises(ValueError, match="non-negative"):
            BoundingBox(x=10.0, y=20.0, width=100.0, height=-150.0)


class TestPaperSection:
    """Tests for PaperSection model."""

    def test_valid_paper_section(self):
        """Test creating a valid paper section."""
        section = PaperSection(
            title="Introduction",
            content="This is the introduction.",
            level=1,
            page_start=1,
            page_end=3,
        )
        assert section.title == "Introduction"
        assert section.level == 1
        assert section.page_start == 1
        assert section.page_end == 3
        assert section.elements == []

    def test_empty_title_raises_error(self):
        """Test that empty title raises ValueError."""
        with pytest.raises(ValueError, match="title must not be empty"):
            PaperSection(
                title="",
                content="Content",
                level=1,
                page_start=1,
                page_end=1,
            )

    def test_invalid_level_raises_error(self):
        """Test that level < 1 raises ValueError."""
        with pytest.raises(ValueError, match="level must be >= 1"):
            PaperSection(
                title="Section",
                content="Content",
                level=0,
                page_start=1,
                page_end=1,
            )

    def test_invalid_page_range_raises_error(self):
        """Test that page_start > page_end raises ValueError."""
        with pytest.raises(ValueError, match="page_start must be <= page_end"):
            PaperSection(
                title="Section",
                content="Content",
                level=1,
                page_start=5,
                page_end=3,
            )


class TestExtractedElement:
    """Tests for ExtractedElement model."""

    def test_valid_extracted_element(self):
        """Test creating a valid extracted element."""
        bbox = BoundingBox(x=10.0, y=20.0, width=100.0, height=150.0)
        element = ExtractedElement(
            uuid=uuid4(),
            element_type=ElementType.FIGURE,
            page_number=1,
            bounding_box=bbox,
            confidence_score=0.95,
            sequence_number=1,
        )
        assert element.element_type == ElementType.FIGURE
        assert element.page_number == 1
        assert element.confidence_score == 0.95

    def test_invalid_confidence_score_raises_error(self):
        """Test that invalid confidence score raises ValueError."""
        bbox = BoundingBox(x=10.0, y=20.0, width=100.0, height=150.0)

        with pytest.raises(ValueError, match="confidence_score must be in range"):
            ExtractedElement(
                uuid=uuid4(),
                element_type=ElementType.FIGURE,
                page_number=1,
                bounding_box=bbox,
                confidence_score=1.5,
                sequence_number=1,
            )

        with pytest.raises(ValueError, match="confidence_score must be in range"):
            ExtractedElement(
                uuid=uuid4(),
                element_type=ElementType.FIGURE,
                page_number=1,
                bounding_box=bbox,
                confidence_score=-0.1,
                sequence_number=1,
            )

    def test_invalid_page_number_raises_error(self):
        """Test that page_number < 1 raises ValueError."""
        bbox = BoundingBox(x=10.0, y=20.0, width=100.0, height=150.0)

        with pytest.raises(ValueError, match="page_number must be > 0"):
            ExtractedElement(
                uuid=uuid4(),
                element_type=ElementType.FIGURE,
                page_number=0,
                bounding_box=bbox,
                confidence_score=0.95,
                sequence_number=1,
            )


class TestFigureElement:
    """Tests for FigureElement model."""

    def test_valid_figure_element(self):
        """Test creating a valid figure element."""
        bbox = BoundingBox(x=10.0, y=20.0, width=100.0, height=150.0)
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


class TestTableElement:
    """Tests for TableElement model."""

    def test_valid_table_element(self):
        """Test creating a valid table element."""
        bbox = BoundingBox(x=10.0, y=20.0, width=100.0, height=150.0)
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


class TestEquationElement:
    """Tests for EquationElement model."""

    def test_valid_equation_element(self):
        """Test creating a valid equation element."""
        bbox = BoundingBox(x=10.0, y=20.0, width=100.0, height=150.0)
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


class TestPaper:
    """Tests for Paper model."""

    def test_valid_paper(self, tmp_path):
        """Test creating a valid paper."""
        # Create a temporary PDF file
        pdf_file = tmp_path / "test_paper.pdf"
        pdf_file.write_text("dummy pdf content")

        paper = Paper(
            file_path=pdf_file,
            title="Test Paper",
            authors=["Author 1", "Author 2"],
            abstract="This is a test paper.",
        )
        assert paper.file_path == pdf_file
        assert paper.title == "Test Paper"
        assert len(paper.authors) == 2

    def test_nonexistent_file_raises_error(self, tmp_path):
        """Test that nonexistent file raises FileNotFoundError."""
        pdf_file = tmp_path / "nonexistent.pdf"

        with pytest.raises(FileNotFoundError, match="Paper file not found"):
            Paper(file_path=pdf_file)

    def test_non_pdf_extension_raises_error(self, tmp_path):
        """Test that non-PDF extension raises ValueError."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("not a pdf")

        with pytest.raises(ValueError, match="must have .pdf extension"):
            Paper(file_path=txt_file)


class TestSlide:
    """Tests for Slide model."""

    def test_valid_slide(self):
        """Test creating a valid slide."""
        slide = Slide(
            title="Introduction",
            content_type=SlideContentType.TEXT,
            content="This is an introduction slide.",
            sequence_number=1,
        )
        assert slide.title == "Introduction"
        assert slide.content_type == SlideContentType.TEXT

    def test_empty_title_raises_error(self):
        """Test that empty title raises ValueError."""
        with pytest.raises(ValueError, match="title must not be empty"):
            Slide(
                title="",
                content_type=SlideContentType.TEXT,
                content="Content",
                sequence_number=1,
            )

    def test_to_latex_generates_frame(self):
        """Test that to_latex generates valid LaTeX frame."""
        slide = Slide(
            title="Test Slide",
            content_type=SlideContentType.TEXT,
            content="Test content",
            sequence_number=1,
        )
        latex = slide.to_latex()
        assert "\\begin{frame}{Test Slide}" in latex
        assert "Test content" in latex
        assert "\\end{frame}" in latex

    def test_add_element_to_slide(self):
        """Test adding element to slide."""
        slide = Slide(
            title="Test Slide",
            content_type=SlideContentType.TEXT,
            content="Test content",
            sequence_number=1,
        )
        element_uuid = uuid4()
        slide.add_element(element_uuid)

        assert slide.content_type == SlideContentType.MIXED
        assert isinstance(slide.content, dict)
        assert element_uuid in slide.content["elements"]


class TestPresentation:
    """Tests for Presentation model."""

    def test_valid_presentation(self, tmp_path):
        """Test creating a valid presentation."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("dummy")

        paper = Paper(file_path=pdf_file)
        slide = Slide(
            title="Title",
            content_type=SlideContentType.TEXT,
            content="Content",
            sequence_number=1,
        )

        presentation = Presentation(
            paper=paper,
            slides=[slide],
            theme="Madrid",
            title="Test Presentation",
            author="Test Author",
        )
        assert presentation.theme == "Madrid"
        assert presentation.title == "Test Presentation"
        assert len(presentation.slides) == 1

    def test_empty_slides_raises_error(self, tmp_path):
        """Test that empty slides list raises ValueError."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("dummy")
        paper = Paper(file_path=pdf_file)

        with pytest.raises(ValueError, match="must have at least one slide"):
            Presentation(
                paper=paper,
                slides=[],
                theme="Madrid",
                title="Test",
                author="Author",
            )

    def test_to_latex_generates_document(self, tmp_path):
        """Test that to_latex generates valid beamer document."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("dummy")
        paper = Paper(file_path=pdf_file)
        slide = Slide(
            title="Title",
            content_type=SlideContentType.TEXT,
            content="Content",
            sequence_number=1,
        )

        presentation = Presentation(
            paper=paper,
            slides=[slide],
            theme="Madrid",
            title="Test Presentation",
            author="Test Author",
        )
        latex = presentation.to_latex()

        assert "\\documentclass{beamer}" in latex
        assert "\\usetheme{Madrid}" in latex
        assert "\\title{Test Presentation}" in latex
        assert "\\begin{document}" in latex
        assert "\\end{document}" in latex

    def test_add_slide(self, tmp_path):
        """Test adding slide to presentation."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("dummy")
        paper = Paper(file_path=pdf_file)
        slide1 = Slide(
            title="Slide 1",
            content_type=SlideContentType.TEXT,
            content="Content 1",
            sequence_number=1,
        )

        presentation = Presentation(
            paper=paper,
            slides=[slide1],
            theme="Madrid",
            title="Test",
            author="Author",
        )

        slide2 = Slide(
            title="Slide 2",
            content_type=SlideContentType.TEXT,
            content="Content 2",
            sequence_number=2,
        )
        presentation.add_slide(slide2)

        assert len(presentation.slides) == 2
        assert presentation.slides[1].title == "Slide 2"

    def test_reorder_slides(self, tmp_path):
        """Test reordering slides in presentation."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("dummy")
        paper = Paper(file_path=pdf_file)

        slides = [
            Slide(
                title=f"Slide {i}",
                content_type=SlideContentType.TEXT,
                content=f"Content {i}",
                sequence_number=i,
            )
            for i in range(3)
        ]

        presentation = Presentation(
            paper=paper,
            slides=slides,
            theme="Madrid",
            title="Test",
            author="Author",
        )

        # Reorder: [0, 1, 2] -> [2, 0, 1]
        presentation.reorder_slides([2, 0, 1])

        assert presentation.slides[0].title == "Slide 2"
        assert presentation.slides[1].title == "Slide 0"
        assert presentation.slides[2].title == "Slide 1"
