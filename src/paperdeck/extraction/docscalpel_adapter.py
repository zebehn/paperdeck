"""
DocScalpel adapter for figure and table extraction.

This module provides an adapter pattern for integrating DocScalpel library
to extract figures and tables from PDF papers.
"""

import logging
import subprocess
import time
from pathlib import Path

from ..core.config import ExtractionConfiguration
from ..core.models import ElementType, ExtractedElement

logger = logging.getLogger(__name__)


class DocScalpelAdapter:
    """Adapter for DocScalpel library to extract figures and tables from PDFs.

    This adapter provides a clean interface to the DocScalpel library for extracting
    figures and tables from academic papers. It implements graceful degradation when
    DocScalpel is not installed and respects configuration flags for selective extraction.

    The adapter pattern isolates the DocScalpel dependency, making it easy to:
    - Test without requiring DocScalpel installation
    - Replace with alternative extraction backends
    - Handle import errors gracefully in production

    Attributes:
        config: Optional extraction configuration with flags and settings
        docscalpel_available: Whether DocScalpel library successfully loaded
        docscalpel: Reference to the docscalpel module (if available)

    Example:
        >>> from pathlib import Path
        >>> from paperdeck.core.models import ElementType
        >>> adapter = DocScalpelAdapter()
        >>> elements = adapter.extract(Path("paper.pdf"), [ElementType.FIGURE])
        >>> print(f"Found {len(elements)} figures")
    """

    def __init__(self, config: ExtractionConfiguration | None = None):
        """Initialize DocScalpel adapter with optional configuration.

        Checks if the DocScalpel CLI command is available. If not found, logs a warning
        and sets docscalpel_available to False, allowing graceful fallback.

        Args:
            config: Optional extraction configuration controlling:
                - extract_figures: Enable/disable figure extraction
                - extract_tables: Enable/disable table extraction
                - confidence_threshold: Minimum confidence for elements
                - output_directory: Where to save extracted files

        Note:
            DocScalpel can be installed with:
            pip install git+https://github.com/zebehn/docscalpel.git
        """
        self.config = config
        self.docscalpel_available = False

        # Check if docscalpel CLI is available
        try:
            result = subprocess.run(
                ['docscalpel', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                self.docscalpel_available = True
                logger.info("DocScalpel CLI available")
            else:
                logger.warning(
                    "DocScalpel CLI not found. Figure/table extraction will be skipped. "
                    "Install with: pip install git+https://github.com/zebehn/docscalpel.git"
                )
        except (subprocess.TimeoutExpired, FileNotFoundError):
            logger.warning(
                "DocScalpel CLI not found. Figure/table extraction will be skipped. "
                "Install with: pip install git+https://github.com/zebehn/docscalpel.git"
            )

    def extract(
        self,
        pdf_path: Path,
        element_types: list[ElementType] | None = None,
    ) -> list[ExtractedElement]:
        """Extract figures and/or tables from a PDF using DocScalpel.

        This method orchestrates the extraction process, respecting configuration flags
        and element type filters. It returns an empty list if DocScalpel is unavailable
        or all element types are disabled.

        The extraction process:
        1. Check DocScalpel availability (graceful fallback if not installed)
        2. Apply configuration flags (extract_figures, extract_tables)
        3. Call DocScalpel extract_elements() function
        4. Convert DocScalpel Elements to PaperDeck ExtractedElements

        Args:
            pdf_path: Path to the PDF file to process
            element_types: Optional list of element types to extract.
                Defaults to [ElementType.FIGURE, ElementType.TABLE].
                Can be filtered by configuration flags.

        Returns:
            List of ExtractedElement objects (FigureElement, TableElement).
            Returns empty list if:
            - DocScalpel is not installed
            - All element types are disabled by configuration
            - No elements found in the PDF
            - Extraction errors occur (logged but not raised)

        Example:
            >>> adapter = DocScalpelAdapter()
            >>> # Extract only figures
            >>> figures = adapter.extract(pdf_path, [ElementType.FIGURE])
            >>> # Extract both (default)
            >>> all_elements = adapter.extract(pdf_path)
        """
        if not self.docscalpel_available:
            logger.info("DocScalpel not available, skipping element extraction")
            return []

        # Default to extracting both figures and tables
        if element_types is None:
            element_types = [ElementType.FIGURE, ElementType.TABLE]

        # Respect configuration flags if provided
        if self.config:
            if not self.config.extract_figures and ElementType.FIGURE in element_types:
                element_types = [et for et in element_types if et != ElementType.FIGURE]
                logger.info("Figure extraction disabled by configuration")

            if not self.config.extract_tables and ElementType.TABLE in element_types:
                element_types = [et for et in element_types if et != ElementType.TABLE]
                logger.info("Table extraction disabled by configuration")

        # If all types filtered out, return empty list
        if not element_types:
            logger.info("No element types enabled for extraction")
            return []

        # Use DocScalpel CLI to extract elements
        start_time = time.perf_counter()

        try:
            # Build types argument for CLI
            types_str = ','.join(et.value for et in element_types)

            # Ensure output directory exists
            output_dir = self.config.output_directory if self.config else Path("extracted")
            output_dir.mkdir(parents=True, exist_ok=True)

            # Build CLI command
            cmd = [
                'docscalpel',
                str(pdf_path),
                '--types', types_str,
                '--output', str(output_dir)
            ]

            # Get configuration values (with defaults)
            confidence_threshold = self.config.confidence_threshold if self.config else 0.5
            boundary_padding = self.config.boundary_padding if self.config else 0
            max_pages = self.config.max_pages if self.config else None

            # Add confidence threshold if configured
            if self.config and self.config.confidence_threshold:
                cmd.extend(['--confidence', str(self.config.confidence_threshold)])

            # Add boundary padding if configured
            if self.config and self.config.boundary_padding > 0:
                cmd.extend(['--padding', str(self.config.boundary_padding)])

            # Add max pages if configured
            if self.config and self.config.max_pages:
                cmd.extend(['--max-pages', str(self.config.max_pages)])

            # Display extraction configuration to user
            logger.info(f"Extracting elements from {pdf_path.name} using DocScalpel CLI...")
            logger.info(f"DocScalpel Configuration:")
            logger.info(f"  • Element types: {types_str}")
            logger.info(f"  • Confidence threshold: {confidence_threshold}")
            logger.info(f"  • Boundary padding: {boundary_padding} pixels")
            if max_pages:
                logger.info(f"  • Max pages: {max_pages}")
            logger.info(f"  • Output directory: {output_dir}")
            logger.debug(f"Full command: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            # Calculate total elapsed time
            elapsed = time.perf_counter() - start_time

            # Check for errors
            if result.returncode != 0:
                logger.error(f"DocScalpel CLI extraction failed for {pdf_path.name}")
                logger.error(f"Exit code: {result.returncode}")
                if result.stderr:
                    logger.error(f"Error output: {result.stderr}")
                return []

            # Log output if available
            if result.stdout:
                logger.debug(f"DocScalpel output: {result.stdout}")

            # Load extracted elements from output directory
            extracted = self._load_extracted_elements(output_dir, element_types)

            # Log performance metrics
            logger.info(
                f"Extraction completed for {pdf_path.name}: "
                f"{len(extracted)} element(s) extracted in {elapsed:.2f}s"
            )

            return extracted

        except subprocess.TimeoutExpired:
            elapsed = time.perf_counter() - start_time
            logger.error(
                f"DocScalpel CLI timed out for {pdf_path.name} (after {elapsed:.2f}s)"
            )
            return []
        except Exception as e:
            elapsed = time.perf_counter() - start_time
            logger.error(
                f"Unexpected extraction error for {pdf_path.name} "
                f"(after {elapsed:.2f}s): {e}",
                exc_info=True
            )
            return []

    def _load_extracted_elements(
        self, output_dir: Path, element_types: list[ElementType]
    ) -> list[ExtractedElement]:
        """Load extracted elements from output directory after CLI extraction.

        Scans the output directory for extracted PDF files created by DocScalpel CLI
        and creates ExtractedElement objects from them. Since the CLI doesn't provide
        metadata like bounding boxes or page numbers, these fields use placeholder values.

        Args:
            output_dir: Directory containing extracted PDF files (figure_##.pdf, table_##.pdf)
            element_types: Types of elements that were extracted

        Returns:
            List of ExtractedElement objects loaded from files

        Note:
            CLI-extracted elements have limited metadata:
            - page_number: Set to sequence_number (actual page unknown from CLI)
            - bounding_box: Set to (0,0,0,0) (unknown)
            - confidence_score: Set to 0.0 (unknown)
            - sequence_number: Parsed from filename
        """
        from uuid import uuid4

        from ..core.models import BoundingBox, FigureElement, TableElement

        extracted = []

        # Scan for each element type
        for element_type in element_types:
            if element_type == ElementType.FIGURE:
                pattern = "figure_*.pdf"
                element_class = FigureElement
            elif element_type == ElementType.TABLE:
                pattern = "table_*.pdf"
                element_class = TableElement
            else:
                continue

            # Find all matching files
            for file_path in sorted(output_dir.glob(pattern)):
                # Parse sequence number from filename (e.g., "figure_01.pdf" -> 1)
                try:
                    # Extract number from filename like "figure_01.pdf"
                    name_parts = file_path.stem.split('_')
                    if len(name_parts) >= 2:
                        sequence_num = int(name_parts[1])
                    else:
                        logger.warning(f"Could not parse sequence number from {file_path.name}")
                        continue
                except ValueError:
                    logger.warning(f"Could not parse sequence number from {file_path.name}")
                    continue

                # Create element with minimal metadata
                # Note: CLI doesn't provide bounding box, page number, or confidence
                # We use placeholder values that indicate these are not available
                # IMPORTANT: Set confidence_score to 1.0 since DocScalpel CLI has already
                # filtered by confidence threshold, so all extracted elements passed the threshold
                element = element_class(
                    uuid=uuid4(),
                    element_type=element_type,
                    page_number=sequence_num,  # Use sequence as page (actual page unknown from CLI)
                    bounding_box=BoundingBox(x=0, y=0, width=0, height=0),  # Unknown
                    confidence_score=1.0,  # Set to 1.0 - CLI already filtered by confidence
                    sequence_number=sequence_num,
                    caption=None,
                    output_filename=file_path,
                )

                extracted.append(element)

        logger.debug(f"Loaded {len(extracted)} elements from {output_dir}")
        return extracted
