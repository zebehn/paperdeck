# Python Logging Best Practices for Library Integration Error Handling

## Context: DocScalpel v1.0.0 Integration

The DocScalpelAdapter needs to handle new ExtractionResult fields:
- `success: bool`
- `errors: List[str]`
- `warnings: List[str]`
- `extraction_time_seconds: float`

---

## 1. Recommended Logging Pattern for Third-Party Library Errors

### Pattern Overview

```python
import logging

logger = logging.getLogger(__name__)

class ThirdPartyLibraryAdapter:
    """Adapter for third-party library integration."""

    def __init__(self):
        """Initialize with graceful degradation."""
        try:
            import third_party_lib
            self.lib = third_party_lib
            self.available = True
            logger.info("Third-party library loaded successfully")
        except ImportError as e:
            self.available = False
            logger.warning(
                f"Third-party library not available: {e}. "
                "Feature will be skipped. Install with: pip install third-party-lib"
            )

    def process(self, data):
        """Process data with the third-party library."""
        if not self.available:
            logger.info("Third-party library not available, skipping processing")
            return None

        try:
            result = self.lib.extract(data)

            # Validate result structure
            self._log_result_details(result)

            return result

        except Exception as e:
            logger.error(
                f"Error during third-party library call: {type(e).__name__}: {e}",
                exc_info=True  # Include full traceback
            )
            return None

    def _log_result_details(self, result):
        """Log third-party library result details."""
        # Log success status
        if hasattr(result, 'success'):
            if result.success:
                logger.info("Third-party library operation successful")
            else:
                logger.warning("Third-party library operation failed")

        # Log errors (if any)
        if hasattr(result, 'errors') and result.errors:
            error_count = len(result.errors)
            logger.error(f"Third-party library reported {error_count} error(s)")
            for i, error in enumerate(result.errors, 1):
                logger.error(f"  [{i}/{error_count}] {error}")

        # Log warnings (if any)
        if hasattr(result, 'warnings') and result.warnings:
            warning_count = len(result.warnings)
            logger.warning(f"Third-party library reported {warning_count} warning(s)")
            for i, warning in enumerate(result.warnings, 1):
                logger.warning(f"  [{i}/{warning_count}] {warning}")
```

### Key Principles

1. **Graceful Import Handling**
   - Catch ImportError at initialization
   - Log warning (not error) - import failures are often expected
   - Provide installation instructions
   - Set availability flag for later checks

2. **Context-Aware Logging**
   - Log library name in messages
   - Include operation context (what was being attempted)
   - Reference configuration if relevant

3. **Structured Error Information**
   - Use `exc_info=True` for unexpected exceptions
   - Include exception type and message
   - Log error details from library response

---

## 2. Individual vs. Batch Error/Warning Logging

### Recommendation: **Log Individually with Context**

#### Why Not Batch?
- **Discoverability**: Individual logs appear at their respective timestamps in log aggregation systems
- **Severity Distinction**: Each error/warning can have appropriate severity level
- **Structured Logging**: Easier to parse and analyze individually
- **Search/Filter**: Log aggregation tools can search for specific errors

#### Recommended Pattern

```python
def _log_result_details(self, result):
    """Log errors and warnings individually with sequence numbers."""

    # Log errors
    if result.errors:
        error_count = len(result.errors)
        logger.error(f"DocScalpel reported {error_count} error(s)")

        for index, error in enumerate(result.errors, 1):
            # Include index for large error lists
            logger.error(f"  Error [{index}/{error_count}]: {error}")

    # Log warnings
    if result.warnings:
        warning_count = len(result.warnings)
        logger.warning(f"DocScalpel reported {warning_count} warning(s)")

        for index, warning in enumerate(result.warnings, 1):
            logger.warning(f"  Warning [{index}/{warning_count}]: {warning}")
```

#### Alternative: Summary-First Pattern
For very large error/warning lists (>10 items):

```python
def _log_result_details(self, result):
    """Log summary first, then details."""

    if result.errors:
        error_count = len(result.errors)
        logger.error(
            f"DocScalpel extraction failed with {error_count} error(s). "
            f"First error: {result.errors[0]}"
        )

        # Only log details if not too many
        if error_count <= 10:
            for error in result.errors:
                logger.error(f"  - {error}")
        else:
            # Log sample + suggest debugging
            for error in result.errors[:5]:
                logger.error(f"  - {error}")
            logger.error(f"  ... and {error_count - 5} more errors")
            logger.debug(f"Full error list: {result.errors}")

    if result.warnings:
        warning_count = len(result.warnings)
        logger.warning(f"DocScalpel reported {warning_count} warning(s)")

        if warning_count <= 10:
            for warning in result.warnings:
                logger.warning(f"  - {warning}")
```

