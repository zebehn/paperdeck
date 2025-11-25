"""LaTeX presentation generation.

This module provides LaTeX code generation functionality including template
rendering, special character escaping, and slide organization.
"""

from .latex_generator import (
    LaTeXGenerator,
    LatexGenerator,
    create_jinja_env,
    escape_latex,
    get_jinja_env,
)
from .slide_organizer import SlideOrganizer

__all__ = [
    "LaTeXGenerator",
    "LatexGenerator",
    "SlideOrganizer",
    "escape_latex",
    "create_jinja_env",
    "get_jinja_env",
]
