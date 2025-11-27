"""Core data models for PaperDeck.

This module defines the fundamental data structures used throughout the application,
including Paper, ExtractedElement, Presentation, and related entities.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4


# ============================================================================
# Enumerations
# ============================================================================


class ElementType(Enum):
    """Type of extracted element from a paper."""

    FIGURE = "figure"
    TABLE = "table"
    EQUATION = "equation"


class SlideContentType(Enum):
    """Type of content in a presentation slide."""

    TEXT = "text"
    ITEMIZE = "itemize"
    FIGURE = "figure"
    TABLE = "table"
    EQUATION = "equation"
    MIXED = "mixed"


class CompilationStatus(Enum):
    """Status of LaTeX compilation."""

    NOT_COMPILED = "not_compiled"
    COMPILING = "compiling"
    SUCCESS = "success"
    FAILED = "failed"


# ============================================================================
# Core Data Structures
# ============================================================================


@dataclass
class BoundingBox:
    """Position and size of an element on a page."""

    x: float
    y: float
    width: float
    height: float

    def __post_init__(self):
        """Validate bounding box coordinates."""
        if self.x < 0 or self.y < 0 or self.width < 0 or self.height < 0:
            raise ValueError("Bounding box coordinates must be non-negative")


@dataclass
class PaperSection:
    """Represents a logical section of a paper."""

    title: str
    content: str
    level: int
    page_start: int
    page_end: int
    elements: List[UUID] = field(default_factory=list)

    def __post_init__(self):
        """Validate section attributes."""
        if not self.title:
            raise ValueError("Section title must not be empty")
        if self.level < 1:
            raise ValueError("Section level must be >= 1")
        if self.page_start > self.page_end:
            raise ValueError("page_start must be <= page_end")


@dataclass
class ExtractedElement:
    """Base class for elements extracted from papers."""

    uuid: UUID
    element_type: ElementType
    page_number: int
    bounding_box: BoundingBox
    confidence_score: float
    sequence_number: int
    output_filename: Optional[Path] = None
    caption: Optional[str] = None

    def __post_init__(self):
        """Validate element attributes."""
        if not 0.0 <= self.confidence_score <= 1.0:
            raise ValueError("confidence_score must be in range [0.0, 1.0]")
        if self.page_number < 1:
            raise ValueError("page_number must be > 0")


@dataclass
class FigureElement(ExtractedElement):
    """Figure extracted from a paper."""

    image_format: str = ""
    width_px: int = 0
    height_px: int = 0

    def __post_init__(self):
        """Validate figure and parent attributes."""
        super().__post_init__()


@dataclass
class TableElement(ExtractedElement):
    """Table extracted from a paper."""

    rows: int = 0
    columns: int = 0
    data: Optional[List[List[str]]] = None

    def __post_init__(self):
        """Validate table and parent attributes."""
        super().__post_init__()


@dataclass
class EquationElement(ExtractedElement):
    """Equation extracted from a paper."""

    latex_code: str = ""
    is_numbered: bool = False

    def __post_init__(self):
        """Validate equation and parent attributes."""
        super().__post_init__()


@dataclass
class Paper:
    """Represents an input technical paper."""

    file_path: Path
    title: Optional[str] = None
    authors: List[str] = field(default_factory=list)
    abstract: Optional[str] = None
    sections: List[PaperSection] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # NEW: Text content integration (Feature 002)
    text_content: Optional[str] = None               # Extracted full text
    text_extraction_result: Optional[Any] = None     # TextExtractionResult instance
    token_count: Optional[int] = None                # Cached token count
    was_truncated: bool = False                      # Whether text was truncated for context

    # NEW: Element extraction integration (Feature 003)
    extracted_elements: List['ExtractedElement'] = field(default_factory=list)  # Figures, tables, equations

    def __post_init__(self):
        """Validate paper attributes."""
        if not self.file_path.exists():
            raise FileNotFoundError(f"Paper file not found: {self.file_path}")
        if not self.file_path.is_file():
            raise ValueError(f"Paper path is not a file: {self.file_path}")
        if self.file_path.suffix.lower() != ".pdf":
            raise ValueError(f"Paper file must have .pdf extension: {self.file_path}")

    @property
    def has_text_content(self) -> bool:
        """Whether paper has successfully extracted text."""
        from ..models.extraction_result import ExtractionStatus
        return (
            self.text_content is not None
            and len(self.text_content) > 0
            and self.text_extraction_result is not None
            and self.text_extraction_result.is_successful
        )

    @property
    def text_extraction_status(self) -> Any:
        """Current text extraction status."""
        from ..models.extraction_result import ExtractionStatus
        if self.text_extraction_result is None:
            return ExtractionStatus.NOT_ATTEMPTED
        return self.text_extraction_result.status


# ============================================================================
# Presentation Models
# ============================================================================


@dataclass
class Slide:
    """Represents a single slide/frame in a beamer presentation."""

    title: str
    content_type: SlideContentType
    content: Any  # Type depends on content_type
    sequence_number: int
    section_name: Optional[str] = None
    subsection_name: Optional[str] = None
    latex_code: Optional[str] = None

    def __post_init__(self):
        """Validate slide attributes."""
        if not self.title:
            raise ValueError("Slide title must not be empty")

    def to_latex(self) -> str:
        """Generate LaTeX code for this frame.

        Returns:
            str: LaTeX code for the slide
        """
        if self.latex_code:
            return self.latex_code

        # Basic frame structure
        latex = f"\\begin{{frame}}{{{self.title}}}\n"

        # Content based on type
        if self.content_type == SlideContentType.TEXT:
            latex += f"{self.content}\n"
        elif self.content_type == SlideContentType.ITEMIZE:
            latex += "\\begin{itemize}\n"
            for item in self.content:
                latex += f"  \\item {item}\n"
            latex += "\\end{itemize}\n"
        elif self.content_type == SlideContentType.FIGURE:
            # Handle figure elements
            if isinstance(self.content, list):
                for element in self.content:
                    latex += self._generate_element_latex(element)
            else:
                latex += self._generate_element_latex(self.content)
        elif self.content_type == SlideContentType.TABLE:
            # Handle table elements
            if isinstance(self.content, list):
                for element in self.content:
                    latex += self._generate_element_latex(element)
            else:
                latex += self._generate_element_latex(self.content)
        elif self.content_type == SlideContentType.EQUATION:
            # Handle equation elements
            if isinstance(self.content, list):
                for element in self.content:
                    latex += self._generate_element_latex(element)
            else:
                latex += self._generate_element_latex(self.content)

        latex += "\\end{frame}\n"
        return latex

    def _generate_element_latex(self, element: 'ExtractedElement') -> str:
        """Generate LaTeX code for an extracted element.

        Args:
            element: ExtractedElement (Figure, Table, or Equation)

        Returns:
            str: LaTeX code for the element
        """
        # Import here to avoid circular dependency
        from ..generation.latex_generator import LaTeXGenerator

        if element.element_type == ElementType.FIGURE:
            return LaTeXGenerator.generate_figure_latex(element)
        elif element.element_type == ElementType.TABLE:
            return LaTeXGenerator.generate_table_latex(element)
        elif element.element_type == ElementType.EQUATION:
            # TODO: Implement equation generation (future phase)
            return f"% Equation {element.sequence_number} (not yet implemented)\n"
        else:
            return f"% Unknown element type: {element.element_type}\n"

    def add_element(self, element_uuid: UUID) -> None:
        """Add extracted element reference to slide.

        Args:
            element_uuid: UUID of the element to add
        """
        if self.content_type == SlideContentType.MIXED:
            if not isinstance(self.content, dict):
                self.content = {"elements": []}
            if "elements" not in self.content:
                self.content["elements"] = []
            self.content["elements"].append(element_uuid)
        else:
            # Convert to mixed content type
            old_content = self.content
            self.content = {"text": old_content, "elements": [element_uuid]}
            self.content_type = SlideContentType.MIXED


@dataclass
class Presentation:
    """Represents a generated LaTeX beamer presentation."""

    paper: Paper
    slides: List[Slide]
    theme: str
    title: str
    author: str
    date: str = r"\today"
    color_theme: Optional[str] = None
    latex_code: Optional[str] = None
    compilation_status: CompilationStatus = CompilationStatus.NOT_COMPILED

    def __post_init__(self):
        """Validate presentation attributes."""
        if not self.slides:
            raise ValueError("Presentation must have at least one slide")
        if not self.title:
            raise ValueError("Presentation title must not be empty")

    def to_latex(self) -> str:
        """Generate complete LaTeX document.

        Returns:
            str: Complete LaTeX beamer document
        """
        if self.latex_code:
            return self.latex_code

        latex = f"""\\documentclass{{beamer}}