#### When to Log as Batch
- **Status Summary Only**: "10 errors occurred" without individual details
- **Performance Monitoring**: Only in DEBUG level for development

```python
logger.debug(f"Full error details: {', '.join(result.errors)}")
```

---

## 3. Log Level Guidelines

### Logging Levels Hierarchy
```
DEBUG   < INFO  < WARNING < ERROR  < CRITICAL
```

### DocScalpel-Specific Guidelines

| Scenario | Level | Example |
|----------|-------|---------|
| **Initialization** | | |
| Library loaded successfully | INFO | `"DocScalpel library loaded successfully"` |
| Library not installed | WARNING | `"DocScalpel not installed. Feature skipped."` |
| **Normal Operation** | | |
| Extraction started | INFO | `"Extracting elements from paper.pdf"` |
| Extraction completed | INFO | `"Successfully extracted 5 figures"` |
| Extraction took X seconds | DEBUG | `"Extraction completed in 2.34s"` |
| **Result Validation** | | |
| `success=True`, no errors | INFO | `"DocScalpel extraction successful"` |
| `success=False` but errors present | ERROR | `"DocScalpel extraction failed: {errors}"` |
| Warnings present but success=True | WARNING | `"Extraction completed with warnings: {warnings}"` |
| **Unexpected Issues** | | |
| Exception during extraction | ERROR | `"Error during DocScalpel extraction: {e}"` |
| Network/timeout issues | ERROR | `"DocScalpel timeout after 30s"` |
| Configuration issues | WARNING | `"Invalid confidence threshold, using default"` |
| Graceful degradation | INFO | `"DocScalpel unavailable, returning empty results"` |

### Key Mapping Rules

```python
# Initialize
logger.info("DocScalpel library loaded")

# Normal success
logger.info(f"Extracted {count} elements from {filename}")

# Result indicates failure
if not result.success:
    logger.error(f"DocScalpel extraction failed: {result.errors}")
elif result.warnings:
    logger.warning(f"DocScalpel warnings: {result.warnings}")

# Exception/unexpected
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
```

### NEVER Mix Up These Cases

❌ **Wrong**: Log as WARNING when success=False
```python
logger.warning(f"Extraction failed: {result.errors}")  # Should be ERROR
```

✅ **Right**: Log as ERROR when success=False
```python
logger.error(f"Extraction failed: {result.errors}")  # Correct
```

---

## 4. Performance Metric Logging Best Practices

### Pattern: Structured Performance Logging

```python
import time
import logging

logger = logging.getLogger(__name__)

class DocScalpelAdapter:
    def extract(self, pdf_path: Path, element_types: List[ElementType]):
        """Extract with performance tracking."""

        # Track timing
        start_time = time.perf_counter()
        logger.info(f"Starting extraction of {pdf_path.name}...")

        try:
            result = self.docscalpel.extract_elements(str(pdf_path), config)

            # Log performance metrics at INFO level (important for operations)
            elapsed = time.perf_counter() - start_time

            logger.info(
                f"Extraction completed for {pdf_path.name}: "
                f"extracted {len(result.elements)} elements in {elapsed:.2f}s"
            )

            # Compare library's internal timing with actual elapsed time
            if hasattr(result, 'extraction_time_seconds'):
                lib_time = result.extraction_time_seconds
                overhead = elapsed - lib_time

                if overhead > lib_time * 0.2:  # >20% overhead
                    logger.warning(
                        f"High overhead for {pdf_path.name}: "
                        f"library took {lib_time:.2f}s, "
                        f"total elapsed {elapsed:.2f}s "
                        f"(overhead: {overhead:.2f}s)"
                    )
                else:
                    logger.debug(
                        f"Performance metrics for {pdf_path.name}: "
                        f"library={lib_time:.2f}s, "
                        f"total={elapsed:.2f}s, "
                        f"overhead={overhead:.2f}s"
                    )

        except Exception as e:
            elapsed = time.perf_counter() - start_time
            logger.error(
                f"Extraction of {pdf_path.name} failed after {elapsed:.2f}s: {e}",
                exc_info=True
            )
            raise
```

### Performance Metric Levels

