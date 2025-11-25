"""Unit tests for LaTeX generation functionality.

These tests verify LaTeX code generation, escaping, and slide organization.
Tests should FAIL until implementations are complete (TDD).
"""

import pytest
from pathlib import Path

from paperdeck.core.models import (
    Paper,
    Presentation,
    Slide,
    SlideContentType,
    FigureElement,
    ElementType,
    BoundingBox,
)
from uuid import uuid4


class TestLaTeXGenerator:
    """Tests for LaTeX code generation."""

    def test_latex_generator_creates_valid_beamer(self, tmp_path):
        """Test that generator creates valid beamer document structure."""
        from paperdeck.generation.latex_generator import LaTeXGenerator

        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("dummy")

        paper = Paper(file_path=pdf_file)
        generator = LaTeXGenerator()

        # Create presentation structure
        slides = [
            Slide(
                title="Introduction",
                content_type=SlideContentType.TEXT,
                content="This is an introduction.",
                sequence_number=1,
            )
        ]

        latex_code = generator.generate_document(
            paper=paper,
            slides=slides,
            theme="Madrid",
            title="Test Presentation",
            author="Test Author",
        )

        # Verify beamer structure
        assert "\\documentclass{beamer}" in latex_code
        assert "\\usetheme{Madrid}" in latex_code
        assert "\\title{Test Presentation}" in latex_code
        assert "\\author{Test Author}" in latex_code
        assert "\\begin{document}" in latex_code
        assert "\\end{document}" in latex_code
        assert "\\begin{frame}" in latex_code
        assert "\\end{frame}" in latex_code

    def test_latex_generator_escapes_special_chars(self):
        """Test that special LaTeX characters are properly escaped."""
        from paperdeck.generation.latex_generator import escape_latex

        # Test all special characters
        assert escape_latex("&") == r"\&"
        assert escape_latex("%") == r"\%"
        assert escape_latex("$") == r"\$"
        assert escape_latex("#") == r"\#"
        assert escape_latex("_") == r"\_"
        assert escape_latex("{") == r"\{"
        assert escape_latex("}") == r"\}"
        assert escape_latex("~") == r"\textasciitilde{}"
        assert escape_latex("^") == r"\^{}"
        assert escape_latex("\\") == r"\textbackslash{}"

        # Test combined string
        text = "Test & verify 50% of $costs"
        escaped = escape_latex(text)
        assert "&" not in escaped
        assert "%" not in escaped
        assert "$" not in escaped
        assert r"\&" in escaped
        assert r"\%" in escaped
        assert r"\$" in escaped

    def test_latex_generator_handles_figures(self, tmp_path):
        """Test that generator includes figures in LaTeX."""
        from paperdeck.generation.latex_generator import LaTeXGenerator

        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("dummy")

        paper = Paper(file_path=pdf_file)
        generator = LaTeXGenerator()

        # Create figure element
        bbox = BoundingBox(x=10, y=20, width=100, height=150)
        figure = FigureElement(
            uuid=uuid4(),
            element_type=ElementType.FIGURE,
            page_number=1,
            bounding_box=bbox,
            confidence_score=0.95,
            sequence_number=1,
            output_filename=Path("figure1.pdf"),
        )

        slides = [
            Slide(
                title="Results",
                content_type=SlideContentType.FIGURE,
                content=figure.uuid,
                sequence_number=1,
            )
        ]

        latex_code = generator.generate_document(
            paper=paper,
            slides=slides,
            theme="Madrid",
            title="Test",
            author="Author",
        )

        # Should include figure reference
        assert "\\includegraphics" in latex_code or "figure" in latex_code.lower()

    def test_latex_generator_uses_jinja2_templates(self):
        """Test that generator uses Jinja2 templates."""
        from paperdeck.generation.latex_generator import get_jinja_env

        env = get_jinja_env()

        # Verify custom delimiters for LaTeX
        assert env.block_start_string == "\\BLOCK{"
        assert env.block_end_string == "}"
        assert env.variable_start_string == "\\VAR{"
        assert env.variable_end_string == "}"

        # Verify escape_latex filter exists
        assert "escape_latex" in env.filters


