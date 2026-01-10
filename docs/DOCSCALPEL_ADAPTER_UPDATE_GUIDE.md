# DocScalpelAdapter Update Guide: Handling v1.0.0 ExtractionResult

## Overview
This guide shows the recommended updates to `DocScalpelAdapter` to properly handle the new ExtractionResult fields from docscalpel v1.0.0:
- `success: bool`
- `errors: List[str]`
- `warnings: List[str]`
- `extraction_time_seconds: float`

---

## Current State vs. Recommended Changes

### Current Implementation (lines 137-164)

```python
try:
    # Create DocScalpel configuration
    docscalpel_config = self._create_docscalpel_config(element_types)

    # Extract elements using DocScalpel
    logger.info(f"Extracting elements from {pdf_path.name} using DocScalpel...")
    result = self.docscalpel.extract_elements(str(pdf_path), docscalpel_config)

    if not result.success:
        logger.warning(f"DocScalpel extraction completed with errors: {result.errors}")

    if result.warnings:
        for warning in result.warnings:
            logger.warning(f"DocScalpel warning: {warning}")

    # Convert DocScalpel elements to PaperDeck elements
    extracted = self._convert_elements(result.elements)

    logger.info(
        f"Successfully extracted {len(extracted)} element(s) from {pdf_path.name} "
        f"({result.figure_count} figures, {result.table_count} tables)"
    )

    return extracted

except Exception as e:
    logger.error(f"Error during DocScalpel extraction: {e}", exc_info=True)
    return []
```

### Issues with Current Implementation

1. ❌ **Wrong Log Level**: Uses WARNING for extraction failure (should be ERROR)
2. ❌ **Batch Error Logging**: Logs errors summary without individual details
3. ❌ **Missing Timing Info**: Ignores extraction_time_seconds from result
4. ❌ **No Overhead Detection**: Doesn't compare library vs. actual elapsed time
5. ❌ **Limited Context**: Success message doesn't reflect error conditions

---

## Recommended Implementation

### Step 1: Add Timing Tracking

```python
def extract(
    self,
    pdf_path: Path,
    element_types: Optional[List[ElementType]] = None,
) -> List[ExtractedElement]:
    """Extract figures and/or tables from a PDF using DocScalpel.

    This method orchestrates the extraction process, respecting configuration flags
    and element type filters. It returns an empty list if DocScalpel is unavailable
    or all element types are disabled.

    The extraction process:
    1. Check DocScalpel availability (graceful fallback if not installed)
    2. Apply configuration flags (extract_figures, extract_tables)
    3. Call DocScalpel extract_elements() function
    4. Convert DocScalpel Elements to PaperDeck ExtractedElements
    5. Log performance metrics and any errors/warnings

    Args:
        pdf_path: Path to the PDF file to process
        element_types: Optional list of element types to extract.
            Defaults to [ElementType.FIGURE, ElementType.TABLE].
            Can be filtered by configuration flags.

    Returns:
        List of ExtractedElement objects (FigureElement, TableElement).
        Returns empty list if:
        - DocScalpel is not installed
        - All element types are disabled by configuration
        - No elements found in the PDF
        - Extraction errors occur (logged but not raised)

    Example:
        >>> adapter = DocScalpelAdapter()
        >>> # Extract only figures
        >>> figures = adapter.extract(pdf_path, [ElementType.FIGURE])
        >>> # Extract both (default)
        >>> all_elements = adapter.extract(pdf_path)
    """
    if not self.docscalpel_available:
        logger.info("DocScalpel not available, skipping element extraction")
        return []

    # Default to extracting both figures and tables
    if element_types is None:
        element_types = [ElementType.FIGURE, ElementType.TABLE]

    # Respect configuration flags if provided
    if self.config:
        if not self.config.extract_figures and ElementType.FIGURE in element_types:
            element_types = [et for et in element_types if et != ElementType.FIGURE]
            logger.info("Figure extraction disabled by configuration")

        if not self.config.extract_tables and ElementType.TABLE in element_types:
            element_types = [et for et in element_types if et != ElementType.TABLE]
            logger.info("Table extraction disabled by configuration")

    # If all types filtered out, return empty list
    if not element_types:
        logger.info("No element types enabled for extraction")
        return []

    # Track timing for performance analysis
    import time
    start_time = time.perf_counter()

    # Use DocScalpel to extract all elements at once
    try:
        # Create DocScalpel configuration
        docscalpel_config = self._create_docscalpel_config(element_types)

        # Extract elements using DocScalpel
        logger.info(f"Extracting elements from {pdf_path.name} using DocScalpel...")
        result = self.docscalpel.extract_elements(str(pdf_path), docscalpel_config)

        # Calculate actual elapsed time
        elapsed_time = time.perf_counter() - start_time

        # Handle extraction result with detailed logging
        return self._handle_extraction_result(pdf_path, result, elapsed_time)

    except Exception as e:
        elapsed_time = time.perf_counter() - start_time
        logger.error(
            f"Error during DocScalpel extraction of {pdf_path.name} "
            f"(after {elapsed_time:.2f}s): {type(e).__name__}: {e}",
            exc_info=True
        )
        logger.info(f"Returning empty results for {pdf_path.name}")
        return []
```

