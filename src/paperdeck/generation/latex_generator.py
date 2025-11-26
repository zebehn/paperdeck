"""LaTeX code generation with Jinja2 templates.

This module provides LaTeX generation functionality including special character
escaping and template rendering with custom Jinja2 delimiters.
"""

from pathlib import Path
from typing import Dict, List, Optional

from jinja2 import Environment, FileSystemLoader, Template

from ..core.exceptions import GenerationError
from ..core.models import Paper, Presentation, Slide


# LaTeX special characters that need escaping
LATEX_SPECIAL_CHARS = {
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\^{}",
    "\\": r"\textbackslash{}",
}


def escape_latex(text: str) -> str:
    """Escape special LaTeX characters in text.

    Args:
        text: Input text with potentially unsafe characters

    Returns:
        str: Text with LaTeX special characters escaped

    Example:
        >>> escape_latex("R&D costs: $50 & 10%")
        'R\\&D costs: \\$50 \\& 10\\%'
    """
    if not text:
        return text

    result = text
    # Use placeholder to avoid double-escaping backslash command
    BACKSLASH_PLACEHOLDER = "<<<BACKSLASH>>>"
    result = result.replace("\\", BACKSLASH_PLACEHOLDER)

    # Escape other special characters (excluding backslash)
    for char, escaped in LATEX_SPECIAL_CHARS.items():
        if char != "\\":  # Will handle separately
            result = result.replace(char, escaped)

    # Replace placeholder with escaped backslash command
    result = result.replace(BACKSLASH_PLACEHOLDER, "\\textbackslash{}")

    return result


def get_jinja_env(template_dir: Optional[Path] = None) -> Environment:
    """Get Jinja2 environment with LaTeX-friendly delimiters.

    Uses custom delimiters to avoid conflicts with LaTeX syntax:
    - Variable: \\VAR{variable}
    - Block: \\BLOCK{for x in items} ... \\BLOCK{endfor}

    Args:
        template_dir: Optional directory containing templates

    Returns:
        Environment: Configured Jinja2 environment
    """
    if template_dir:
        loader = FileSystemLoader(str(template_dir))
    else:
        loader = None

    env = Environment(
        loader=loader,
        block_start_string="\\BLOCK{",
        block_end_string="}",
        variable_start_string="\\VAR{",
        variable_end_string="}",
        trim_blocks=True,
        lstrip_blocks=True,
        autoescape=False,  # LaTeX doesn't use HTML escaping
    )

    # Add custom filters
    env.filters["escape_latex"] = escape_latex

    return env


# Keep old name for backwards compatibility
create_jinja_env = get_jinja_env


class LaTeXGenerator:
    """Generate LaTeX code from presentation model using templates."""

    def __init__(self, template_dir: Optional[Path] = None):
        """Initialize LaTeX generator.

        Args:
            template_dir: Directory containing Jinja2 templates
        """
        self.template_dir = template_dir
        self.env = get_jinja_env(template_dir)

    def generate_document(
        self,
        paper: Paper,
        slides: List[Slide],
        theme: str,
        title: str,
        author: str,
        date: str = r"\today",
    ) -> str:
        """Generate complete LaTeX beamer document.

        Args:
            paper: Source paper
            slides: List of slides to include
            theme: Beamer theme name
            title: Presentation title
            author: Author name
            date: Date string (default: \\today)

        Returns:
            str: Complete LaTeX beamer document

        Raises:
            GenerationError: If generation fails
        """
        try:
            # Create presentation object
            presentation = Presentation(
                paper=paper,
                slides=slides,
                theme=theme,
                title=title,
                author=author,
                date=date,
            )

            # Generate LaTeX code using Presentation.to_latex()
            latex_code = presentation.to_latex()
            return latex_code
        except Exception as e:
            raise GenerationError(f"Failed to generate document: {e}")

    def generate_from_template(
        self, presentation: Presentation, template_name: str
    ) -> str:
        """Generate LaTeX code from presentation using template.

        Args:
            presentation: Presentation model with slides
            template_name: Name of template file to use

        Returns:
            str: Generated LaTeX code

        Raises:
            GenerationError: If template not found or rendering fails
        """
        try:
            template = self.env.get_template(template_name)
        except Exception as e:
            raise GenerationError(f"Failed to load template '{template_name}': {e}")

        try:
            context = self._build_context(presentation)
            latex_code = template.render(context)
            return latex_code
        except Exception as e:
            raise GenerationError(f"Failed to render template: {e}")

    def generate_from_string(
        self, presentation: Presentation, template_str: str
    ) -> str:
        """Generate LaTeX code from presentation using template string.

        Args:
            presentation: Presentation model with slides
            template_str: Template string with Jinja2 syntax

        Returns:
            str: Generated LaTeX code

        Raises:
            GenerationError: If rendering fails
        """
        try:
            template = self.env.from_string(template_str)
            context = self._build_context(presentation)
            latex_code = template.render(context)
            return latex_code
        except Exception as e:
            raise GenerationError(f"Failed to render template: {e}")

    def _build_context(self, presentation: Presentation) -> Dict[str, any]:
        """Build Jinja2 context from presentation model.

        Args:
            presentation: Presentation model

        Returns:
            Dict[str, any]: Template context with presentation data
        """
        return {
            "presentation": presentation,
            "title": presentation.title,
            "author": presentation.author,
            "date": presentation.date,
            "theme": presentation.theme,
            "slides": presentation.slides,
            "paper": presentation.paper,
        }

    @staticmethod
    def generate_figure_latex(
        figure_element,
        output_dir: Optional[Path] = None,
        width: str = "0.8\\textwidth"
    ) -> str:
        """Generate LaTeX code for a figure element.

        Args:
            figure_element: FigureElement object to render
            output_dir: Output directory containing the figure file (for relative path calculation)
            width: LaTeX width specification (default: 0.8\\textwidth)

        Returns:
            str: LaTeX code for including the figure with caption
        """
        if not figure_element.output_filename:
            # No image file - return placeholder
            return f"% Figure {figure_element.sequence_number} (no image available)\n"

        # Format the graphics path
        graphics_path = LaTeXGenerator._format_graphics_path(
            figure_element.output_filename, output_dir
        )

        # Build LaTeX code
        latex = "\\begin{figure}\n"
        latex += "  \\centering\n"
        latex += f"  \\includegraphics[width={width}]{{{graphics_path}}}\n"

        # Add caption if available
        if figure_element.caption:
            escaped_caption = escape_latex(figure_element.caption)
            latex += f"  \\caption{{{escaped_caption}}}\n"

        latex += "\\end{figure}\n"
        return latex

    @staticmethod
    def _format_graphics_path(
        figure_path: Path,
        output_dir: Optional[Path] = None
    ) -> str:
        """Format graphics path for LaTeX \\includegraphics command.

        Converts absolute paths to relative paths from output directory.

        Args:
            figure_path: Absolute path to the figure file
            output_dir: Output directory (for calculating relative path)

        Returns:
            str: Formatted path suitable for \\includegraphics{}
        """
        if output_dir and figure_path.is_absolute():
            try:
                # Make path relative to output directory
                relative_path = figure_path.relative_to(output_dir)
                # Use forward slashes for LaTeX compatibility
                return str(relative_path).replace("\\", "/")
            except ValueError:
                # figure_path is not relative to output_dir, use absolute path
                pass

        # Use forward slashes for LaTeX compatibility
        return str(figure_path).replace("\\", "/")


# Keep old name for backwards compatibility
LatexGenerator = LaTeXGenerator