| Metric Type | Level | When to Use |
|------------|-------|------------|
| **Critical (SLA)** | INFO | Extraction time, total processing time |
| **Operational** | INFO | Success/failure, element counts, results |
| **Diagnostic** | DEBUG | Library vs. actual timing, overhead breakdown |
| **Optimization** | DEBUG | Detailed performance traces for profiling |

### Recommended Metrics to Log

```python
def _log_extraction_metrics(self, pdf_path: Path, result, elapsed_time: float):
    """Log comprehensive extraction metrics."""

    logger.info(
        f"Extraction summary for {pdf_path.name}: "
        f"success={result.success}, "
        f"elements={len(result.elements)}, "
        f"figures={result.figure_count}, "
        f"tables={result.table_count}, "
        f"time={elapsed_time:.2f}s"
    )

    # Log library's internal timing
    if hasattr(result, 'extraction_time_seconds'):
        logger.debug(
            f"Library internal timing: {result.extraction_time_seconds:.2f}s"
        )

    # Log errors/warnings with timing context
    if result.errors:
        logger.error(
            f"Extraction errors ({len(result.errors)}): {result.errors[0]} "
            f"(occurred after {elapsed_time:.2f}s)"
        )

    if result.warnings:
        logger.warning(
            f"Extraction warnings ({len(result.warnings)}): {result.warnings[0]}"
        )
```

### Avoid These Performance Logging Mistakes

❌ **Don't**: Log every millisecond
```python
logger.info(f"Extraction took {elapsed_time}s")  # Too much precision
```

✅ **Do**: Format to 2-3 decimal places
```python
logger.info(f"Extraction took {elapsed_time:.2f}s")
```

❌ **Don't**: Log performance at ERROR level
```python
logger.error(f"Extraction took 30s")  # Not an error!
```

✅ **Do**: Use INFO for operational metrics
```python
logger.info(f"Extraction took 30.45s")
```

❌ **Don't**: Log timing for every function call
```python
for elem in elements:
    start = time.time()
    process(elem)
    logger.info(f"Processed in {time.time() - start}s")  # Too verbose
```

✅ **Do**: Log aggregate timing
```python
start = time.time()
for elem in elements:
    process(elem)
logger.debug(f"Processed {len(elements)} elements in {time.time() - start:.2f}s")
```

---

## 5. Graceful Degradation Pattern

### Core Principle
**Never raise exceptions for third-party library failures. Always degrade gracefully.**

### Complete Graceful Degradation Pattern