### Step 2: Add Result Handler Method

```python
def _handle_extraction_result(
    self,
    pdf_path: Path,
    result,
    elapsed_time: float,
) -> List[ExtractedElement]:
    """Handle extraction result with structured logging and error reporting.

    This method:
    1. Validates the result structure
    2. Logs errors at ERROR level (not WARNING)
    3. Logs warnings at WARNING level
    4. Logs performance metrics
    5. Converts valid elements
    6. Returns partial results if available despite errors

    Args:
        pdf_path: Path to the PDF that was processed
        result: DocScalpel ExtractionResult object with:
            - success: bool indicating overall success
            - errors: List[str] of error messages (if any)
            - warnings: List[str] of warning messages (if any)
            - extraction_time_seconds: float of library execution time
            - elements: List of extracted element objects
            - figure_count: int count of figures
            - table_count: int count of tables
        elapsed_time: float of actual elapsed time including overhead

    Returns:
        List of ExtractedElement objects. May be partial if extraction
        had errors but returned some elements.
    """
    # First, log the overall status
    if not result.success:
        logger.error(f"DocScalpel extraction failed for {pdf_path.name}")
        self._log_extraction_errors(result.errors)
    else:
        logger.info(f"DocScalpel extraction succeeded for {pdf_path.name}")

    # Log warnings even on success
    if result.warnings:
        self._log_extraction_warnings(result.warnings)

    # Log performance metrics
    self._log_performance_metrics(pdf_path, result, elapsed_time)

    # Convert and return elements (even if there were errors, try partial)
    extracted = self._convert_elements(result.elements)

    # Log summary
    if extracted:
        logger.info(
            f"Successfully converted {len(extracted)} element(s) from "
            f"{pdf_path.name}: {result.figure_count} figures, "
            f"{result.table_count} tables"
        )
    elif not result.success:
        logger.warning(
            f"No elements extracted from {pdf_path.name} due to errors. "
            "Returning empty list."
        )
    else:
        logger.info(f"No elements found in {pdf_path.name}")

    return extracted
```

### Step 3: Add Structured Error Logging

```python
def _log_extraction_errors(self, errors: Optional[List[str]]) -> None:
    """Log extraction errors individually with context.

    Args:
        errors: List of error messages from DocScalpel result
    """
    if not errors:
        return

    error_count = len(errors)
    logger.error(f"DocScalpel reported {error_count} error(s):")

    # Log each error with enumeration
    for i, error in enumerate(errors, 1):
        logger.error(f"  [{i}/{error_count}] {error}")

    # Log first error again for visibility
    if error_count > 0:
        logger.error(f"First error: {errors[0]}")
```

### Step 4: Add Structured Warning Logging

```python
def _log_extraction_warnings(self, warnings: Optional[List[str]]) -> None:
    """Log extraction warnings individually.

    For many warnings (>10), log sample and suggest DEBUG for full details.

    Args:
        warnings: List of warning messages from DocScalpel result
    """
    if not warnings:
        return

    warning_count = len(warnings)
    logger.warning(f"DocScalpel reported {warning_count} warning(s):")

    # Log all warnings if reasonable count
    if warning_count <= 10:
        for i, warning in enumerate(warnings, 1):
            logger.warning(f"  [{i}/{warning_count}] {warning}")
    else:
        # Log sample + note about debug logging
        for i, warning in enumerate(warnings[:5], 1):
            logger.warning(f"  [{i}/{warning_count}] {warning}")
        logger.warning(f"  ... and {warning_count - 5} more warnings")
        logger.debug(f"Full warning list for detailed analysis: {warnings}")
```

