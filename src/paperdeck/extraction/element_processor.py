"""
Element processor for saving and managing extracted PDF elements.

Handles saving figures and tables to the filesystem with proper naming
and format conversion.
"""

from pathlib import Path
from typing import Optional
import logging

from ..core.models import ExtractedElement, ElementType
from ..core.exceptions import ExtractionError

logger = logging.getLogger(__name__)


class ElementProcessor:
    """Processes and saves extracted elements to filesystem with error handling.

    This class handles the file I/O operations for extracted elements (figures, tables,
    equations) with:
    - Consistent naming conventions (figure_1.png, table_2.png, etc.)
    - Directory creation and management
    - Error handling for corrupted or invalid image data
    - Multiple format support (PNG, PDF, JPG)

    The processor ensures all elements are saved with sequential numbering and proper
    file extensions, making them easy to reference in LaTeX documents.

    Attributes:
        output_directory: Path where extracted elements are saved

    Example:
        >>> processor = ElementProcessor(Path("./output/extracted"))
        >>> # Save a figure
        >>> path = processor.save_figure(image_bytes, figure_number=1)
        >>> print(path)  # output/extracted/figure_1.png
    """

    def __init__(self, output_directory: Path):
        """Initialize element processor with output directory.

        Creates the output directory if it doesn't exist. Logs initialization success.

        Args:
            output_directory: Directory where extracted elements will be saved.
                Will be created if it doesn't exist.

        Raises:
            OSError: If directory cannot be created (permissions, disk full, etc.)
        """
        self.output_directory = output_directory
        try:
            self.output_directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"ElementProcessor initialized with output directory: {output_directory}")
        except OSError as e:
            logger.error(f"Failed to create output directory {output_directory}: {e}")
            raise

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
        """Save a figure to the output directory with error handling.

        Args:
            figure_data: Raw figure image bytes. Should be valid image data.
            figure_number: Sequential figure number for naming (1, 2, 3, ...)
            format: Output format extension (png, pdf, jpg). Default: png

        Returns:
            Path to saved figure file

        Raises:
            ExtractionError: If image data is corrupted or file cannot be written
            ValueError: If figure_data is empty

        Example:
            >>> processor = ElementProcessor(Path("./output"))
            >>> figure_path = processor.save_figure(image_bytes, 1, "png")
        """
        if not figure_data:
            raise ValueError(f"Figure {figure_number} has no image data")

        filename = f"figure_{figure_number}.{format}"
        output_path = self.output_directory / filename

        try:
            output_path.write_bytes(figure_data)
            logger.info(f"Saved figure {figure_number} to {output_path}")
            return output_path
        except (OSError, IOError) as e:
            logger.error(f"Failed to save figure {figure_number}: {e}")
            raise ExtractionError(f"Failed to save figure {figure_number} to {output_path}: {e}")

    def save_table(
        self,
        table_data: bytes,
        table_number: int,
        format: str = "png",
    ) -> Path:
        """Save a table to the output directory with error handling.

        Args:
            table_data: Raw table image bytes. Should be valid image data.
            table_number: Sequential table number for naming (1, 2, 3, ...)
            format: Output format extension (png, pdf, jpg). Default: png

        Returns:
            Path to saved table file

        Raises:
            ExtractionError: If image data is corrupted or file cannot be written
            ValueError: If table_data is empty

        Example:
            >>> processor = ElementProcessor(Path("./output"))
            >>> table_path = processor.save_table(image_bytes, 1, "png")
        """
        if not table_data:
            raise ValueError(f"Table {table_number} has no image data")

        filename = f"table_{table_number}.{format}"
        output_path = self.output_directory / filename

        try:
            output_path.write_bytes(table_data)
            logger.info(f"Saved table {table_number} to {output_path}")
            return output_path
        except (OSError, IOError) as e:
            logger.error(f"Failed to save table {table_number}: {e}")
            raise ExtractionError(f"Failed to save table {table_number} to {output_path}: {e}")