```python
import logging
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

class DocScalpelAdapter:
    """Adapter with complete graceful degradation."""

    def __init__(self, config: Optional[ExtractionConfiguration] = None):
        """Initialize with graceful import handling."""
        self.config = config
        self.docscalpel_available = False

        try:
            import docscalpel
            self.docscalpel = docscalpel
            self.docscalpel_available = True
            logger.info("DocScalpel library loaded successfully")
        except ImportError as e:
            logger.warning(
                f"DocScalpel not available: {e}. "
                "Element extraction will be skipped. "
                "Install with: pip install git+https://github.com/zebehn/docscalpel.git"
            )

    def extract(
        self,
        pdf_path: Path,
        element_types: Optional[List[ElementType]] = None,
    ) -> List[ExtractedElement]:
        """Extract elements with full graceful degradation."""

        # Graceful degradation: Library not available
        if not self.docscalpel_available:
            logger.info(
                f"DocScalpel unavailable for {pdf_path.name}, "
                "returning empty results"
            )
            return []

        # Graceful degradation: File validation
        if not pdf_path.exists():
            logger.warning(f"PDF file not found: {pdf_path}")
            return []

        if not pdf_path.is_file():
            logger.warning(f"Path is not a file: {pdf_path}")
            return []

        if pdf_path.suffix.lower() != ".pdf":
            logger.warning(f"File is not a PDF: {pdf_path}")
            return []

        # Graceful degradation: Configuration filtering
        if element_types is None:
            element_types = [ElementType.FIGURE, ElementType.TABLE]

        if self.config:
            filtered_types = self._apply_config_filters(element_types)
            if not filtered_types:
                logger.info(
                    f"All element types disabled for {pdf_path.name}, "
                    "returning empty results"
                )
                return []
            element_types = filtered_types

        # Extraction attempt with comprehensive error handling
        return self._safe_extract(pdf_path, element_types)

    def _safe_extract(
        self,
        pdf_path: Path,
        element_types: List[ElementType],
    ) -> List[ExtractedElement]:
        """Perform extraction with comprehensive error handling."""

        try:
            logger.info(f"Extracting elements from {pdf_path.name}...")

            docscalpel_config = self._create_docscalpel_config(element_types)
            result = self.docscalpel.extract_elements(str(pdf_path), docscalpel_config)

            return self._handle_extraction_result(pdf_path, result)

        except TimeoutError:
            # Specific handling for timeout
            logger.warning(
                f"Extraction timeout for {pdf_path.name}, "
                "returning partial results if available"
            )
            return []

        except MemoryError:
            # Specific handling for memory issues
            logger.warning(
                f"Memory error during extraction of {pdf_path.name}, "
                "PDF may be too large. Returning empty results."
            )
            return []

        except Exception as e:
            # Generic exception handler - always graceful
            logger.error(
                f"Error during extraction of {pdf_path.name}: "
                f"{type(e).__name__}: {e}",
                exc_info=True
            )
            logger.info(f"Gracefully degrading - returning empty results for {pdf_path.name}")
            return []

    def _handle_extraction_result(
        self,
        pdf_path: Path,
        result,
    ) -> List[ExtractedElement]:
        """Handle extraction result with graceful degradation."""

        # Check success status
        if not result.success:
            logger.error(
                f"DocScalpel extraction failed for {pdf_path.name}. "
                f"Errors: {len(result.errors) if result.errors else 0}"
            )

            # Log each error
            for i, error in enumerate(result.errors or [], 1):
                logger.error(f"  Error [{i}]: {error}")

            # Even on failure, try to return partial results
            if hasattr(result, 'elements') and result.elements:
                logger.warning(
                    f"Returning {len(result.elements)} partial results "
                    f"despite extraction failure"
                )
                return self._convert_elements(result.elements)

            # Complete failure - return empty
            return []

        # Log warnings even on success
        if result.warnings:
            for i, warning in enumerate(result.warnings, 1):
                logger.warning(f"  Warning [{i}]: {warning}")

        # Extract and convert elements
        extracted = self._convert_elements(result.elements)

        # Log successful completion
        logger.info(
            f"Successfully extracted {len(extracted)} element(s) from {pdf_path.name}: "
            f"{result.figure_count} figures, {result.table_count} tables "
            f"(library time: {result.extraction_time_seconds:.2f}s)"
        )

        return extracted

    def _convert_elements(self, docscalpel_elements: List) -> List[ExtractedElement]:
        """Convert elements with error handling."""

        converted = []

        for i, ds_elem in enumerate(docscalpel_elements):
            try:
                element = self._convert_single_element(ds_elem)
                if element:
                    converted.append(element)
            except Exception as e:
                # Log conversion error but continue with other elements
                logger.warning(
                    f"Failed to convert element {i}: {type(e).__name__}: {e}"
                )
                continue

        if not converted and docscalpel_elements:
            logger.warning(
                f"Failed to convert {len(docscalpel_elements)} element(s). "
                "Returning empty list."
            )

        return converted

    def _convert_single_element(self, ds_elem) -> Optional[ExtractedElement]:
        """Convert a single element with validation."""

        # Validate required fields
        if not hasattr(ds_elem, 'element_type'):
            logger.warning("Element missing element_type, skipping")
            return None

        if not hasattr(ds_elem, 'bounding_box'):
            logger.warning(f"Element missing bounding_box, skipping")
            return None

        # ... conversion logic ...
        return element

    def _apply_config_filters(
        self,
        element_types: List[ElementType],
    ) -> List[ElementType]:
        """Apply configuration filters."""

        filtered = element_types.copy()

        if self.config and not self.config.extract_figures:
            filtered = [et for et in filtered if et != ElementType.FIGURE]
            logger.info("Figure extraction disabled by configuration")

        if self.config and not self.config.extract_tables:
            filtered = [et for et in filtered if et != ElementType.TABLE]
            logger.info("Table extraction disabled by configuration")

        return filtered
```

### Graceful Degradation Checklist

- [ ] **Library Import**: Catch ImportError, log warning, set availability flag
- [ ] **File Validation**: Check existence, is_file(), file extension
- [ ] **Configuration**: Respect flags, log when filtering applies
- [ ] **Extraction Timeout**: Handle with specific message, return partial if available
- [ ] **Memory Issues**: Handle separately, suggest file size limits
- [ ] **Generic Exceptions**: Catch all, log full context with exc_info=True
- [ ] **Partial Results**: Return partial results even on failure when possible
- [ ] **Conversion Errors**: Don't fail on single element - continue processing
- [ ] **Always Log Context**: Include filename, operation, and current state
- [ ] **Always Return Default**: Never raise, always return empty/None on failure