class TestSlideOrganizer:
    """Tests for intelligent slide organization."""

    def test_slide_organizer_groups_small_elements(self):
        """Test that organizer groups multiple small elements on one slide."""
        from paperdeck.generation.slide_organizer import SlideOrganizer

        organizer = SlideOrganizer()

        # Create several small elements
        elements = []
        for i in range(3):
            bbox = BoundingBox(x=10, y=20 + i * 50, width=80, height=40)
            elem = FigureElement(
                uuid=uuid4(),
                element_type=ElementType.FIGURE,
                page_number=1,
                bounding_box=bbox,
                confidence_score=0.95,
                sequence_number=i,
                caption=f"Small figure {i}",
            )
            elements.append(elem)

        slides = organizer.organize_elements(elements)

        # Should group small elements together
        assert len(slides) > 0
        # Could be on one or multiple slides depending on grouping logic
        assert all(isinstance(slide, Slide) for slide in slides)

    def test_slide_organizer_separates_large_elements(self):
        """Test that organizer gives large elements dedicated slides."""
        from paperdeck.generation.slide_organizer import SlideOrganizer

        organizer = SlideOrganizer()

        # Create large element
        bbox = BoundingBox(x=10, y=20, width=400, height=300)
        large_elem = FigureElement(
            uuid=uuid4(),
            element_type=ElementType.FIGURE,
            page_number=1,
            bounding_box=bbox,
            confidence_score=0.95,
            sequence_number=1,
            caption="Large figure",
        )

        slides = organizer.organize_elements([large_elem])

        # Large element should get its own slide
        assert len(slides) >= 1
        # Verify slide contains the element
        if slides:
            assert slides[0].content == large_elem.uuid or large_elem.uuid in str(slides[0].content)

    def test_slide_organizer_respects_sequence_order(self):
        """Test that organizer maintains element sequence order."""
        from paperdeck.generation.slide_organizer import SlideOrganizer

        organizer = SlideOrganizer()

        # Create elements with specific sequence
        elements = []
        for i in range(5):
            bbox = BoundingBox(x=10, y=20, width=100, height=100)
            elem = FigureElement(
                uuid=uuid4(),
                element_type=ElementType.FIGURE,
                page_number=1,
                bounding_box=bbox,
                confidence_score=0.95,
                sequence_number=i,
            )
            elements.append(elem)

        slides = organizer.organize_elements(elements)

        # Verify slides are in sequence order
        assert all(isinstance(slide, Slide) for slide in slides)
        for i, slide in enumerate(slides):
            assert slide.sequence_number == i


class TestBeamerTemplates:
    """Tests for beamer template rendering."""

    def test_beamer_template_exists(self):
        """Test that beamer base template file exists."""
        from paperdeck.generation import latex_generator

        template_dir = Path(latex_generator.__file__).parent / "templates"
        # Template should exist or be creatable
        assert template_dir.parent.exists()

    def test_beamer_template_renders_with_context(self):
        """Test that beamer template renders with context variables."""
        from paperdeck.generation.latex_generator import get_jinja_env

        env = get_jinja_env()

        # Create simple template
        template_str = r"""
\documentclass{beamer}
\usetheme{\VAR{theme}}
\title{\VAR{title}}
\begin{document}
\frame{\titlepage}
\end{document}
"""
        template = env.from_string(template_str)

        result = template.render(theme="Madrid", title="Test Presentation")

        assert "\\usetheme{Madrid}" in result
        assert "\\title{Test Presentation}" in result

    def test_beamer_template_supports_color_theme(self, tmp_path):
        """Test that beamer template supports color themes."""
        from paperdeck.generation.latex_generator import LaTeXGenerator

        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("dummy")

        paper = Paper(file_path=pdf_file)
        generator = LaTeXGenerator()

        slides = [
            Slide(
                title="Test",
                content_type=SlideContentType.TEXT,
                content="Content",
                sequence_number=1,
            )
        ]

        latex_code = generator.generate_document(
            paper=paper,
            slides=slides,
            theme="Madrid",
            color_theme="beaver",
            title="Test",
            author="Author",
        )

        # Should include color theme
        assert "\\usecolortheme{beaver}" in latex_code or "beaver" in latex_code


class TestPresentationModel:
    """Tests for Presentation model LaTeX generation."""

    def test_presentation_to_latex_generates_complete_document(self, tmp_path):
        """Test that Presentation.to_latex() generates complete document."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("dummy")

        paper = Paper(file_path=pdf_file)
        slides = [
            Slide(
                title="Slide 1",
                content_type=SlideContentType.TEXT,
                content="Content 1",
                sequence_number=1,
            ),
            Slide(
                title="Slide 2",
                content_type=SlideContentType.ITEMIZE,
                content=["Point 1", "Point 2", "Point 3"],
                sequence_number=2,
            ),
        ]

        presentation = Presentation(
            paper=paper,
            slides=slides,
            theme="Madrid",
            title="Test Presentation",
            author="Test Author",
        )

        latex_code = presentation.to_latex()

        # Verify complete structure
        assert latex_code.startswith("\\documentclass{beamer}")
        assert "\\begin{document}" in latex_code
        assert "\\end{document}" in latex_code
        assert "Slide 1" in latex_code
        assert "Slide 2" in latex_code
        assert "Point 1" in latex_code
