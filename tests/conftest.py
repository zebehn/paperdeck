"""Shared test fixtures and utilities."""

import pytest
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter


@pytest.fixture
def sample_pdf(tmp_path: Path) -> Path:
    """Create a minimal valid PDF for testing.

    Args:
        tmp_path: Pytest temporary directory fixture

    Returns:
        Path to the generated PDF file
    """
    pdf_path = tmp_path / "sample.pdf"
    c = canvas.Canvas(str(pdf_path), pagesize=letter)
    c.drawString(100, 750, "Test Document")
    c.drawString(100, 730, "This is a sample PDF for testing.")
    c.save()
    return pdf_path


@pytest.fixture
def sample_pdf_with_figure(tmp_path: Path) -> Path:
    """Create a PDF with a simple figure for testing.

    Args:
        tmp_path: Pytest temporary directory fixture

    Returns:
        Path to the generated PDF file with figure
    """
    pdf_path = tmp_path / "paper_with_figure.pdf"
    c = canvas.Canvas(str(pdf_path), pagesize=letter)

    # Title
    c.drawString(100, 750, "Research Paper Title")

    # Some text
    c.drawString(100, 720, "This is the introduction section.")
    c.drawString(100, 700, "Here is some academic content.")

    # Simple figure (rectangle with label)
    c.setStrokeColorRGB(0, 0, 0)
    c.setFillColorRGB(0.8, 0.8, 0.8)
    c.rect(150, 500, 300, 150, fill=1)
    c.drawString(250, 460, "Figure 1: Test Figure")

    # More text
    c.drawString(100, 420, "Discussion of the figure above.")

    c.save()
    return pdf_path


@pytest.fixture
def sample_pdf_with_multiple_elements(tmp_path: Path) -> Path:
    """Create a PDF with figures, tables, and equations for testing.

    Args:
        tmp_path: Pytest temporary directory fixture

    Returns:
        Path to the generated PDF with multiple elements
    """
    pdf_path = tmp_path / "paper_with_elements.pdf"
    c = canvas.Canvas(str(pdf_path), pagesize=letter)

    # Page 1 - Figure
    c.drawString(100, 750, "Research Paper with Multiple Elements")
    c.drawString(100, 720, "Abstract: This paper presents...")

    # Figure
    c.setStrokeColorRGB(0, 0, 0)
    c.setFillColorRGB(0.7, 0.8, 0.9)
    c.rect(150, 550, 300, 150, fill=1)
    c.drawString(250, 520, "Figure 1: Experimental Results")

    c.showPage()

    # Page 2 - Table
    c.drawString(100, 750, "Methodology Section")
    c.drawString(100, 720, "Table 1 shows the comparison...")

    # Simple table
    c.setStrokeColorRGB(0, 0, 0)
    c.grid([150, 250, 350, 450], [600, 580, 560, 540])
    c.drawString(160, 585, "Method")
    c.drawString(260, 585, "Accuracy")
    c.drawString(360, 585, "Speed")
    c.drawString(160, 565, "A")
    c.drawString(260, 565, "95%")
    c.drawString(360, 565, "Fast")
    c.drawString(160, 545, "B")
    c.drawString(260, 545, "92%")
    c.drawString(360, 545, "Slow")
    c.drawString(250, 510, "Table 1: Performance Comparison")

    c.save()
    return pdf_path


@pytest.fixture
def sample_large_pdf(tmp_path: Path, num_pages: int = 50) -> Path:
    """Create a large PDF with multiple pages for performance testing.

    Args:
        tmp_path: Pytest temporary directory fixture
        num_pages: Number of pages to generate (default 50)

    Returns:
        Path to the generated large PDF file
    """
    pdf_path = tmp_path / f"large_paper_{num_pages}pages.pdf"
    c = canvas.Canvas(str(pdf_path), pagesize=letter)

    for page_num in range(1, num_pages + 1):
        c.drawString(100, 750, f"Page {page_num} of {num_pages}")
        c.drawString(100, 720, "Lorem ipsum dolor sit amet, consectetur adipiscing elit.")
        c.drawString(100, 700, "Sed do eiusmod tempor incididunt ut labore et dolore magna.")

        # Add a simple figure every 5 pages
        if page_num % 5 == 0:
            c.setFillColorRGB(0.9, 0.9, 0.9)
            c.rect(150, 550, 300, 150, fill=1)
            c.drawString(230, 520, f"Figure {page_num // 5}: Chart")

        c.showPage()

    c.save()
    return pdf_path
