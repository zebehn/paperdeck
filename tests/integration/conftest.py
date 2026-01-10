"""Fixtures for integration tests."""

import pytest
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter


@pytest.fixture
def sample_pdf_with_figures(tmp_path: Path) -> Path:
    """Create a PDF with multiple figures for integration testing.

    This fixture creates a realistic PDF with figures that can be
    extracted by docscalpel for end-to-end integration tests.

    Args:
        tmp_path: Pytest temporary directory fixture

    Returns:
        Path to the generated PDF with figures
    """
    pdf_path = tmp_path / "research_paper.pdf"
    c = canvas.Canvas(str(pdf_path), pagesize=letter)

    # Page 1 - Title and first figure
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, 750, "Machine Learning Performance Analysis")

    c.setFont("Helvetica", 12)
    c.drawString(100, 720, "Abstract: This paper presents a comprehensive analysis...")
    c.drawString(100, 700, "of machine learning model performance across various tasks.")

    # Figure 1 - Bar chart simulation
    c.setFont("Helvetica-Bold", 10)
    c.drawString(200, 600, "Figure 1: Model Accuracy Comparison")
    c.setFont("Helvetica", 9)

    # Simple bar chart representation
    c.setFillColorRGB(0.2, 0.4, 0.8)
    c.rect(150, 450, 50, 120, fill=1)
    c.setFillColorRGB(0.8, 0.4, 0.2)
    c.rect(220, 450, 50, 100, fill=1)
    c.setFillColorRGB(0.4, 0.8, 0.2)
    c.rect(290, 450, 50, 140, fill=1)

    # Axis labels
    c.setFillColorRGB(0, 0, 0)
    c.drawString(160, 430, "Model A")
    c.drawString(230, 430, "Model B")
    c.drawString(300, 430, "Model C")

    c.showPage()

    # Page 2 - Second figure
    c.setFont("Helvetica", 12)
    c.drawString(100, 750, "Methodology Section")
    c.drawString(100, 730, "Our experimental setup consists of three main components...")

    # Figure 2 - Scatter plot simulation
    c.setFont("Helvetica-Bold", 10)
    c.drawString(200, 600, "Figure 2: Training Convergence")
    c.setFont("Helvetica", 9)

    # Draw axes
    c.setStrokeColorRGB(0, 0, 0)
    c.line(150, 450, 150, 550)  # Y-axis
    c.line(150, 450, 450, 450)  # X-axis

    # Simulate data points
    import random
    random.seed(42)
    c.setFillColorRGB(0.2, 0.6, 0.8)
    for i in range(20):
        x = 150 + i * 15
        y = 450 + 5 * i + random.randint(-10, 10)
        c.circle(x, y, 3, fill=1)

    # Axis labels
    c.setFillColorRGB(0, 0, 0)
    c.drawString(140, 560, "Loss")
    c.drawString(460, 440, "Epoch")

    c.showPage()

    # Page 3 - Third figure (table-like visualization)
    c.setFont("Helvetica", 12)
    c.drawString(100, 750, "Results Section")

    # Figure 3 - Results table
    c.setFont("Helvetica-Bold", 10)
    c.drawString(220, 650, "Figure 3: Performance Metrics")
    c.setFont("Helvetica", 9)

    # Table headers
    c.setStrokeColorRGB(0, 0, 0)
    c.setFillColorRGB(0.9, 0.9, 0.9)
    c.rect(150, 600, 300, 30, fill=1, stroke=1)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(180, 610, "Metric")
    c.drawString(280, 610, "Value")
    c.drawString(380, 610, "Std Dev")

    # Table rows
    metrics = [
        ("Accuracy", "95.2%", "±1.3%"),
        ("Precision", "93.8%", "±1.5%"),
        ("Recall", "94.5%", "±1.2%"),
        ("F1-Score", "94.1%", "±1.4%")
    ]

    y_pos = 570
    for metric, value, std in metrics:
        c.rect(150, y_pos, 300, 30, fill=0, stroke=1)
        c.drawString(180, y_pos + 10, metric)
        c.drawString(280, y_pos + 10, value)
        c.drawString(380, y_pos + 10, std)
        y_pos -= 30

    c.save()
    return pdf_path


@pytest.fixture
def corrupted_pdf(tmp_path: Path) -> Path:
    """Create a corrupted PDF file for testing error handling.

    Args:
        tmp_path: Pytest temporary directory fixture

    Returns:
        Path to corrupted PDF file
    """
    pdf_path = tmp_path / "corrupted.pdf"
    # Write invalid PDF content
    pdf_path.write_text("%PDF-1.4\n%CORRUPTED\nThis is not a valid PDF")
    return pdf_path


@pytest.fixture
def empty_pdf(tmp_path: Path) -> Path:
    """Create an empty PDF with no figures for testing.

    Args:
        tmp_path: Pytest temporary directory fixture

    Returns:
        Path to empty PDF file
    """
    pdf_path = tmp_path / "empty.pdf"
    c = canvas.Canvas(str(pdf_path), pagesize=letter)
    c.drawString(100, 750, "Empty Document")
    c.drawString(100, 730, "This PDF contains no figures, tables, or equations.")
    c.save()
    return pdf_path
