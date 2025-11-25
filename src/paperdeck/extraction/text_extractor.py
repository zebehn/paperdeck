"""
PyMuPDF-based text extraction from academic PDFs.

This module provides high-performance text extraction from PDF papers,
handling multi-column layouts and academic document structures.
"""

import time
from pathlib import Path
from typing import Optional

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

from src.paperdeck.core.config import TextExtractionConfig
from src.paperdeck.models.extraction_result import (
    ExtractionStatus,
    TextExtractionResult,
)
from src.paperdeck.extraction.text_sanitizer import TextSanitizer


class PyMuPDFTextExtractor:
    """
    Text extractor using PyMuPDF (fitz) for high-performance extraction.

    Handles multi-column layouts common in academic papers and performs
    basic text sanitization to remove artifacts.
    """

    def __init__(self):
        """Initialize the text extractor."""
        if fitz is None:
            raise ImportError(
                "PyMuPDF is required for text extraction. "
                "Install it with: pip install PyMuPDF>=1.23.0"
            )
        self.sanitizer = TextSanitizer()

    def extract(
        self,
        pdf_path: Path,
        config: TextExtractionConfig,
    ) -> TextExtractionResult:
        """
        Extract text from a PDF file.

        Args:
            pdf_path: Path to the PDF file
            config: Configuration for text extraction

        Returns:
            TextExtractionResult with extraction status and content
        """
        start_time = time.time()

        try:
            # Open the PDF (fitz will handle file existence)
            doc = fitz.open(str(pdf_path))
            page_count = len(doc)

            # Extract text from all pages
            raw_text_parts = []
            for page in doc:
                page_text = self._extract_page_text(page, config)
                if page_text:
                    raw_text_parts.append(page_text)

            doc.close()

            # Combine all page text
            raw_text = "\n\n".join(raw_text_parts)
            raw_text_length = len(raw_text)

            # Sanitize the text to remove artifacts
            clean_text = self.sanitizer.sanitize(raw_text, config)
            clean_text_length = len(clean_text)

            elapsed = time.time() - start_time

            if not raw_text or raw_text_length == 0:
                return TextExtractionResult(
                    status=ExtractionStatus.FAILED,
                    text_content=None,
                    raw_text_length=0,
                    clean_text_length=0,
                    page_count=page_count,
                    extraction_time_seconds=elapsed,
                    error_message="No text content extracted from PDF",
                )

            return TextExtractionResult(
                status=ExtractionStatus.SUCCESS,
                text_content=clean_text,
                raw_text_length=raw_text_length,
                clean_text_length=clean_text_length,
                page_count=page_count,
                extraction_time_seconds=elapsed,
            )

        except FileNotFoundError as e:
            elapsed = time.time() - start_time
            return TextExtractionResult(
                status=ExtractionStatus.FAILED,
                text_content=None,
                raw_text_length=0,
                clean_text_length=0,
                page_count=0,
                extraction_time_seconds=elapsed,
                error_message=f"File not found: {pdf_path}",
            )

        except RuntimeError as e:
            elapsed = time.time() - start_time
            error_msg = str(e)

            # Check for encryption error
            if "encrypt" in error_msg.lower():
                return TextExtractionResult(
                    status=ExtractionStatus.FAILED,
                    text_content=None,
                    raw_text_length=0,
                    clean_text_length=0,
                    page_count=0,
                    extraction_time_seconds=elapsed,
                    error_message=f"PDF is encrypted: {error_msg}",
                )

            # Check for file not found in error message
            if "no such file" in error_msg.lower() or "not found" in error_msg.lower():
                return TextExtractionResult(
                    status=ExtractionStatus.FAILED,
                    text_content=None,
                    raw_text_length=0,
                    clean_text_length=0,
                    page_count=0,
                    extraction_time_seconds=elapsed,
                    error_message=f"File not found: {pdf_path}",
                )

            # Generic error
            return TextExtractionResult(
                status=ExtractionStatus.FAILED,
                text_content=None,
                raw_text_length=0,
                clean_text_length=0,
                page_count=0,
                extraction_time_seconds=elapsed,
                error_message=f"Error extracting text: {error_msg}",
            )

        except Exception as e:
            elapsed = time.time() - start_time
            return TextExtractionResult(
                status=ExtractionStatus.FAILED,
                text_content=None,
                raw_text_length=0,
                clean_text_length=0,
                page_count=0,
                extraction_time_seconds=elapsed,
                error_message=f"Unexpected error: {str(e)}",
            )

    def _extract_page_text(
        self,
        page,
        config: TextExtractionConfig,
    ) -> str:
        """
        Extract text from a single page, handling multi-column layouts.

        Args:
            page: PyMuPDF page object
            config: Configuration for text extraction

        Returns:
            Extracted text from the page
        """
        try:
            # Use column_boxes for multi-column detection
            # Pass margins from config
            columns = page.column_boxes(
                footer_margin=config.footer_margin,
                header_margin=config.header_margin,
                no_image_text=config.remove_image_text,
            )

            if not columns:
                # Fallback to regular text extraction
                return page.get_text()

            # Extract text from each column
            column_texts = []
            for column_box in columns:
                # Get text from this column's bounding box
                text = page.get_text(clip=column_box)
                if text and text.strip():
                    column_texts.append(text)

            # Join columns with newline
            return "\n".join(column_texts)

        except Exception:
            # Fallback to simple text extraction
            return page.get_text()
