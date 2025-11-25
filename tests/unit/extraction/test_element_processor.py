"""
Unit tests for ElementProcessor.

Tests saving figures and tables to filesystem.
"""

import pytest
from pathlib import Path
from uuid import uuid4

from paperdeck.extraction.element_processor import ElementProcessor
from paperdeck.core.models import (
    ExtractedElement,
    ElementType,
    FigureElement,
    TableElement,
    BoundingBox,
)


class TestElementProcessor:
    """Tests for ElementProcessor initialization."""

    def test_initialization_creates_output_directory(self, tmp_path):
        """Test processor creates output directory if it doesn't exist."""
        output_dir = tmp_path / "extracted"
        assert not output_dir.exists()

        processor = ElementProcessor(output_dir)

        assert output_dir.exists()
        assert output_dir.is_dir()

    def test_initialization_with_existing_directory(self, tmp_path):
        """Test processor handles existing output directory."""
        output_dir = tmp_path / "extracted"
        output_dir.mkdir()

        processor = ElementProcessor(output_dir)

        assert output_dir.exists()


class TestElementProcessorSaveFigure:
    """Tests for saving figures."""

    @pytest.fixture
    def processor(self, tmp_path):
        """Create element processor with temp directory."""
        return ElementProcessor(tmp_path / "extracted")

    def test_save_figure_creates_file(self, processor):
        """Test save_figure creates a file with correct name."""
        figure_data = b"fake image data"
        figure_number = 1

        result_path = processor.save_figure(figure_data, figure_number, format="png")

        assert result_path.exists()
        assert result_path.name == "figure_1.png"
        assert result_path.read_bytes() == figure_data

    def test_save_figure_with_different_format(self, processor):
        """Test save_figure respects output format."""
        figure_data = b"fake pdf data"
        figure_number = 2

        result_path = processor.save_figure(figure_data, figure_number, format="pdf")

        assert result_path.exists()
        assert result_path.name == "figure_2.pdf"

    def test_save_multiple_figures(self, processor):
        """Test saving multiple figures."""
        for i in range(1, 4):
            figure_data = f"figure {i} data".encode()
            result_path = processor.save_figure(figure_data, i)

            assert result_path.exists()
            assert result_path.name == f"figure_{i}.png"


class TestElementProcessorSaveTable:
    """Tests for saving tables."""

    @pytest.fixture
    def processor(self, tmp_path):
        """Create element processor with temp directory."""
        return ElementProcessor(tmp_path / "extracted")

    def test_save_table_creates_file(self, processor):
        """Test save_table creates a file with correct name."""
        table_data = b"fake table image data"
        table_number = 1

        result_path = processor.save_table(table_data, table_number, format="png")

        assert result_path.exists()
        assert result_path.name == "table_1.png"
        assert result_path.read_bytes() == table_data

    def test_save_table_with_different_format(self, processor):
        """Test save_table respects output format."""
        table_data = b"fake table pdf"
        table_number = 3

        result_path = processor.save_table(table_data, table_number, format="pdf")

        assert result_path.exists()
        assert result_path.name == "table_3.pdf"


class TestElementProcessorSaveElement:
    """Tests for generic save_element method."""

    @pytest.fixture
    def processor(self, tmp_path):
        """Create element processor."""
        return ElementProcessor(tmp_path / "extracted")

    @pytest.fixture
    def figure_element(self):
        """Create a sample FigureElement."""
        return FigureElement(
            uuid=uuid4(),
            element_type=ElementType.FIGURE,
            page_number=1,
            bounding_box=BoundingBox(x=10, y=20, width=100, height=150),
            confidence_score=0.95,
            sequence_number=1,
            caption="Test Figure",
        )

    def test_save_element_for_figure(self, processor, figure_element):
        """Test save_element works for figure elements."""
        image_data = b"figure image data"

        result_path = processor.save_element(figure_element, image_data, format="png")

        assert result_path.exists()
        assert result_path.name == "figure_1.png"
        assert result_path.read_bytes() == image_data
