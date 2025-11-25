"""
DocScalpel adapter for figure and table extraction.

This module provides an adapter pattern for integrating DocScalpel library
to extract figures and tables from PDF papers.
"""

from pathlib import Path
from typing import List, Optional
import logging

from ..core.models import ExtractedElement, ElementType
from ..core.config import ExtractionConfig

logger = logging.getLogger(__name__)


class DocScalpelAdapter:
    """
    Adapter for DocScalpel library to extract figures and tables from PDFs.

    Provides graceful fallback if DocScalpel is not installed.
    """

    def __init__(self, config: Optional[ExtractionConfig] = None):
        """
        Initialize DocScalpel adapter.

        Args:
            config: Configuration for extraction behavior
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
        """
        Extract figures and/or tables from PDF.

        Args:
            pdf_path: Path to PDF file
            element_types: Types of elements to extract (FIGURE, TABLE)

        Returns:
            List of extracted elements
        """
        if not self.docscalpel_available:
            logger.info("DocScalpel not available, skipping element extraction")
            return []

        # Default to extracting both figures and tables
        if element_types is None:
            element_types = [ElementType.FIGURE, ElementType.TABLE]

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
