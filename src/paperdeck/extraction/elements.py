"""Extracted element data classes and utilities.

This module re-exports element classes from core.models and provides
extraction-specific utilities.
"""

# Re-export element classes for convenience
from ..core.models import (
    BoundingBox,
    ElementType,
    EquationElement,
    ExtractedElement,
    FigureElement,
    TableElement,
)

__all__ = [
    "BoundingBox",
    "ElementType",
    "ExtractedElement",
    "FigureElement",
    "TableElement",
    "EquationElement",
]
