"""
Element processor for saving and managing extracted PDF elements.

Handles saving figures and tables to the filesystem with proper naming
and format conversion.
"""

from pathlib import Path
from typing import Optional
import logging

from ..core.models import ExtractedElement, ElementType

logger = logging.getLogger(__name__)


class ElementProcessor:
    """
    Processes and saves extracted elements (figures, tables) to filesystem.
    """

    def __init__(self, output_directory: Path):
        """
        Initialize element processor.

        Args:
            output_directory: Directory to save extracted elements
        """
        self.output_directory = output_directory
        self.output_directory.mkdir(parents=True, exist_ok=True)
        logger.info(f"ElementProcessor initialized with output directory: {output_directory}")

    def save_element(
        self,
        element: ExtractedElement,
        image_data: bytes,
        format: str = "png",
    ) -> Path:
        """
        Save an extracted element to filesystem.

        Args:
            element: The extracted element with metadata
            image_data: Raw image data bytes
            format: Output format (png, pdf, jpg)

        Returns:
            Path to saved file
        """
        # Generate filename based on element type and sequence
        element_type_name = element.element_type.value.lower()
        filename = f"{element_type_name}_{element.sequence_number}.{format}"
        output_path = self.output_directory / filename

        # Save the image data
        output_path.write_bytes(image_data)
        logger.info(f"Saved {element_type_name} to {output_path}")

        return output_path

    def save_figure(
        self,
        figure_data: bytes,
        figure_number: int,
        format: str = "png",
    ) -> Path:
        """
        Save a figure to the output directory.

        Args:
            figure_data: Raw figure image bytes
            figure_number: Sequential figure number
            format: Output format (png, pdf)

        Returns:
            Path to saved figure file
        """
        filename = f"figure_{figure_number}.{format}"
        output_path = self.output_directory / filename
        output_path.write_bytes(figure_data)
        logger.info(f"Saved figure {figure_number} to {output_path}")
        return output_path

    def save_table(
        self,
        table_data: bytes,
        table_number: int,
        format: str = "png",
    ) -> Path:
        """
        Save a table to the output directory.

        Args:
            table_data: Raw table image bytes
            table_number: Sequential table number
            format: Output format (png, pdf)

        Returns:
            Path to saved table file
        """
        filename = f"table_{table_number}.{format}"
        output_path = self.output_directory / filename
        output_path.write_bytes(table_data)
        logger.info(f"Saved table {table_number} to {output_path}")
        return output_path
