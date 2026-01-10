"""
Element loader for reading pre-extracted PDF elements from filesystem.

Complements ElementProcessor by providing the inverse operation: loading
elements from disk rather than saving them.
"""

import logging
import re
from pathlib import Path
from uuid import uuid4

from ..core.models import (
    BoundingBox,
    ElementType,
    ExtractedElement,
    FigureElement,
    TableElement,
)

logger = logging.getLogger(__name__)


class ElementLoader:
    """Loads pre-extracted elements from filesystem.

    This class reads existing extracted elements (figures, tables) from
    a directory and reconstructs ExtractedElement objects for use in
    presentation generation.

    Expected directory structure:
        extracted/
            figure_01.pdf
            figure_02.png
            table_01.pdf
            table_02.jpg

    Attributes:
        input_directory: Path containing pre-extracted elements
    """

    def __init__(self, input_directory: Path):
        """Initialize element loader.

        Args:
            input_directory: Directory containing extracted element files

        Raises:
            FileNotFoundError: If input_directory doesn't exist
            ValueError: If input_directory is not a directory
        """
        if not input_directory.exists():
            raise FileNotFoundError(f"Input directory not found: {input_directory}")
        if not input_directory.is_dir():
            raise ValueError(f"Input path is not a directory: {input_directory}")

        self.input_directory = input_directory
        logger.info(f"ElementLoader initialized with input directory: {input_directory}")

    def load_elements(
        self,
        element_types: list[ElementType] | None = None,
    ) -> list[ExtractedElement]:
        """Load pre-extracted elements from filesystem.

        Scans the input directory for files matching naming patterns:
        - figure_N.{pdf,png,jpg,jpeg} -> FigureElement
        - table_N.{pdf,png,jpg,jpeg} -> TableElement

        Args:
            element_types: Types of elements to load (default: all types)

        Returns:
            List[ExtractedElement]: Loaded elements sorted by sequence number

        Raises:
            ExtractionError: If loading fails
        """
        if element_types is None:
            element_types = [ElementType.FIGURE, ElementType.TABLE]

        # Warn about invalid files before loading
        self._warn_about_invalid_files()

        elements = []

        # Load figures
        if ElementType.FIGURE in element_types:
            elements.extend(self._load_figures())

        # Load tables
        if ElementType.TABLE in element_types:
            elements.extend(self._load_tables())

        # Sort by sequence number
        elements.sort(key=lambda e: e.sequence_number)

        # Check for gaps in numbering
        self._warn_about_gaps(elements)

        logger.info(
            f"Loaded {len(elements)} pre-extracted element(s) from {self.input_directory}"
        )

        return elements

    def validate_directory(self) -> tuple[bool, list[str]]:
        """Validate that directory contains valid element files.

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # Check for at least one valid element file
        valid_files = []
        for pattern in [
            r"^figure_\d+\.(pdf|png|jpg|jpeg)$",
            r"^table_\d+\.(pdf|png|jpg|jpeg)$",
        ]:
            regex = re.compile(pattern, re.IGNORECASE)
            valid_files.extend(
                [f for f in self.input_directory.iterdir() if regex.match(f.name)]
            )

        if not valid_files:
            errors.append(
                f"No valid element files found in {self.input_directory}. "
                "Expected files like figure_01.pdf, table_01.png, etc."
            )

        return (len(errors) == 0, errors)

    def _load_figures(self) -> list[FigureElement]:
        """Load figure elements from directory.

        Returns:
            List of FigureElement objects
        """
        figures = []
        pattern = re.compile(r"^figure_(\d+)\.(pdf|png|jpg|jpeg)$", re.IGNORECASE)

        for file_path in self.input_directory.iterdir():
            if not file_path.is_file():
                continue

            match = pattern.match(file_path.name)
            if match:
                sequence_num = int(match.group(1))

                figure = FigureElement(
                    uuid=uuid4(),
                    element_type=ElementType.FIGURE,
                    page_number=1,  # Unknown from filename alone
                    bounding_box=BoundingBox(x=0, y=0, width=0, height=0),  # Unknown
                    confidence_score=1.0,  # Assume pre-extracted elements are valid
                    sequence_number=sequence_num,
                    output_filename=file_path,
                    caption=None,  # Could load from metadata.json if available
                )

                figures.append(figure)
                logger.debug(f"Loaded figure: {file_path.name}")

        logger.info(f"Loaded {len(figures)} figure(s)")
        return figures

    def _load_tables(self) -> list[TableElement]:
        """Load table elements from directory.

        Returns:
            List of TableElement objects
        """
        tables = []
        pattern = re.compile(r"^table_(\d+)\.(pdf|png|jpg|jpeg)$", re.IGNORECASE)

        for file_path in self.input_directory.iterdir():
            if not file_path.is_file():
                continue

            match = pattern.match(file_path.name)
            if match:
                sequence_num = int(match.group(1))

                table = TableElement(
                    uuid=uuid4(),
                    element_type=ElementType.TABLE,
                    page_number=1,  # Unknown from filename alone
                    bounding_box=BoundingBox(x=0, y=0, width=0, height=0),  # Unknown
                    confidence_score=1.0,  # Assume pre-extracted elements are valid
                    sequence_number=sequence_num,
                    output_filename=file_path,
                    caption=None,  # Could load from metadata.json if available
                )

                tables.append(table)
                logger.debug(f"Loaded table: {file_path.name}")

        logger.info(f"Loaded {len(tables)} table(s)")
        return tables

    def _warn_about_invalid_files(self) -> None:
        """Scan directory and warn about files with invalid names or formats.

        This helps users identify files that don't match expected patterns.
        """
        valid_pattern = re.compile(
            r"^(figure|table)_(\d+)\.(pdf|png|jpg|jpeg)$", re.IGNORECASE
        )

        invalid_files = []
        for file_path in self.input_directory.iterdir():
            if not file_path.is_file():
                continue

            # Skip hidden files and system files
            if file_path.name.startswith('.'):
                continue

            # Check if file matches valid pattern
            if not valid_pattern.match(file_path.name):
                invalid_files.append(file_path.name)

        if invalid_files:
            files_str = ', '.join(invalid_files[:5])
            extra = f" and {len(invalid_files) - 5} more" if len(invalid_files) > 5 else ""
            logger.warning(
                f"Found {len(invalid_files)} file(s) with invalid naming pattern "
                f"in {self.input_directory}. Files will be ignored. "
                f"Expected pattern: figure_##.pdf, table_##.png, etc. "
                f"Invalid files: {files_str}{extra}"
            )

    def _warn_about_gaps(self, elements: list[ExtractedElement]) -> None:
        """Check for gaps in sequence numbering and warn user.

        Args:
            elements: List of loaded elements (should be sorted by sequence_number)
        """
        if not elements:
            return

        # Group elements by type
        figures = [e for e in elements if e.element_type == ElementType.FIGURE]
        tables = [e for e in elements if e.element_type == ElementType.TABLE]

        # Check figures for gaps
        if figures:
            figure_nums = sorted([f.sequence_number for f in figures])
            expected_range = range(figure_nums[0], figure_nums[-1] + 1)
            missing_nums = set(expected_range) - set(figure_nums)

            if missing_nums:
                missing_str = ', '.join(str(n) for n in sorted(missing_nums))
                expected = ', '.join(f'figure_{n:02d}.*' for n in sorted(missing_nums))
                logger.warning(
                    f"Gap detected in figure numbering. Missing sequence numbers: {missing_str}. "
                    f"Expected files: {expected}"
                )

        # Check tables for gaps
        if tables:
            table_nums = sorted([t.sequence_number for t in tables])
            expected_range = range(table_nums[0], table_nums[-1] + 1)
            missing_nums = set(expected_range) - set(table_nums)

            if missing_nums:
                missing_str = ', '.join(str(n) for n in sorted(missing_nums))
                logger.warning(
                    f"Gap detected in table numbering. Missing sequence numbers: {missing_str}. "
                    f"Expected files: {', '.join(f'table_{n:02d}.*' for n in sorted(missing_nums))}"
                )