### Step 5: Add Performance Metric Logging

```python
def _log_performance_metrics(
    self,
    pdf_path: Path,
    result,
    elapsed_time: float,
) -> None:
    """Log performance metrics for extraction.

    Compares library's internal timing with actual elapsed time
    to identify overhead and potential bottlenecks.

    Args:
        pdf_path: Path to PDF that was processed
        result: DocScalpel ExtractionResult with extraction_time_seconds
        elapsed_time: float of actual elapsed time in seconds
    """
    # Log at INFO level (operational metric)
    logger.info(
        f"Performance metrics for {pdf_path.name}: "
        f"total={elapsed_time:.2f}s, "
        f"library={result.extraction_time_seconds:.2f}s"
    )

    # Calculate overhead
    overhead = elapsed_time - result.extraction_time_seconds

    # Log detailed diagnostics at DEBUG level
    logger.debug(
        f"Extraction overhead for {pdf_path.name}: {overhead:.2f}s "
        f"({(overhead/elapsed_time)*100:.1f}% of total time)"
    )

    # Warn if overhead is significant (>20% or >2 seconds)
    if overhead > max(2.0, result.extraction_time_seconds * 0.2):
        logger.warning(
            f"High overhead for {pdf_path.name}: {overhead:.2f}s "
            f"(library={result.extraction_time_seconds:.2f}s, "
            f"total={elapsed_time:.2f}s). "
            f"May indicate configuration or I/O issues."
        )
```

### Step 6: Improve Element Conversion with Error Handling

```python
def _convert_elements(self, docscalpel_elements: List) -> List[ExtractedElement]:
    """Convert DocScalpel Element objects to PaperDeck ExtractedElement objects.

    Handles errors gracefully during conversion, logging issues but continuing
    with other elements.

    Args:
        docscalpel_elements: List of DocScalpel Element objects

    Returns:
        List of PaperDeck ExtractedElement objects (FigureElement, TableElement, etc.)
        May be partial if some elements failed conversion.
    """
    from ..core.models import FigureElement, TableElement, EquationElement, BoundingBox
    from uuid import uuid4

    converted = []
    element_count = len(docscalpel_elements)

    for i, ds_elem in enumerate(docscalpel_elements):
        try:
            # Map DocScalpel ElementType to PaperDeck ElementType
            if ds_elem.element_type == self.docscalpel.ElementType.FIGURE:
                paperdeck_type = ElementType.FIGURE
                element_class = FigureElement
            elif ds_elem.element_type == self.docscalpel.ElementType.TABLE:
                paperdeck_type = ElementType.TABLE
                element_class = TableElement
            elif ds_elem.element_type == self.docscalpel.ElementType.EQUATION:
                paperdeck_type = ElementType.EQUATION
                element_class = EquationElement
            else:
                logger.warning(
                    f"Unknown element type in element {i+1}/{element_count}: "
                    f"{ds_elem.element_type}"
                )
                continue

            # Validate required attributes
            if not hasattr(ds_elem, 'bounding_box'):
                logger.warning(
                    f"Element {i+1}/{element_count} missing bounding_box, skipping"
                )
                continue

            if not hasattr(ds_elem, 'page_number'):
                logger.warning(
                    f"Element {i+1}/{element_count} missing page_number, skipping"
                )
                continue

            # Convert DocScalpel BoundingBox to PaperDeck BoundingBox
            bbox = BoundingBox(
                x=ds_elem.bounding_box.x,
                y=ds_elem.bounding_box.y,
                width=ds_elem.bounding_box.width,
                height=ds_elem.bounding_box.height,
            )

            # Create PaperDeck element
            element = element_class(
                uuid=uuid4(),
                element_type=paperdeck_type,
                page_number=ds_elem.page_number,
                bounding_box=bbox,
                confidence_score=ds_elem.confidence_score,
                sequence_number=ds_elem.sequence_number,
                caption=None,  # DocScalpel doesn't extract captions yet
                output_filename=Path(ds_elem.output_filename),  # Path to saved image
            )

            converted.append(element)

        except Exception as e:
            # Log conversion error but continue with other elements
            logger.warning(
                f"Failed to convert element {i+1}/{element_count}: "
                f"{type(e).__name__}: {e}"
            )
            continue

    if not converted and docscalpel_elements:
        logger.warning(
            f"Converted 0 out of {element_count} elements. "
            "Check warnings above for details."
        )

    return converted
```