---

## Implementation Checklist for DocScalpelAdapter

### Current Implementation Review
✅ Already correct:
- Library import with try/except
- Logging at module level
- Returns empty list on unavailability
- exc_info=True for exceptions

### Recommended Updates

**1. Structured Error Logging**
```python
# Current (lines 145-150)
if not result.success:
    logger.warning(f"DocScalpel extraction completed with errors: {result.errors}")

if result.warnings:
    for warning in result.warnings:
        logger.warning(f"DocScalpel warning: {warning}")

# Recommended
if not result.success:
    logger.error(f"DocScalpel extraction failed for {pdf_path.name}")
    for i, error in enumerate(result.errors, 1):
        logger.error(f"  Error [{i}/{len(result.errors)}]: {error}")

if result.warnings:
    logger.warning(f"DocScalpel reported {len(result.warnings)} warning(s)")
    for i, warning in enumerate(result.warnings, 1):
        logger.warning(f"  Warning [{i}/{len(result.warnings)}]: {warning}")
```

**2. Performance Metric Logging**
```python
# Add timing tracking
import time

start_time = time.perf_counter()

result = self.docscalpel.extract_elements(str(pdf_path), docscalpel_config)
elapsed = time.perf_counter() - start_time

# Log with timing context
logger.info(
    f"Successfully extracted {len(extracted)} element(s) from {pdf_path.name} "
    f"({result.figure_count} figures, {result.table_count} tables) "
    f"in {elapsed:.2f}s (library: {result.extraction_time_seconds:.2f}s)"
)
```

**3. Add Diagnostic Logging**
```python
logger.debug(
    f"Extraction diagnostics for {pdf_path.name}: "
    f"total_time={elapsed:.2f}s, "
    f"library_time={result.extraction_time_seconds:.2f}s, "
    f"overhead={(elapsed - result.extraction_time_seconds):.2f}s"
)
```

**4. Element Conversion Error Handling**
```python
def _convert_elements(self, docscalpel_elements: List) -> List[ExtractedElement]:
    """Convert DocScalpel elements with error handling."""

    converted = []

    for i, ds_elem in enumerate(docscalpel_elements):
        try:
            # ... conversion logic ...
            converted.append(element)
        except Exception as e:
            logger.warning(
                f"Failed to convert element {i}/{len(docscalpel_elements)}: "
                f"{type(e).__name__}: {e}"
            )
            continue  # Don't fail entire batch

    return converted
```

---

## Logging Configuration Recommendations

### For Library Development

```python
# src/paperdeck/logging_config.py
import logging
import logging.handlers

def setup_logging(level=logging.INFO, log_file=None):
    """Configure logging for the application."""

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)

    # File handler (if specified)
    if log_file:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Capture all, filter at handler level
    root_logger.addHandler(console_handler)
    if log_file:
        root_logger.addHandler(file_handler)

    # Reduce noise from third-party libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('openai').setLevel(logging.WARNING)
```

### For Testing

```python
# tests/conftest.py
import logging

@pytest.fixture
def caplog_info(caplog):
    """Fixture to capture logs at INFO level."""
    caplog.set_level(logging.INFO)
    return caplog

def test_docscalpel_extraction_errors(caplog_info):
    """Test that extraction errors are logged properly."""

    adapter = DocScalpelAdapter()
    result = adapter.extract(pdf_path)

    # Verify error logging
    assert "extraction failed" in caplog_info.text.lower()
    assert len(caplog_info.records) > 0
```

---

## Summary Table: Quick Reference

| Question | Answer |
|----------|--------|
| **Log errors individually?** | Yes, with index/count for clarity |
| **Batch warnings?** | No, log individually. Use summary only if >10 items |
| **ERROR level for failures?** | Yes, when success=False |
| **WARNING level for warnings?** | Yes, when success=True but warnings exist |
| **INFO for metrics?** | Yes, for timing and element counts |
| **DEBUG for overhead?** | Yes, for library vs. actual timing comparison |
| **Always use exc_info=True?** | Yes, for unexpected exceptions |
| **Raise on library errors?** | Never. Always return default/None |
| **Log library name?** | Yes, every message should include context |
| **Format timing?** | 2-3 decimal places (e.g., 2.34s) |

