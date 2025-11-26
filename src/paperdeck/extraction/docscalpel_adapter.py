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
        3. Call specialized detection methods (_detect_figures, _detect_tables)
        4. Return combined list of extracted elements

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

        extracted = []

        # Extract figures
        if ElementType.FIGURE in element_types:
            figures = self._detect_figures(pdf_path)
            extracted.extend(figures)
            logger.info(f"Extracted {len(figures)} figure(s) from {pdf_path.name}")

        # Extract tables
        if ElementType.TABLE in element_types:
            tables = self._detect_tables(pdf_path)
            extracted.extend(tables)
            logger.info(f"Extracted {len(tables)} table(s) from {pdf_path.name}")

        return extracted

    def _detect_figures(self, pdf_path: Path) -> List[ExtractedElement]:
        """
        Detect and extract figures from PDF using DocScalpel.

        Args:
            pdf_path: Path to PDF file

        Returns:
            List of FigureElement objects
        """
        from ..core.models import FigureElement
        from uuid import uuid4

        figures = []

        try:
            # TODO: Replace with actual DocScalpel API calls
            # For now, return empty list (DocScalpel integration pending)
            # Expected flow:
            # 1. doc = self.docscalpel.Document(str(pdf_path))
            # 2. detected_figures = doc.detect_figures()
            # 3. for each figure: extract metadata and create FigureElement

            logger.debug(f"Figure detection called for {pdf_path.name}")

        except Exception as e:
            logger.error(f"Error detecting figures: {e}", exc_info=True)

        return figures

    def _extract_figure_metadata(self, doc_figure) -> dict:
        """
        Extract metadata from a DocScalpel figure object.

        Args:
            doc_figure: DocScalpel figure object

        Returns:
            Dictionary with figure metadata (caption, bbox, confidence)
        """
        metadata = {
            "caption": None,
            "page_number": 1,
            "bounding_box": {"x": 0, "y": 0, "width": 100, "height": 100},
            "confidence_score": 0.0,
        }

        try:
            # TODO: Replace with actual DocScalpel API
            # metadata["caption"] = doc_figure.caption
            # metadata["page_number"] = doc_figure.page
            # metadata["bounding_box"] = doc_figure.bbox
            # metadata["confidence_score"] = doc_figure.confidence
            pass

        except Exception as e:
            logger.warning(f"Error extracting figure metadata: {e}")

        return metadata

    def _detect_tables(self, pdf_path: Path) -> List[ExtractedElement]:
        """
        Detect and extract tables from PDF using DocScalpel.

        Args:
            pdf_path: Path to PDF file

        Returns:
            List of TableElement objects
        """
        from ..core.models import TableElement
        from uuid import uuid4

        tables = []

        try:
            # TODO: Replace with actual DocScalpel API calls
            logger.debug(f"Table detection called for {pdf_path.name}")

        except Exception as e:
            logger.error(f"Error detecting tables: {e}", exc_info=True)

        return tables
