"""
Data models for PDF text extraction results.

This module defines the status and result entities for text extraction operations.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ExtractionStatus(Enum):
    """Status of text extraction operation."""

    SUCCESS = "success"           # Text extracted successfully
    PARTIAL = "partial"           # Some text extracted, but with warnings
    FAILED = "failed"             # Extraction failed completely
    NOT_ATTEMPTED = "not_attempted"  # Text extraction was not attempted


@dataclass
class TextExtractionResult:
    """Result of PDF text extraction."""

    status: ExtractionStatus
    text_content: Optional[str]       # Extracted and sanitized text
    raw_text_length: int              # Length before sanitization
    clean_text_length: int            # Length after sanitization
    page_count: int                   # Number of pages processed
    extraction_time_seconds: float    # Time taken for extraction
    error_message: Optional[str] = None  # Error details if failed
    warnings: list[str] = field(default_factory=list)  # Non-fatal issues encountered

    @property
    def is_successful(self) -> bool:
        """Whether extraction produced usable text."""
        return self.status in (ExtractionStatus.SUCCESS, ExtractionStatus.PARTIAL)

    @property
    def sanitization_reduction_pct(self) -> float:
        """Percentage of text removed during sanitization."""
        if self.raw_text_length == 0:
            return 0.0
        reduction = self.raw_text_length - self.clean_text_length
        return (reduction / self.raw_text_length) * 100


def validate_extraction_result(result: TextExtractionResult) -> list[str]:
    """
    Validate extraction result for consistency.

    Args:
        result: TextExtractionResult to validate

    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []

    # Status-specific validations
    if result.status == ExtractionStatus.SUCCESS:
        if not result.text_content:
            errors.append("SUCCESS status requires non-empty text_content")
        if result.error_message:
            errors.append("SUCCESS status should not have error_message")

    if result.status == ExtractionStatus.FAILED:
        if not result.error_message:
            errors.append("FAILED status requires error_message")
        if result.text_content:
            errors.append("FAILED status should not have text_content")

    # Range validations
    if result.extraction_time_seconds < 0:
        errors.append("extraction_time_seconds must be non-negative")

    if result.page_count < 0:
        errors.append("page_count must be non-negative")

    if result.clean_text_length > result.raw_text_length:
        errors.append("clean_text_length cannot exceed raw_text_length")

    return errors