---

## Complete Updated Code

### File: `/Users/jangminsu/Development/paperdeck/src/paperdeck/extraction/docscalpel_adapter.py`

```python
"""
DocScalpel adapter for figure and table extraction.

This module provides an adapter pattern for integrating DocScalpel library
to extract figures and tables from PDF papers.
"""

from pathlib import Path
from typing import List, Optional
import logging
import time

from ..core.models import ExtractedElement, ElementType
from ..core.config import ExtractionConfiguration

logger = logging.getLogger(__name__)


class DocScalpelAdapter:
    """Adapter for DocScalpel library to extract figures and tables from PDFs.

    This adapter provides a clean interface to the DocScalpel library for extracting
    figures and tables from academic papers. It implements graceful degradation when
    DocScalpel is not installed and respects configuration flags for selective extraction.

    The adapter pattern isolates the DocScalpel dependency, making it easy to:
    - Test without requiring DocScalpel installation
    - Replace with alternative extraction backends
    - Handle import errors gracefully in production

    Attributes:
        config: Optional extraction configuration with flags and settings
        docscalpel_available: Whether DocScalpel library successfully loaded
        docscalpel: Reference to the docscalpel module (if available)

    Example:
        >>> from pathlib import Path
        >>> from paperdeck.core.models import ElementType
        >>> adapter = DocScalpelAdapter()
        >>> elements = adapter.extract(Path("paper.pdf"), [ElementType.FIGURE])
        >>> print(f"Found {len(elements)} figures")
    """

    def __init__(self, config: Optional[ExtractionConfiguration] = None):
        """Initialize DocScalpel adapter with optional configuration.

        Attempts to import the DocScalpel library. If import fails, logs a warning
        and sets docscalpel_available to False, allowing graceful fallback.

        Args:
            config: Optional extraction configuration controlling:
                - extract_figures: Enable/disable figure extraction
                - extract_tables: Enable/disable table extraction
                - confidence_threshold: Minimum confidence for elements
                - output_directory: Where to save extracted files

        Note:
            DocScalpel can be installed with:
            pip install git+https://github.com/zebehn/docscalpel.git
        """
        self.config = config
        self.docscalpel_available = False

        # Try to import DocScalpel
        try:
            import docscalpel
            self.docscalpel = docscalpel
            self.docscalpel_available = True
            logger.info("DocScalpel library loaded successfully")
        except ImportError:
            logger.warning(
                "DocScalpel not installed. Figure/table extraction will be skipped. "
                "Install with: pip install git+https://github.com/zebehn/docscalpel.git"
            )

    def extract(
        self,
        pdf_path: Path,
        element_types: Optional[List[ElementType]] = None,
    ) -> List[ExtractedElement]:
        """Extract figures and/or tables from a PDF using DocScalpel.

        This method orchestrates the extraction process, respecting configuration flags
        and element type filters. It returns an empty list if DocScalpel is unavailable
        or all element types are disabled.

        The extraction process:
        1. Check DocScalpel availability (graceful fallback if not installed)
        2. Apply configuration flags (extract_figures, extract_tables)
        3. Call DocScalpel extract_elements() function
        4. Convert DocScalpel Elements to PaperDeck ExtractedElements
        5. Log performance metrics and any errors/warnings

        Args:
            pdf_path: Path to the PDF file to process
            element_types: Optional list of element types to extract.
                Defaults to [ElementType.FIGURE, ElementType.TABLE].
                Can be filtered by configuration flags.

        Returns:
            List of ExtractedElement objects (FigureElement, TableElement).
            Returns empty list if:
            - DocScalpel is not installed
            - All element types are disabled by configuration
            - No elements found in the PDF
            - Extraction errors occur (logged but not raised)

        Example:
            >>> adapter = DocScalpelAdapter()
            >>> # Extract only figures
            >>> figures = adapter.extract(pdf_path, [ElementType.FIGURE])
            >>> # Extract both (default)
            >>> all_elements = adapter.extract(pdf_path)
        """
        if not self.docscalpel_available:
            logger.info("DocScalpel not available, skipping element extraction")
            return []

        # Default to extracting both figures and tables
        if element_types is None:
            element_types = [ElementType.FIGURE, ElementType.TABLE]

        # Respect configuration flags if provided
        if self.config:
            if not self.config.extract_figures and ElementType.FIGURE in element_types:
                element_types = [et for et in element_types if et != ElementType.FIGURE]
                logger.info("Figure extraction disabled by configuration")

            if not self.config.extract_tables and ElementType.TABLE in element_types:
                element_types = [et for et in element_types if et != ElementType.TABLE]
                logger.info("Table extraction disabled by configuration")

        # If all types filtered out, return empty list
        if not element_types:
            logger.info("No element types enabled for extraction")
            return []

        # Track timing for performance analysis
        start_time = time.perf_counter()

        # Use DocScalpel to extract all elements at once
        try:
            # Create DocScalpel configuration
            docscalpel_config = self._create_docscalpel_config(element_types)

            # Extract elements using DocScalpel
            logger.info(f"Extracting elements from {pdf_path.name} using DocScalpel...")
            result = self.docscalpel.extract_elements(str(pdf_path), docscalpel_config)

            # Calculate actual elapsed time
            elapsed_time = time.perf_counter() - start_time

            # Handle extraction result with detailed logging
            return self._handle_extraction_result(pdf_path, result, elapsed_time)

        except Exception as e:
            elapsed_time = time.perf_counter() - start_time
            logger.error(
                f"Error during DocScalpel extraction of {pdf_path.name} "
                f"(after {elapsed_time:.2f}s): {type(e).__name__}: {e}",
                exc_info=True
            )
            logger.info(f"Returning empty results for {pdf_path.name}")
            return []

    def _handle_extraction_result(
        self,
        pdf_path: Path,
        result,
        elapsed_time: float,
    ) -> List[ExtractedElement]:
        """Handle extraction result with structured logging and error reporting.

        This method:
        1. Validates the result structure
        2. Logs errors at ERROR level (not WARNING)
        3. Logs warnings at WARNING level
        4. Logs performance metrics
        5. Converts valid elements
        6. Returns partial results if available despite errors

        Args:
            pdf_path: Path to the PDF that was processed
            result: DocScalpel ExtractionResult object
            elapsed_time: Actual elapsed time including overhead

        Returns:
            List of ExtractedElement objects
        """
        # First, log the overall status
        if not result.success:
            logger.error(f"DocScalpel extraction failed for {pdf_path.name}")
            self._log_extraction_errors(result.errors)
        else:
            logger.info(f"DocScalpel extraction succeeded for {pdf_path.name}")

        # Log warnings even on success
        if result.warnings:
            self._log_extraction_warnings(result.warnings)

        # Log performance metrics
        self._log_performance_metrics(pdf_path, result, elapsed_time)

        # Convert and return elements (even if there were errors, try partial)
        extracted = self._convert_elements(result.elements)

        # Log summary
        if extracted:
            logger.info(
                f"Successfully converted {len(extracted)} element(s) from "
                f"{pdf_path.name}: {result.figure_count} figures, "
                f"{result.table_count} tables"
            )
        elif not result.success:
            logger.warning(
                f"No elements extracted from {pdf_path.name} due to errors. "
                "Returning empty list."
            )
        else:
            logger.info(f"No elements found in {pdf_path.name}")

        return extracted

    def _log_extraction_errors(self, errors: Optional[List[str]]) -> None:
        """Log extraction errors individually with context."""
        if not errors:
            return

        error_count = len(errors)
        logger.error(f"DocScalpel reported {error_count} error(s):")

        for i, error in enumerate(errors, 1):
            logger.error(f"  [{i}/{error_count}] {error}")

    def _log_extraction_warnings(self, warnings: Optional[List[str]]) -> None:
        """Log extraction warnings individually."""
        if not warnings:
            return

        warning_count = len(warnings)
        logger.warning(f"DocScalpel reported {warning_count} warning(s):")

        if warning_count <= 10:
            for i, warning in enumerate(warnings, 1):
                logger.warning(f"  [{i}/{warning_count}] {warning}")
        else:
            for i, warning in enumerate(warnings[:5], 1):
                logger.warning(f"  [{i}/{warning_count}] {warning}")
            logger.warning(f"  ... and {warning_count - 5} more warnings")
            logger.debug(f"Full warning list: {warnings}")

    def _log_performance_metrics(
        self,
        pdf_path: Path,
        result,
        elapsed_time: float,
    ) -> None:
        """Log performance metrics for extraction."""
        logger.info(
            f"Performance metrics for {pdf_path.name}: "
            f"total={elapsed_time:.2f}s, "
            f"library={result.extraction_time_seconds:.2f}s"
        )

        overhead = elapsed_time - result.extraction_time_seconds

        logger.debug(
            f"Extraction overhead for {pdf_path.name}: {overhead:.2f}s "
            f"({(overhead/elapsed_time)*100:.1f}% of total time)"
        )

        if overhead > max(2.0, result.extraction_time_seconds * 0.2):
            logger.warning(
                f"High overhead for {pdf_path.name}: {overhead:.2f}s "
                f"(library={result.extraction_time_seconds:.2f}s, "
                f"total={elapsed_time:.2f}s). "
                f"May indicate configuration or I/O issues."
            )

    def _create_docscalpel_config(self, element_types: List[ElementType]):
        """Create DocScalpel ExtractionConfig from PaperDeck element types.

        Args:
            element_types: List of PaperDeck ElementType enums to extract

        Returns:
            DocScalpel ExtractionConfig object
        """
        # Map PaperDeck ElementType to DocScalpel ElementType
        docscalpel_types = []
        for elem_type in element_types:
            if elem_type == ElementType.FIGURE:
                docscalpel_types.append(self.docscalpel.ElementType.FIGURE)
            elif elem_type == ElementType.TABLE:
                docscalpel_types.append(self.docscalpel.ElementType.TABLE)
            elif elem_type == ElementType.EQUATION:
                docscalpel_types.append(self.docscalpel.ElementType.EQUATION)

        # Create configuration with our settings
        config = self.docscalpel.ExtractionConfig(
            element_types=docscalpel_types,
            output_directory=str(self.config.output_directory) if self.config else ".",
            confidence_threshold=self.config.confidence_threshold if self.config else 0.5,
            naming_pattern="{type}_{counter}.png",
            overwrite_existing=True,
        )

        return config

    def _convert_elements(self, docscalpel_elements: List) -> List[ExtractedElement]:
        """Convert DocScalpel Element objects to PaperDeck ExtractedElement objects.

        Handles errors gracefully during conversion, logging issues but continuing
        with other elements.

        Args:
            docscalpel_elements: List of DocScalpel Element objects

        Returns:
            List of PaperDeck ExtractedElement objects
        """
        from ..core.models import FigureElement, TableElement, EquationElement, BoundingBox
        from uuid import uuid4

        converted = []
        element_count = len(docscalpel_elements)

        for i, ds_elem in enumerate(docscalpel_elements):
            try:
                # Map DocScalpel ElementType to PaperDeck ElementType
                if ds_elem.element_type == self.docscalpel.ElementType.FIGURE:
                    paperdeck_type = ElementType.FIGURE
                    element_class = FigureElement
                elif ds_elem.element_type == self.docscalpel.ElementType.TABLE:
                    paperdeck_type = ElementType.TABLE
                    element_class = TableElement
                elif ds_elem.element_type == self.docscalpel.ElementType.EQUATION:
                    paperdeck_type = ElementType.EQUATION
                    element_class = EquationElement
                else:
                    logger.warning(
                        f"Unknown element type in element {i+1}/{element_count}: "
                        f"{ds_elem.element_type}"
                    )
                    continue

                # Validate required attributes
                if not hasattr(ds_elem, 'bounding_box'):
                    logger.warning(
                        f"Element {i+1}/{element_count} missing bounding_box, skipping"
                    )
                    continue

                if not hasattr(ds_elem, 'page_number'):
                    logger.warning(
                        f"Element {i+1}/{element_count} missing page_number, skipping"
                    )
                    continue

                # Convert DocScalpel BoundingBox to PaperDeck BoundingBox
                bbox = BoundingBox(
                    x=ds_elem.bounding_box.x,
                    y=ds_elem.bounding_box.y,
                    width=ds_elem.bounding_box.width,
                    height=ds_elem.bounding_box.height,
                )

                # Create PaperDeck element
                element = element_class(
                    uuid=uuid4(),
                    element_type=paperdeck_type,
                    page_number=ds_elem.page_number,
                    bounding_box=bbox,
                    confidence_score=ds_elem.confidence_score,
                    sequence_number=ds_elem.sequence_number,
                    caption=None,
                    output_filename=Path(ds_elem.output_filename),
                )

                converted.append(element)

            except Exception as e:
                logger.warning(
                    f"Failed to convert element {i+1}/{element_count}: "
                    f"{type(e).__name__}: {e}"
                )
                continue

        if not converted and docscalpel_elements:
            logger.warning(
                f"Converted 0 out of {element_count} elements. "
                "Check warnings above for details."
            )

        return converted
```

