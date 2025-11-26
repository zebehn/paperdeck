"""
Unit tests for figure and table LaTeX generation.

Tests the LaTeX code generation for figure and table elements in slides.
"""

import pytest
from pathlib import Path
from uuid import uuid4

from paperdeck.core.models import (
    BoundingBox,
    ElementType,
    FigureElement,
    TableElement,
    Paper,
    Slide,
    SlideContentType,
)
from paperdeck.generation.latex_generator import LaTeXGenerator


class TestFigureLatexGeneration:
    """Tests for figure LaTeX generation."""

    @pytest.fixture
    def sample_figure(self):
        """Create a sample figure element."""
        return FigureElement(
            uuid=uuid4(),
            element_type=ElementType.FIGURE,
            page_number=1,
            bounding_box=BoundingBox(x=10, y=20, width=300, height=200),
            confidence_score=0.95,
            sequence_number=1,
            output_filename=Path("extracted/figure_1.png"),
            caption="Sample Figure Caption",
            image_format="png",
            width_px=300,
            height_px=200,
        )

    def test_generate_figure_latex_with_caption(self, sample_figure):
        """Test generating LaTeX for figure with caption."""
        latex = LaTeXGenerator.generate_figure_latex(sample_figure)

        assert "\\begin{figure}" in latex
        assert "\\includegraphics" in latex
        assert "extracted/figure_1.png" in latex
        assert "\\caption{Sample Figure Caption}" in latex
        assert "\\end{figure}" in latex

    def test_generate_figure_latex_without_caption(self):
        """Test generating LaTeX for figure without caption."""
        figure = FigureElement(
            uuid=uuid4(),
            element_type=ElementType.FIGURE,
            page_number=1,
            bounding_box=BoundingBox(x=10, y=20, width=300, height=200),
            confidence_score=0.95,
            sequence_number=2,
            output_filename=Path("extracted/figure_2.png"),
            caption=None,
        )

        latex = LaTeXGenerator.generate_figure_latex(figure)

        assert "\\begin{figure}" in latex
        assert "\\includegraphics" in latex
        assert "\\caption" not in latex

    def test_generate_figure_latex_without_filename(self):
        """Test generating LaTeX for figure without output file."""
        figure = FigureElement(
            uuid=uuid4(),
            element_type=ElementType.FIGURE,
            page_number=1,
            bounding_box=BoundingBox(x=10, y=20, width=300, height=200),
            confidence_score=0.95,
            sequence_number=3,
            output_filename=None,
        )

        latex = LaTeXGenerator.generate_figure_latex(figure)

        # Should return placeholder comment
        assert "Figure 3" in latex
        assert "no image available" in latex

    def test_generate_figure_latex_custom_width(self, sample_figure):
        """Test generating LaTeX with custom width."""
        latex = LaTeXGenerator.generate_figure_latex(
            sample_figure, width="0.5\\textwidth"
        )

        assert "width=0.5\\textwidth" in latex

    def test_format_graphics_path_with_forward_slashes(self):
        """Test path formatting uses forward slashes."""
        path = Path("extracted/figures/figure_1.png")
        formatted = LaTeXGenerator._format_graphics_path(path)

        assert "\\" not in formatted or "/" in formatted
        assert "figure_1.png" in formatted

    def test_format_graphics_path_relative_to_output_dir(self):
        """Test path becomes relative to output directory."""
        figure_path = Path("/tmp/output/extracted/figure_1.png")
        output_dir = Path("/tmp/output")

        formatted = LaTeXGenerator._format_graphics_path(figure_path, output_dir)

        assert formatted == "extracted/figure_1.png"


class TestSlideWithFigures:
    """Tests for Slide.to_latex() with figure content."""

    @pytest.fixture
    def figure_slide(self):
        """Create a slide with figure content."""
        figure = FigureElement(
            uuid=uuid4(),
            element_type=ElementType.FIGURE,
            page_number=1,
            bounding_box=BoundingBox(x=10, y=20, width=300, height=200),
            confidence_score=0.95,
            sequence_number=1,
            output_filename=Path("extracted/figure_1.png"),
            caption="Test Figure",
        )

        return Slide(
            title="Figure Slide",
            content_type=SlideContentType.FIGURE,
            content=[figure],
            sequence_number=1,
        )

    def test_slide_to_latex_generates_figure_content(self, figure_slide):
        """Test Slide.to_latex() generates figure content."""
        latex = figure_slide.to_latex()

        assert "\\begin{frame}{Figure Slide}" in latex
        assert "\\begin{figure}" in latex
        assert "\\includegraphics" in latex
        assert "extracted/figure_1.png" in latex
        assert "\\caption{Test Figure}" in latex
        assert "\\end{frame}" in latex

    def test_slide_to_latex_with_multiple_figures(self):
        """Test slide with multiple figures."""
        figures = [
            FigureElement(
                uuid=uuid4(),
                element_type=ElementType.FIGURE,
                page_number=1,
                bounding_box=BoundingBox(x=10, y=20, width=300, height=200),
                confidence_score=0.95,
                sequence_number=i,
                output_filename=Path(f"extracted/figure_{i}.png"),
                caption=f"Figure {i}",
            )
            for i in range(1, 3)
        ]

        slide = Slide(
            title="Multiple Figures",
            content_type=SlideContentType.FIGURE,
            content=figures,
            sequence_number=1,
        )

        latex = slide.to_latex()

        assert latex.count("\\begin{figure}") == 2
        assert "figure_1.png" in latex
        assert "figure_2.png" in latex


