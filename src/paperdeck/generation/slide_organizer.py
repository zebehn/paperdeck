"""Slide organization and content grouping logic.

This module provides intelligent organization of extracted elements and paper
sections into presentation slides.
"""

from typing import List, Optional

from ..core.models import (
    ElementType,
    ExtractedElement,
    Paper,
    PaperSection,
    Presentation,
    Slide,
    SlideContentType,
)


class SlideOrganizer:
    """Organize paper content into presentation slides."""

    def __init__(
        self,
        max_elements_per_slide: int = 2,
        create_title_slide: bool = True,
        create_outline_slide: bool = True,
        large_element_threshold: int = 200,  # width or height in pixels
    ):
        """Initialize slide organizer.

        Args:
            max_elements_per_slide: Maximum elements (figures/tables) per slide
            create_title_slide: Whether to create a title slide
            create_outline_slide: Whether to create an outline/agenda slide
            large_element_threshold: Threshold for considering an element "large"
        """
        self.max_elements_per_slide = max_elements_per_slide
        self.create_title_slide = create_title_slide
        self.create_outline_slide = create_outline_slide
        self.large_element_threshold = large_element_threshold

    def organize(self, paper: Paper) -> Presentation:
        """Organize paper into presentation structure.

        Args:
            paper: Paper model with sections and elements

        Returns:
            Presentation: Organized presentation with slides
        """
        slides = []

        # Create title slide
        if self.create_title_slide:
            title_slide = self._create_title_slide(paper)
            slides.append(title_slide)

        # Create outline slide
        if self.create_outline_slide:
            outline_slide = self._create_outline_slide(paper)
            slides.append(outline_slide)

        # Create content slides from sections
        for section in paper.sections:
            section_slides = self._create_section_slides(section)
            slides.extend(section_slides)

        # Create presentation
        presentation = Presentation(
            paper=paper,
            title=paper.title or "Untitled",
            author=paper.authors[0] if paper.authors else "Unknown",
            date="",  # Date can be set later or extracted from metadata
            theme="Madrid",  # Default theme
            slides=slides,
        )

        return presentation

    def organize_elements(
        self, elements: List[ExtractedElement], title_prefix: str = "Content"
    ) -> List[Slide]:
        """Organize extracted elements into slides.

        This method intelligently groups elements based on their size and type.
        Large elements get their own slides, while small elements can be grouped.

        Args:
            elements: List of extracted elements to organize
            title_prefix: Prefix for slide titles

        Returns:
            List[Slide]: Organized slides containing the elements
        """
        if not elements:
            return []

        slides = []

        # Separate large and small elements
        large_elements = []
        small_elements = []

        for element in elements:
            bbox = element.bounding_box
            is_large = (
                bbox.width >= self.large_element_threshold
                or bbox.height >= self.large_element_threshold
            )

            if is_large:
                large_elements.append(element)
            else:
                small_elements.append(element)

        # Large elements get their own slides
        for idx, element in enumerate(large_elements):
            content_type = self._element_type_to_slide_type(element.element_type)
            slide = Slide(
                title=element.caption or f"{title_prefix} - {element.element_type.value.title()}",
                content_type=content_type,
                content=[element],  # Use content instead of elements
                sequence_number=len(slides) + idx,
            )
            slides.append(slide)

        # Small elements are grouped
        for i in range(0, len(small_elements), self.max_elements_per_slide):
            batch = small_elements[i : i + self.max_elements_per_slide]

            # Determine content type from first element
            content_type = self._element_type_to_slide_type(batch[0].element_type)

            # Create title
            if len(batch) == 1:
                title = batch[0].caption or f"{title_prefix} - {batch[0].element_type.value.title()}"
            else:
                title = f"{title_prefix} - {batch[0].element_type.value.title()}s"

            slide = Slide(
                title=title,
                content_type=content_type,
                content=batch,  # Use content instead of elements
                sequence_number=len(slides) + len(large_elements) + i // self.max_elements_per_slide,
            )
            slides.append(slide)

        return slides

    def _element_type_to_slide_type(self, element_type: ElementType) -> SlideContentType:
        """Map ElementType to SlideContentType.

        Args:
            element_type: Type of extracted element

        Returns:
            SlideContentType: Corresponding slide content type
        """
        if element_type == ElementType.FIGURE:
            return SlideContentType.FIGURE
        elif element_type == ElementType.TABLE:
            return SlideContentType.TABLE
        elif element_type == ElementType.EQUATION:
            return SlideContentType.EQUATION
        else:
            return SlideContentType.TEXT

    def _create_title_slide(self, paper: Paper) -> Slide:
        """Create title slide from paper metadata.

        Args:
            paper: Paper model

        Returns:
            Slide: Title slide
        """
        # Format authors for display
        authors = ", ".join(paper.authors) if paper.authors else "Unknown Author"

        return Slide(
            title=paper.title,
            content_type=SlideContentType.TEXT,
            content=f"Authors: {authors}",
            sequence_number=0,
        )

    def _create_outline_slide(self, paper: Paper) -> Slide:
        """Create outline/agenda slide from paper sections.

        Args:
            paper: Paper model

        Returns:
            Slide: Outline slide
        """
        # Build outline from section titles
        outline_items = []
        for section in paper.sections:
            if section.title:
                outline_items.append(section.title)

        return Slide(
            title="Outline",
            content_type=SlideContentType.ITEMIZE,
            content=outline_items,
            sequence_number=1,
        )

    def _create_section_slides(self, section: PaperSection) -> List[Slide]:
        """Create slides for a paper section.

        Args:
            section: Paper section with content and elements

        Returns:
            List[Slide]: Slides for this section
        """
        slides = []

        # Create section header slide
        if section.title:
            header_slide = Slide(
                title=section.title,
                content_type=SlideContentType.TEXT,
                content=section.content[:500] if section.content else "",
                sequence_number=len(slides),
            )
            slides.append(header_slide)

        # Group elements by type and create slides
        figures = [e for e in section.elements if e.element_type == ElementType.FIGURE]
        tables = [e for e in section.elements if e.element_type == ElementType.TABLE]
        equations = [e for e in section.elements if e.element_type == ElementType.EQUATION]

        # Create figure slides
        figure_slides = self._create_element_slides(
            figures, SlideContentType.FIGURE, section.title or "Figure"
        )
        slides.extend(figure_slides)

        # Create table slides
        table_slides = self._create_element_slides(
            tables, SlideContentType.TABLE, section.title or "Table"
        )
        slides.extend(table_slides)

        # Create equation slides
        equation_slides = self._create_element_slides(
            equations, SlideContentType.EQUATION, section.title or "Equation"
        )
        slides.extend(equation_slides)

        # If section has content but no elements, create text slide
        if not section.elements and section.content:
            text_slide = Slide(
                title=section.title or "Content",
                content_type=SlideContentType.TEXT,
                content=section.content[:1000],  # Limit content length
                sequence_number=len(slides),
            )
            slides.append(text_slide)

        return slides

    def _create_element_slides(
        self,
        elements: List[ExtractedElement],
        content_type: SlideContentType,
        section_title: str,
    ) -> List[Slide]:
        """Create slides from list of elements.

        Args:
            elements: List of extracted elements
            content_type: Type of content for slides
            section_title: Title of parent section

        Returns:
            List[Slide]: Slides containing elements
        """
        slides = []

        # Group elements into slides (respecting max_elements_per_slide)
        for i in range(0, len(elements), self.max_elements_per_slide):
            batch = elements[i : i + self.max_elements_per_slide]

            # Determine slide title
            if len(batch) == 1:
                title = batch[0].caption or f"{section_title} - {content_type.value.title()}"
            else:
                start_idx = i + 1
                end_idx = min(i + len(batch), len(elements))
                title = f"{section_title} - {content_type.value.title()}s {start_idx}-{end_idx}"

            # Create slide with elements
            slide = Slide(
                title=title,
                content_type=content_type,
                content=batch,
                sequence_number=len(slides) + i // self.max_elements_per_slide,
            )
            slides.append(slide)

        return slides
