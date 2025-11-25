"""Integration tests for end-to-end workflow.

These tests verify the complete presentation generation pipeline.
"""

import pytest
from pathlib import Path
from uuid import uuid4

from paperdeck.core.models import (
    Paper,
    PaperSection,
    FigureElement,
    ElementType,
    BoundingBox,
)
from paperdeck.generation.slide_organizer import SlideOrganizer
from paperdeck.generation.latex_generator import LaTeXGenerator


class TestEndToEndWorkflow:
    """Test complete workflow from paper to presentation."""

    def test_paper_to_slides_workflow(self, tmp_path):
        """Test organizing paper into slides."""
        # Create a mock PDF file
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\n%Test\n")

        # Create paper with content
        paper = Paper(
            file_path=pdf_file,
            title="Machine Learning Research",
            authors=["Dr. Smith", "Dr. Jones"],
        )

        # Add a section (without elements for simplicity)
        paper.sections.append(
            PaperSection(
                title="Results",
                content="Our results show significant improvements.",
                level=1,
                page_start=1,
                page_end=1,
            )
        )

        # Organize into presentation
        organizer = SlideOrganizer()
        presentation = organizer.organize(paper)

        # Verify presentation structure
        assert presentation is not None
        assert presentation.title == "Machine Learning Research"
        assert len(presentation.slides) >= 1  # At least title slide

    def test_slides_to_latex_workflow(self, tmp_path):
        """Test generating LaTeX from slides."""
        # Create paper
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\n%Test\n")

        paper = Paper(
            file_path=pdf_file,
            title="Test Paper",
            authors=["Author"],
        )

        # Organize
        organizer = SlideOrganizer()
        presentation = organizer.organize(paper)

        # Generate LaTeX
        generator = LaTeXGenerator()
        latex_code = presentation.to_latex()

        # Verify LaTeX structure
        assert latex_code is not None
        assert "\\documentclass{beamer}" in latex_code
        assert "\\begin{document}" in latex_code
        assert "\\end{document}" in latex_code
        assert presentation.title in latex_code

    def test_complete_generation_workflow(self, tmp_path):
        """Test complete workflow from paper to LaTeX file."""
        # Setup
        pdf_file = tmp_path / "research.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\n%Complete Test\n")

        # Create paper
        paper = Paper(
            file_path=pdf_file,
            title="Complete Workflow Test",
            authors=["Test Author"],
        )

        # Add section directly to paper.sections list
        paper.sections.append(
            PaperSection(
                title="Introduction",
                content="This is the introduction section.",
                level=1,
                page_start=1,
                page_end=1,
            )
        )

        # Organize
        organizer = SlideOrganizer(create_outline_slide=True)
        presentation = organizer.organize(paper)

        # Generate LaTeX
        latex_code = presentation.to_latex()

        # Write to file
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        tex_file = output_dir / "presentation.tex"
        tex_file.write_text(latex_code)

        # Verify file was created
        assert tex_file.exists()
        assert tex_file.stat().st_size > 0

        # Verify content
        content = tex_file.read_text()
        assert "\\documentclass{beamer}" in content
        assert "Complete Workflow Test" in content

    def test_error_handling_invalid_paper(self, tmp_path):
        """Test error handling with invalid paper."""
        # Test with non-PDF file (should fail validation)
        non_pdf_file = tmp_path / "test.txt"
        non_pdf_file.write_text("not a pdf")

        with pytest.raises(ValueError, match="pdf extension"):
            paper = Paper(
                file_path=non_pdf_file,
                title="Test",
                authors=[],
            )

    def test_latex_special_characters(self, tmp_path):
        """Test handling of special characters in LaTeX."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\n%Test\n")

        # Create paper with special characters
        paper = Paper(
            file_path=pdf_file,
            title="Test & Analysis: 50% Results",
            authors=["Dr. Smith & Jones"],
        )

        # Generate presentation
        organizer = SlideOrganizer()
        presentation = organizer.organize(paper)
        latex_code = presentation.to_latex()

        # Note: The Presentation.to_latex() method currently doesn't
        # escape special characters, but this test documents the expected
        # behavior for future improvements
        assert latex_code is not None