\\usetheme{{{self.theme}}}
"""
        if self.color_theme:
            latex += f"\\usecolortheme{{{self.color_theme}}}\n"

        latex += f"""
\\title{{{self.title}}}
\\author{{{self.author}}}
\\date{{{self.date}}}

\\begin{{document}}

\\frame{{\\titlepage}}

"""
        # Add slides
        for slide in self.slides:
            latex += slide.to_latex() + "\n"

        latex += "\\end{document}\n"

        self.latex_code = latex
        return latex

    def add_slide(self, slide: Slide) -> None:
        """Append slide to presentation.

        Args:
            slide: Slide to add
        """
        self.slides.append(slide)

    def reorder_slides(self, new_order: List[int]) -> None:
        """Change slide order.

        Args:
            new_order: List of slide indices in desired order
        """
        if len(new_order) != len(self.slides):
            raise ValueError("new_order must contain all slide indices")
        if set(new_order) != set(range(len(self.slides))):
            raise ValueError("new_order must contain each index exactly once")

        self.slides = [self.slides[i] for i in new_order]

        # Update sequence numbers
        for i, slide in enumerate(self.slides):
            slide.sequence_number = i

    def compile_to_pdf(self, output_path: Path) -> bool:
        """Compile LaTeX to PDF.

        Args:
            output_path: Path for output PDF

        Returns:
            bool: True if compilation successful

        Note:
            This is a placeholder. Actual implementation will call pdflatex.
        """
        self.compilation_status = CompilationStatus.COMPILING
        # TODO: Implement actual LaTeX compilation
        self.compilation_status = CompilationStatus.NOT_COMPILED
        return False