---

## Testing the Updated Implementation

### Unit Test Example

```python
# tests/unit/extraction/test_docscalpel_adapter.py

import pytest
import logging
from pathlib import Path
from unittest.mock import Mock, MagicMock

from paperdeck.extraction.docscalpel_adapter import DocScalpelAdapter
from paperdeck.core.models import ElementType


class TestDocScalpelAdapterErrorHandling:
    """Test error and warning logging."""

    @pytest.fixture
    def mock_docscalpel_module(self):
        """Create mock DocScalpel module."""
        mock = MagicMock()
        mock.ElementType.FIGURE = "figure"
        mock.ElementType.TABLE = "table"
        return mock

    @pytest.fixture
    def adapter(self, mock_docscalpel_module):
        """Create adapter with mocked DocScalpel."""
        adapter = DocScalpelAdapter()
        adapter.docscalpel = mock_docscalpel_module
        adapter.docscalpel_available = True
        return adapter

    def test_extraction_with_errors_logs_at_error_level(
        self, adapter, tmp_path, caplog
    ):
        """Test that extraction errors are logged at ERROR level."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("dummy pdf")

        # Mock result with errors
        result = MagicMock()
        result.success = False
        result.errors = ["Error 1", "Error 2"]
        result.warnings = []
        result.elements = []
        result.figure_count = 0
        result.table_count = 0
        result.extraction_time_seconds = 0.5

        adapter.docscalpel.extract_elements.return_value = result

        with caplog.at_level(logging.ERROR):
            adapter.extract(pdf_file, [ElementType.FIGURE])

        # Verify ERROR level logs
        error_records = [r for r in caplog.records if r.levelno == logging.ERROR]
        assert len(error_records) >= 3  # At least: overall + 2 errors
        assert any("extraction failed" in r.message.lower() for r in error_records)
        assert any("Error 1" in r.message for r in error_records)
        assert any("Error 2" in r.message for r in error_records)

    def test_extraction_with_warnings_logs_at_warning_level(
        self, adapter, tmp_path, caplog
    ):
        """Test that extraction warnings are logged at WARNING level."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("dummy pdf")

        result = MagicMock()
        result.success = True
        result.errors = []
        result.warnings = ["Warning 1", "Warning 2"]
        result.elements = []
        result.figure_count = 0
        result.table_count = 0
        result.extraction_time_seconds = 0.5

        adapter.docscalpel.extract_elements.return_value = result

        with caplog.at_level(logging.WARNING):
            adapter.extract(pdf_file, [ElementType.FIGURE])

        warning_records = [r for r in caplog.records if r.levelno == logging.WARNING]
        assert len(warning_records) >= 2
        assert any("Warning 1" in r.message for r in warning_records)
        assert any("Warning 2" in r.message for r in warning_records)

    def test_performance_metrics_logged(self, adapter, tmp_path, caplog):
        """Test that performance metrics are logged."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("dummy pdf")

        result = MagicMock()
        result.success = True
        result.errors = []
        result.warnings = []
        result.elements = []
        result.figure_count = 0
        result.table_count = 0
        result.extraction_time_seconds = 2.34

        adapter.docscalpel.extract_elements.return_value = result

        with caplog.at_level(logging.INFO):
            adapter.extract(pdf_file, [ElementType.FIGURE])

        # Verify timing is in logs
        assert any("2.34s" in r.message for r in caplog.records)
        assert any("Performance metrics" in r.message for r in caplog.records)
```

---

## Migration Checklist

- [ ] Review current `docscalpel_adapter.py` implementation
- [ ] Add `import time` at top of file
- [ ] Update `extract()` method to track timing
- [ ] Add `_handle_extraction_result()` method
- [ ] Add `_log_extraction_errors()` method
- [ ] Add `_log_extraction_warnings()` method
- [ ] Add `_log_performance_metrics()` method
- [ ] Update `_convert_elements()` with error handling
- [ ] Update unit tests to verify logging levels
- [ ] Test with real DocScalpel v1.0.0 API
- [ ] Verify logs in development
- [ ] Update integration tests
- [ ] Document logging format in README

