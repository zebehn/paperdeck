"""PDF element extraction using DocScalpel.

This module provides the PaperExtractor class that wraps DocScalpel functionality
to extract figures, tables, and equations from PDF papers.
"""

from pathlib import Path
from typing import List, Optional
from uuid import uuid4
import logging

from ..core.models import (
    BoundingBox,
    ElementType,
    EquationElement,
    ExtractedElement,
    FigureElement,
    TableElement,
)
from ..core.config import ExtractionConfiguration
from ..core.exceptions import ExtractionError
from .docscalpel_adapter import DocScalpelAdapter
from .element_processor import ElementProcessor

logger = logging.getLogger(__name__)


class PaperExtractor:
    """Extracts figures, tables, and equations from PDF papers using DocScalpel.

    This class wraps the docscalpel library to provide a consistent interface
    for PDF element extraction.
    """

    def __init__(
        self,
        confidence_threshold: float = 0.75,
        output_directory: Optional[Path] = None,
        extraction_config: Optional[ExtractionConfiguration] = None,
    ):
        """Initialize the paper extractor.

        Args:
            confidence_threshold: Minimum confidence score for extracted elements (0.0-1.0)
            output_directory: Directory to save extracted element files
            extraction_config: Optional extraction configuration with flags
        """
        if not 0.0 <= confidence_threshold <= 1.0:
            raise ValueError("confidence_threshold must be in range [0.0, 1.0]")

        self.confidence_threshold = confidence_threshold
        self.output_directory = output_directory or Path("./extracted")

        # Initialize DocScalpel adapter and element processor
        self.adapter = DocScalpelAdapter(config=extraction_config)
        self.processor = ElementProcessor(self.output_directory)

    def extract(
        self,
        paper_path: Path,
        element_types: Optional[List[ElementType]] = None,
    ) -> List[ExtractedElement]:
        """Extract elements from a PDF paper.

        Args:
            paper_path: Path to the PDF file
            element_types: Types of elements to extract (default: all types)

        Returns:
            List[ExtractedElement]: Extracted elements that meet confidence threshold

        Raises:
            FileNotFoundError: If paper_path does not exist
            ValueError: If paper_path is not a valid PDF
            ExtractionError: If extraction fails
        """
        # Validate input
        if not paper_path.exists():
            raise FileNotFoundError(f"Paper file not found: {paper_path}")

        if not paper_path.is_file():
            raise ValueError(f"Paper path is not a file: {paper_path}")

        if paper_path.suffix.lower() != ".pdf":
            raise ValueError(f"Paper file must be PDF: {paper_path}")

        # Default to all element types (excluding EQUATION for now - not DocScalpel supported)
        if element_types is None:
            element_types = [ElementType.FIGURE, ElementType.TABLE]

        # Use DocScalpel adapter to extract elements
        logger.info(f"Extracting elements from {paper_path.name} using DocScalpel")

        try:
            extracted_elements = self.adapter.extract(paper_path, element_types)

            # Filter by confidence threshold
            filtered_elements = [
                elem for elem in extracted_elements
                if elem.confidence_score >= self.confidence_threshold
            ]

            logger.info(
                f"Extracted {len(extracted_elements)} elements, "
                f"{len(filtered_elements)} passed confidence threshold {self.confidence_threshold}"
            )

            return filtered_elements

        except Exception as e:
            logger.error(f"Error extracting elements from {paper_path}: {e}", exc_info=True)
            # Graceful fallback - return empty list
            return []

    def _map_element_types(self, element_types: List[ElementType]) -> List:
        """Map our ElementType enum to docscalpel's ElementType.

        Args:
            element_types: Our ElementType enum values

        Returns:
            List: DocScalpel ElementType values
        """
        # TODO: Import and map docscalpel ElementType
        # from docscalpel import ElementType as DSElementType
        # return [DSElementType[et.name] for et in element_types]
        return []

    def _convert_elements(self, ds_elements: List) -> List[ExtractedElement]:
        """Convert docscalpel elements to our ExtractedElement format.

        Args:
            ds_elements: Elements from docscalpel

        Returns:
            List[ExtractedElement]: Converted elements
        """
        extracted = []

        for elem in ds_elements:
            # Filter by confidence threshold
            if elem.confidence_score < self.confidence_threshold:
                continue

            # Create bounding box
            bbox = BoundingBox(
                x=elem.bounding_box.x,
                y=elem.bounding_box.y,
                width=elem.bounding_box.width,
                height=elem.bounding_box.height,
            )

            # Determine element type and create appropriate subclass
            element_type = ElementType[elem.element_type.name]

            if element_type == ElementType.FIGURE:
                element = FigureElement(
                    uuid=uuid4(),
                    element_type=element_type,
                    page_number=elem.page_number,
                    bounding_box=bbox,
                    confidence_score=elem.confidence_score,
                    sequence_number=elem.sequence_number,
                    output_filename=Path(elem.output_filename) if elem.output_filename else None,
                    caption=getattr(elem, "caption", None),
                    image_format=getattr(elem, "image_format", ""),
                    width_px=getattr(elem, "width_px", 0),
                    height_px=getattr(elem, "height_px", 0),
                )
            elif element_type == ElementType.TABLE:
                element = TableElement(
                    uuid=uuid4(),
                    element_type=element_type,
                    page_number=elem.page_number,
                    bounding_box=bbox,
                    confidence_score=elem.confidence_score,
                    sequence_number=elem.sequence_number,
                    output_filename=Path(elem.output_filename) if elem.output_filename else None,
                    caption=getattr(elem, "caption", None),
                    rows=getattr(elem, "rows", 0),
                    columns=getattr(elem, "columns", 0),
                    data=getattr(elem, "data", None),
                )
            elif element_type == ElementType.EQUATION:
                element = EquationElement(
                    uuid=uuid4(),
                    element_type=element_type,
                    page_number=elem.page_number,
                    bounding_box=bbox,
                    confidence_score=elem.confidence_score,
                    sequence_number=elem.sequence_number,
                    output_filename=Path(elem.output_filename) if elem.output_filename else None,
                    caption=getattr(elem, "caption", None),
                    latex_code=getattr(elem, "latex_code", ""),
                    is_numbered=getattr(elem, "is_numbered", False),
                )
            else:
                # Fallback to base ExtractedElement
                element = ExtractedElement(
                    uuid=uuid4(),
                    element_type=element_type,
                    page_number=elem.page_number,
                    bounding_box=bbox,
                    confidence_score=elem.confidence_score,
                    sequence_number=elem.sequence_number,
                    output_filename=Path(elem.output_filename) if elem.output_filename else None,
                    caption=getattr(elem, "caption", None),
                )

            extracted.append(element)

        return extracted