class TestTableLatexGeneration:
    """Tests for table LaTeX generation."""

    @pytest.fixture
    def sample_table(self):
        """Create a sample table element."""
        return TableElement(
            uuid=uuid4(),
            element_type=ElementType.TABLE,
            page_number=1,
            bounding_box=BoundingBox(x=10, y=20, width=400, height=300),
            confidence_score=0.92,
            sequence_number=1,
            output_filename=Path("extracted/table_1.png"),
            caption="Sample Table Caption",
            rows=5,
            columns=3,
        )

    def test_generate_table_latex_with_caption(self, sample_table):
        """Test generating LaTeX for table with caption."""
        latex = LaTeXGenerator.generate_table_latex(sample_table)

        assert "\\begin{table}" in latex
        assert "\\includegraphics" in latex
        assert "extracted/table_1.png" in latex
        assert "\\caption{Sample Table Caption}" in latex
        assert "\\end{table}" in latex

    def test_generate_table_latex_without_caption(self):
        """Test generating LaTeX for table without caption."""
        table = TableElement(
            uuid=uuid4(),
            element_type=ElementType.TABLE,
            page_number=1,
            bounding_box=BoundingBox(x=10, y=20, width=400, height=300),
            confidence_score=0.92,
            sequence_number=2,
            output_filename=Path("extracted/table_2.png"),
            caption=None,
        )

        latex = LaTeXGenerator.generate_table_latex(table)

        assert "\\begin{table}" in latex
        assert "\\includegraphics" in latex
        assert "\\caption" not in latex

    def test_generate_table_latex_without_filename(self):
        """Test generating LaTeX for table without output file."""
        table = TableElement(
            uuid=uuid4(),
            element_type=ElementType.TABLE,
            page_number=1,
            bounding_box=BoundingBox(x=10, y=20, width=400, height=300),
            confidence_score=0.92,
            sequence_number=3,
            output_filename=None,
        )

        latex = LaTeXGenerator.generate_table_latex(table)

        # Should return placeholder comment
        assert "Table 3" in latex
        assert "no image available" in latex

    def test_generate_table_latex_custom_width(self, sample_table):
        """Test generating LaTeX with custom width."""
        latex = LaTeXGenerator.generate_table_latex(
            sample_table, width="0.7\\textwidth"
        )

        assert "width=0.7\\textwidth" in latex

    def test_generate_table_latex_default_width(self, sample_table):
        """Test table uses wider default width than figures."""
        latex = LaTeXGenerator.generate_table_latex(sample_table)

        # Tables default to 0.9\textwidth (wider than figures' 0.8)
        assert "width=0.9\\textwidth" in latex


class TestSlideWithTables:
    """Tests for Slide.to_latex() with table content."""

    @pytest.fixture
    def table_slide(self):
        """Create a slide with table content."""
        table = TableElement(
            uuid=uuid4(),
            element_type=ElementType.TABLE,
            page_number=1,
            bounding_box=BoundingBox(x=10, y=20, width=400, height=300),
            confidence_score=0.92,
            sequence_number=1,
            output_filename=Path("extracted/table_1.png"),
            caption="Test Table",
            rows=5,
            columns=3,
        )

        return Slide(
            title="Table Slide",
            content_type=SlideContentType.TABLE,
            content=[table],
            sequence_number=1,
        )

    def test_slide_to_latex_generates_table_content(self, table_slide):
        """Test Slide.to_latex() generates table content."""
        latex = table_slide.to_latex()

        assert "\\begin{frame}{Table Slide}" in latex
        assert "\\begin{table}" in latex
        assert "\\includegraphics" in latex
        assert "extracted/table_1.png" in latex
        assert "\\caption{Test Table}" in latex
        assert "\\end{frame}" in latex

    def test_slide_to_latex_with_multiple_tables(self):
        """Test slide with multiple tables."""
        tables = [
            TableElement(
                uuid=uuid4(),
                element_type=ElementType.TABLE,
                page_number=1,
                bounding_box=BoundingBox(x=10, y=20, width=400, height=300),
                confidence_score=0.92,
                sequence_number=i,
                output_filename=Path(f"extracted/table_{i}.png"),
                caption=f"Table {i}",
            )
            for i in range(1, 3)
        ]

        slide = Slide(
            title="Multiple Tables",
            content_type=SlideContentType.TABLE,
            content=tables,
            sequence_number=1,
        )

        latex = slide.to_latex()

        assert latex.count("\\begin{table}") == 2
        assert "table_1.png" in latex
        assert "table_2.png" in latex


class TestMixedElementSlides:
    """Tests for slides with both figures and tables."""

    def test_presentation_with_figures_and_tables(self):
        """Test that both figures and tables can be in same presentation."""
        figure = FigureElement(
            uuid=uuid4(),
            element_type=ElementType.FIGURE,
            page_number=1,
            bounding_box=BoundingBox(x=10, y=20, width=300, height=200),
            confidence_score=0.95,
            sequence_number=1,
            output_filename=Path("extracted/figure_1.png"),
            caption="Test Figure",
        )

        table = TableElement(
            uuid=uuid4(),
            element_type=ElementType.TABLE,
            page_number=2,
            bounding_box=BoundingBox(x=10, y=20, width=400, height=300),
            confidence_score=0.92,
            sequence_number=1,
            output_filename=Path("extracted/table_1.png"),
            caption="Test Table",
        )

        figure_slide = Slide(
            title="Figure Slide",
            content_type=SlideContentType.FIGURE,
            content=[figure],
            sequence_number=1,
        )

        table_slide = Slide(
            title="Table Slide",
            content_type=SlideContentType.TABLE,
            content=[table],
            sequence_number=2,
        )

        figure_latex = figure_slide.to_latex()
        table_latex = table_slide.to_latex()

        # Verify both generate correct LaTeX
        assert "\\begin{figure}" in figure_latex
        assert "figure_1.png" in figure_latex
        assert "\\begin{table}" in table_latex
        assert "table_1.png" in table_latex
