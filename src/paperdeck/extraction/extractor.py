"""PDF element extraction using DocScalpel.

This module provides the PaperExtractor class that wraps DocScalpel functionality
to extract figures, tables, and equations from PDF papers.
"""

from pathlib import Path
from typing import List, Optional
from uuid import uuid4

from ..core.models import (
    BoundingBox,
    ElementType,
    EquationElement,
    ExtractedElement,
    FigureElement,
    TableElement,
)
from ..core.exceptions import ExtractionError


class PaperExtractor:
    """Extracts figures, tables, and equations from PDF papers using DocScalpel.

    This class wraps the docscalpel library to provide a consistent interface
    for PDF element extraction.
    """

    def __init__(
        self,
        confidence_threshold: float = 0.75,
        output_directory: Optional[Path] = None,
    ):
        """Initialize the paper extractor.

        Args:
            confidence_threshold: Minimum confidence score for extracted elements (0.0-1.0)
            output_directory: Directory to save extracted element files
        """
        if not 0.0 <= confidence_threshold <= 1.0:
            raise ValueError("confidence_threshold must be in range [0.0, 1.0]")

        self.confidence_threshold = confidence_threshold
        self.output_directory = output_directory or Path("./extracted")

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

        # Default to all element types
        if element_types is None:
            element_types = [ElementType.FIGURE, ElementType.TABLE, ElementType.EQUATION]

        # Try to import docscalpel (it may not be installed)
        try:
            # Note: docscalpel might not be available in test environment
            # For now, we'll provide a mock implementation that returns empty list
            # Real implementation will use: from docscalpel import extract_elements
            pass
        except ImportError:
            # DocScalpel not installed - return empty list for testing
            return []

        # Mock implementation for testing
        # Real implementation will call docscalpel here
        extracted_elements: List[ExtractedElement] = []

        # TODO: Integrate actual docscalpel extraction
        # config = ExtractionConfig(
        #     element_types=self._map_element_types(element_types),
        #     confidence_threshold=self.confidence_threshold,
        #     output_directory=str(self.output_directory),
        # )
        # result = extract_elements(str(paper_path), config)
        # extracted_elements = self._convert_elements(result.elements)

        return extracted_elements

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
