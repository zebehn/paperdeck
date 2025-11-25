"""
Generation service for orchestrating presentation creation.

Coordinates text extraction, element extraction, and presentation generation.
"""

import logging
from pathlib import Path
from typing import Optional

from src.paperdeck.core.config import AppConfiguration, TextExtractionConfig
from src.paperdeck.core.models import Paper
from src.paperdeck.extraction.text_extractor import PyMuPDFTextExtractor
from src.paperdeck.models.extraction_result import ExtractionStatus

logger = logging.getLogger(__name__)


class GenerationService:
    """
    Orchestrates the presentation generation workflow.

    Responsibilities:
    - Extract text from PDF (with graceful fallback)
    - Populate Paper model with extracted content
    - Log extraction status and metrics
    - Coordinate with other services for complete generation
    """

    def __init__(self, config: AppConfiguration):
        """
        Initialize the generation service.

        Args:
            config: Application configuration
        """
        self.config = config
        self.text_extractor = PyMuPDFTextExtractor()

    def prepare_paper(
        self,
        pdf_path: Path,
        extraction_config: Optional[TextExtractionConfig] = None,
    ) -> Paper:
        """
        Prepare a Paper object with extracted text content.

        This method:
        1. Creates a Paper model from the PDF path
        2. Attempts to extract text content if enabled
        3. Logs extraction status and metrics
        4. Gracefully falls back to metadata-only if extraction fails

        Args:
            pdf_path: Path to the PDF file
            extraction_config: Configuration for text extraction (optional)

        Returns:
            Paper: Paper object with text content (if extraction succeeded)

        Note:
            This method NEVER raises exceptions for extraction failures.
            Instead, it logs warnings and returns a Paper object without text content.
        """
        # Create base Paper object
        paper = Paper(file_path=pdf_path)

        # Use provided config or default from app config
        if extraction_config is None:
            extraction_config = self.config.text_extraction

        # Check if text extraction is enabled
        if not extraction_config.enabled:
            logger.info(
                f"Text extraction disabled for {pdf_path.name}. "
                "Using metadata-only mode."
            )
            return paper

        # Attempt text extraction
        logger.info(f"Starting text extraction for {pdf_path.name}...")

        try:
            extraction_result = self.text_extractor.extract(
                pdf_path, extraction_config
            )

            # Log extraction metrics
            self._log_extraction_metrics(pdf_path, extraction_result)

            # Check if extraction was successful
            if extraction_result.is_successful:
                # Populate paper with extracted text
                paper.text_content = extraction_result.text_content
                paper.text_extraction_result = extraction_result

                logger.info(
                    f"Text extraction successful for {pdf_path.name}: "
                    f"{extraction_result.page_count} pages, "
                    f"{extraction_result.clean_text_length} characters, "
                    f"{extraction_result.extraction_time_seconds:.2f}s"
                )
            else:
                # Extraction failed - log warning and fall back
                self._log_extraction_failure(pdf_path, extraction_result)
                logger.warning(
                    f"Falling back to metadata-only mode for {pdf_path.name}"
                )

        except Exception as e:
            # Unexpected error during extraction - log and fall back gracefully
            logger.error(
                f"Unexpected error during text extraction for {pdf_path.name}: {e}",
                exc_info=True,
            )
            logger.warning(
                f"Falling back to metadata-only mode for {pdf_path.name}"
            )

        return paper

    def _log_extraction_metrics(self, pdf_path: Path, result) -> None:
        """
        Log detailed extraction metrics.

        Args:
            pdf_path: Path to the PDF file
            result: TextExtractionResult object
        """
        logger.info(f"Extraction metrics for {pdf_path.name}:")
        logger.info(f"  Status: {result.status.value}")
        logger.info(f"  Pages: {result.page_count}")
        logger.info(f"  Raw text length: {result.raw_text_length} chars")
        logger.info(f"  Clean text length: {result.clean_text_length} chars")
        logger.info(
            f"  Sanitization reduced text by {result.sanitization_reduction_pct:.1f}%"
        )
        logger.info(f"  Extraction time: {result.extraction_time_seconds:.2f}s")

        # Log warnings if present
        if result.warnings:
            for warning in result.warnings:
                logger.warning(f"  Warning: {warning}")

    def _log_extraction_failure(self, pdf_path: Path, result) -> None:
        """
        Log extraction failure details.

        Args:
            pdf_path: Path to the PDF file
            result: TextExtractionResult object with failure status
        """
        logger.warning(f"Text extraction failed for {pdf_path.name}")
        logger.warning(f"  Status: {result.status.value}")

        if result.error_message:
            logger.warning(f"  Error: {result.error_message}")

        # Log partial success info if available
        if result.status == ExtractionStatus.PARTIAL:
            logger.info(
                f"  Partial extraction: {result.page_count} pages processed"
            )
            if result.text_content:
                logger.info(
                    f"  Partial content length: {len(result.text_content)} chars"
                )
