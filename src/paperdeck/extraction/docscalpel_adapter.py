"""
DocScalpel adapter for figure and table extraction.

This module provides an adapter pattern for integrating DocScalpel library
to extract figures and tables from PDF papers.
"""

from pathlib import Path
from typing import List, Optional
import logging

from ..core.models import ExtractedElement, ElementType
from ..core.config import ExtractionConfiguration

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

    def __init__(self, config: Optional[ExtractionConfiguration] = None):
        """Initialize DocScalpel adapter with optional configuration.

        Attempts to import the DocScalpel library. If import fails, logs a warning
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

        # Try to import DocScalpel
        try:
            import docscalpel
            self.docscalpel = docscalpel
            self.docscalpel_available = True
            logger.info("DocScalpel library loaded successfully")
        except ImportError:
            logger.warning(
                "DocScalpel not installed. Figure/table extraction will be skipped. "
                "Install with: pip install git+https://github.com/zebehn/docscalpel.git"
            )

    def extract(
        self,
        pdf_path: Path,
        element_types: Optional[List[ElementType]] = None,
    ) -> List[ExtractedElement]:
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

        # Use DocScalpel to extract all elements at once
        try:
            # Create DocScalpel configuration
            docscalpel_config = self._create_docscalpel_config(element_types)

            # Extract elements using DocScalpel
            logger.info(f"Extracting elements from {pdf_path.name} using DocScalpel...")
            result = self.docscalpel.extract_elements(str(pdf_path), docscalpel_config)

            if not result.success:
                logger.warning(f"DocScalpel extraction completed with errors: {result.errors}")

            if result.warnings:
                for warning in result.warnings:
                    logger.warning(f"DocScalpel warning: {warning}")

            # Convert DocScalpel elements to PaperDeck elements
            extracted = self._convert_elements(result.elements)

            logger.info(
                f"Successfully extracted {len(extracted)} element(s) from {pdf_path.name} "
                f"({result.figure_count} figures, {result.table_count} tables)"
            )

            return extracted

        except Exception as e:
            logger.error(f"Error during DocScalpel extraction: {e}", exc_info=True)
            return []

    def _create_docscalpel_config(self, element_types: List[ElementType]):
        """Create DocScalpel ExtractionConfig from PaperDeck element types.

        Args:
            element_types: List of PaperDeck ElementType enums to extract

        Returns:
            DocScalpel ExtractionConfig object
        """
        # Map PaperDeck ElementType to DocScalpel ElementType
        docscalpel_types = []
        for elem_type in element_types:
            if elem_type == ElementType.FIGURE:
                docscalpel_types.append(self.docscalpel.ElementType.FIGURE)
            elif elem_type == ElementType.TABLE:
                docscalpel_types.append(self.docscalpel.ElementType.TABLE)
            elif elem_type == ElementType.EQUATION:
                docscalpel_types.append(self.docscalpel.ElementType.EQUATION)

        # Create configuration with our settings
        config = self.docscalpel.ExtractionConfig(
            element_types=docscalpel_types,
            output_directory=str(self.config.output_directory) if self.config else ".",
            confidence_threshold=self.config.confidence_threshold if self.config else 0.5,
            naming_pattern="{type}_{counter}.png",  # Match our naming convention
            overwrite_existing=True,
        )

        return config

    def _convert_elements(self, docscalpel_elements: List) -> List[ExtractedElement]:
        """Convert DocScalpel Element objects to PaperDeck ExtractedElement objects.

        Args:
            docscalpel_elements: List of DocScalpel Element objects

        Returns:
            List of PaperDeck ExtractedElement objects (FigureElement, TableElement, etc.)
        """
        from ..core.models import FigureElement, TableElement, EquationElement, BoundingBox
        from uuid import uuid4

        converted = []

        for ds_elem in docscalpel_elements:
            # Map DocScalpel ElementType to PaperDeck ElementType
            if ds_elem.element_type == self.docscalpel.ElementType.FIGURE:
                paperdeck_type = ElementType.FIGURE
                element_class = FigureElement
            elif ds_elem.element_type == self.docscalpel.ElementType.TABLE:
                paperdeck_type = ElementType.TABLE
                element_class = TableElement
            elif ds_elem.element_type == self.docscalpel.ElementType.EQUATION:
                paperdeck_type = ElementType.EQUATION
                element_class = EquationElement
            else:
                logger.warning(f"Unknown element type: {ds_elem.element_type}")
                continue

            # Convert DocScalpel BoundingBox to PaperDeck BoundingBox
            bbox = BoundingBox(
                x=ds_elem.bounding_box.x,
                y=ds_elem.bounding_box.y,
                width=ds_elem.bounding_box.width,
                height=ds_elem.bounding_box.height,
            )

            # Create PaperDeck element
            element = element_class(
                uuid=uuid4(),
                element_type=paperdeck_type,
                page_number=ds_elem.page_number,
                bounding_box=bbox,
                confidence_score=ds_elem.confidence_score,
                sequence_number=ds_elem.sequence_number,
                caption=None,  # DocScalpel doesn't extract captions yet
                output_filename=Path(ds_elem.output_filename),  # Path to saved image
            )

            converted.append(element)

        return converted
