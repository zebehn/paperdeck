# Before/After Logging Comparison

## Side-by-Side: Current vs. Recommended Implementation

---

## Scenario 1: Extraction with Errors

### Current Implementation

```python
if not result.success:
    logger.warning(f"DocScalpel extraction completed with errors: {result.errors}")

if result.warnings:
    for warning in result.warnings:
        logger.warning(f"DocScalpel warning: {warning}")
```

**Log Output:**
```
WARNING - DocScalpel extraction completed with errors: ['Error 1', 'Error 2']
WARNING - DocScalpel warning: Warning 1
WARNING - DocScalpel warning: Warning 2
```

**Problems:**
- ❌ Uses WARNING for failures (should be ERROR)
- ❌ Errors logged as single batch message
- ❌ No enumeration or count context
- ❌ Hard to parse in log aggregation systems
- ❌ Errors and warnings at same level (can't distinguish severity)

### Recommended Implementation

```python
if not result.success:
    logger.error(f"DocScalpel extraction failed for {pdf_path.name}")
    self._log_extraction_errors(result.errors)
else:
    logger.info(f"DocScalpel extraction succeeded for {pdf_path.name}")

if result.warnings:
    self._log_extraction_warnings(result.warnings)

def _log_extraction_errors(self, errors: Optional[List[str]]) -> None:
    if not errors:
        return
    error_count = len(errors)
    logger.error(f"DocScalpel reported {error_count} error(s):")
    for i, error in enumerate(errors, 1):
        logger.error(f"  [{i}/{error_count}] {error}")

def _log_extraction_warnings(self, warnings: Optional[List[str]]) -> None:
    if not warnings:
        return
    warning_count = len(warnings)
    logger.warning(f"DocScalpel reported {warning_count} warning(s):")
    for i, warning in enumerate(warnings, 1):
        logger.warning(f"  [{i}/{warning_count}] {warning}")
```

**Log Output:**
```
ERROR   - DocScalpel extraction failed for paper.pdf
ERROR   - DocScalpel reported 2 error(s):
ERROR   -   [1/2] Error 1
ERROR   -   [2/2] Error 2
WARNING - DocScalpel reported 2 warning(s):
WARNING -   [1/2] Warning 1
WARNING -   [2/2] Warning 2
```

**Benefits:**
- ✅ Correct level: ERROR for failures, WARNING for warnings
- ✅ Individual log entries for each error
- ✅ Enumeration shows progress: [1/2], [2/2]
- ✅ Parseable by log aggregation tools
- ✅ Clear distinction between error and warning severity

---

## Scenario 2: Performance Metrics

### Current Implementation

```python
logger.info(
    f"Successfully extracted {len(extracted)} element(s) from {pdf_path.name} "
    f"({result.figure_count} figures, {result.table_count} tables)"
)
```

**Log Output:**
```
INFO - Successfully extracted 5 element(s) from paper.pdf (3 figures, 2 tables)
```

**Problems:**
- ❌ Doesn't include timing information
- ❌ No performance comparison (library vs. actual elapsed)
- ❌ Can't detect overhead or bottlenecks
- ❌ Missing extraction_time_seconds from new API

### Recommended Implementation

```python
# Track actual time
start_time = time.perf_counter()
result = self.docscalpel.extract_elements(str(pdf_path), docscalpel_config)
elapsed_time = time.perf_counter() - start_time

# Log with timing
logger.info(
    f"Performance metrics for {pdf_path.name}: "
    f"total={elapsed_time:.2f}s, "
    f"library={result.extraction_time_seconds:.2f}s"
)

# Detect overhead
def _log_performance_metrics(self, pdf_path: Path, result, elapsed_time: float):
    logger.info(
        f"Performance metrics for {pdf_path.name}: "
        f"total={elapsed_time:.2f}s, library={result.extraction_time_seconds:.2f}s"
    )

    overhead = elapsed_time - result.extraction_time_seconds
    logger.debug(
        f"Extraction overhead for {pdf_path.name}: {overhead:.2f}s "
        f"({(overhead/elapsed_time)*100:.1f}% of total time)"
    )

    if overhead > max(2.0, result.extraction_time_seconds * 0.2):
        logger.warning(
            f"High overhead for {pdf_path.name}: {overhead:.2f}s. "
            f"May indicate I/O or configuration issues."
        )
```

**Log Output:**
```
INFO    - Performance metrics for paper.pdf: total=3.45s, library=3.34s
DEBUG   - Extraction overhead for paper.pdf: 0.11s (3.2% of total time)
INFO    - Successfully converted 5 element(s) from paper.pdf: 3 figures, 2 tables
```

If overhead is high:
```
INFO    - Performance metrics for paper.pdf: total=5.50s, library=3.34s
WARNING - High overhead for paper.pdf: 2.16s. May indicate I/O or configuration issues.
DEBUG   - Extraction overhead for paper.pdf: 2.16s (39.3% of total time)
```

**Benefits:**
- ✅ Includes timing information from new API
- ✅ Shows both library and actual elapsed time
- ✅ Automatically detects anomalous overhead
- ✅ Helpful diagnostic information for optimization
- ✅ Guides investigation of performance issues

---

## Scenario 3: Exception Handling

### Current Implementation

```python
except Exception as e:
    logger.error(f"Error during DocScalpel extraction: {e}", exc_info=True)
    return []
```

**Log Output:**
```
ERROR - Error during DocScalpel extraction: [Errno 2] No such file or directory: '/path/to/paper.pdf'
ERROR - Traceback (most recent call last):
        File "...", line 143, in extract
        result = self.docscalpel.extract_elements(str(pdf_path), docscalpel_config)
        File "docscalpel/extract.py", line 45, in extract_elements
        with open(pdf_path) as f:
        FileNotFoundError: [Errno 2] No such file or directory: '/path/to/paper.pdf'
```

**Problems:**
- ❌ Error message doesn't include context (filename, operation)
- ❌ No timing information for how long it failed
- ❌ User doesn't know if degradation occurred gracefully

### Recommended Implementation

```python
start_time = time.perf_counter()

try:
    logger.info(f"Extracting elements from {pdf_path.name} using DocScalpel...")
    result = self.docscalpel.extract_elements(str(pdf_path), docscalpel_config)

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

**Log Output:**
```
INFO    - Extracting elements from paper.pdf using DocScalpel...
ERROR   - Error during DocScalpel extraction of paper.pdf (after 0.05s): FileNotFoundError: [Errno 2] No such file or directory
ERROR   - Traceback (most recent call last):
          ...full traceback...
INFO    - Returning empty results for paper.pdf
```

**Benefits:**
- ✅ Context-aware error message (filename, filename)
- ✅ Timing shows how long before failure
- ✅ Clear indication that degradation occurred
- ✅ Exception type included for categorization
- ✅ Operator can understand what happened at a glance

---

## Scenario 4: Element Conversion

### Current Implementation

```python
def _convert_elements(self, docscalpel_elements: List) -> List[ExtractedElement]:
    """Convert DocScalpel Element objects to PaperDeck ExtractedElement objects."""
    converted = []

    for ds_elem in docscalpel_elements:
        # Map DocScalpel ElementType to PaperDeck ElementType
        if ds_elem.element_type == self.docscalpel.ElementType.FIGURE:
            # ... conversion logic ...
        else:
            logger.warning(f"Unknown element type: {ds_elem.element_type}")
            continue

    return converted
```

**Log Output:**
```
WARNING - Unknown element type: 'equation'
```

**Problems:**
- ❌ No context about which element failed (number/position)
- ❌ No total count, so can't tell if many elements failed
- ❌ Can't catch other conversion errors (missing attributes, etc.)
- ❌ Users don't know how many elements were lost

### Recommended Implementation

```python
def _convert_elements(self, docscalpel_elements: List) -> List[ExtractedElement]:
    """Convert elements with error handling and diagnostics."""
    converted = []
    element_count = len(docscalpel_elements)

    for i, ds_elem in enumerate(docscalpel_elements):
        try:
            # Validate element type
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

            # ... conversion logic ...
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

**Log Output (Success):**
```
INFO - Successfully converted 5 element(s) from paper.pdf: 3 figures, 2 tables
```

**Log Output (With Issues):**
```
WARNING - Unknown element type in element 3/5: 'equation'
WARNING - Element 5/5 missing bounding_box, skipping
WARNING - Failed to convert element 4/5: AttributeError: 'Element' has no attribute 'confidence'
INFO    - Successfully converted 2 element(s) from paper.pdf (partial): 2 figures, 0 tables
```

**Log Output (Complete Failure):**
```
WARNING - Failed to convert element 1/5: AttributeError: 'Element' has no attribute 'element_type'
WARNING - Failed to convert element 2/5: AttributeError: 'Element' has no attribute 'element_type'
WARNING - Failed to convert element 3/5: AttributeError: 'Element' has no attribute 'element_type'
WARNING - Failed to convert element 4/5: AttributeError: 'Element' has no attribute 'element_type'
WARNING - Failed to convert element 5/5: AttributeError: 'Element' has no attribute 'element_type'
WARNING - Converted 0 out of 5 elements. Check warnings above for details.
```

**Benefits:**
- ✅ Context: Shows which element [i/total]
- ✅ Detailed messages for different failure types
- ✅ Exception type included for debugging
- ✅ Summary message if complete failure
- ✅ Users understand exactly what happened and why

---

## Scenario 5: Success Path (Full Comparison)

### Current Implementation

```
INFO - Extracting elements from paper.pdf using DocScalpel...
INFO - Successfully extracted 5 element(s) from paper.pdf (3 figures, 2 tables)
```

### Recommended Implementation

```
INFO    - Extracting elements from paper.pdf using DocScalpel...
INFO    - DocScalpel extraction succeeded for paper.pdf
INFO    - Performance metrics for paper.pdf: total=2.45s, library=2.34s
DEBUG   - Extraction overhead for paper.pdf: 0.11s (4.5% of total time)
INFO    - Successfully converted 5 element(s) from paper.pdf: 3 figures, 2 tables
```

**Comparison:**

| Aspect | Current | Recommended |
|--------|---------|-------------|
| Overall Status | 1 message | 1 message (+ explicit success) |
| Performance Info | None | 2 messages (INFO + DEBUG) |
| Overhead Detection | None | Automatic if >20% or >2s |
| Timing Visibility | None | Shown in INFO |
| Diagnostic Info | None | DEBUG level details |
| Total Messages | 2 | 5 (INFO visible, DEBUG optional) |

---

## Log Filtering for Different Audiences

### User/Operator (INFO only)
```
INFO    - Extracting elements from paper.pdf using DocScalpel...
INFO    - DocScalpel extraction succeeded for paper.pdf
INFO    - Performance metrics for paper.pdf: total=2.45s, library=2.34s
INFO    - Successfully converted 5 element(s) from paper.pdf: 3 figures, 2 tables
```

### Developer/Support (INFO + WARNING)
```
INFO    - Extracting elements from paper.pdf using DocScalpel...
INFO    - DocScalpel extraction succeeded for paper.pdf
WARNING - DocScalpel reported 1 warning(s):
WARNING -   [1/1] Confidence score below threshold
INFO    - Performance metrics for paper.pdf: total=2.45s, library=2.34s
INFO    - Successfully converted 5 element(s) from paper.pdf: 3 figures, 2 tables
```

### Troubleshooting (INFO + WARNING + ERROR)
```
INFO    - Extracting elements from paper.pdf using DocScalpel...
ERROR   - DocScalpel extraction failed for paper.pdf
ERROR   - DocScalpel reported 2 error(s):
ERROR   -   [1/2] PDF parsing error at page 5
ERROR   -   [2/2] Insufficient memory for large image
WARNING - No elements extracted from paper.pdf due to errors. Returning empty list.
```

### Deep Diagnosis (DEBUG included)
```
INFO    - Extracting elements from paper.pdf using DocScalpel...
INFO    - DocScalpel extraction succeeded for paper.pdf
INFO    - Performance metrics for paper.pdf: total=2.45s, library=2.34s
DEBUG   - Extraction overhead for paper.pdf: 0.11s (4.5% of total time)
DEBUG   - Element conversion details: 5 processed, 0 failed
INFO    - Successfully converted 5 element(s) from paper.pdf: 3 figures, 2 tables
```

---

## Summary of Key Changes

| Aspect | Current | Recommended | Impact |
|--------|---------|-------------|--------|
| **Error Log Level** | WARNING | ERROR | Clearer severity |
| **Error Logging** | Batch message | Individual messages | Better search/filter |
| **Error Enumeration** | None | [i/total] format | Context and progress |
| **Performance Metrics** | None | INFO + DEBUG | Visibility + optimization |
| **Overhead Detection** | None | Automatic | Issue identification |
| **Timing Format** | None | X.XXs (2 decimals) | Consistency |
| **Element Conversion** | Basic | With validation | Resilience |
| **Exception Context** | Generic | With timing/filename | Debugging |
| **Success Message** | Generic count | Count + timing | Completeness |
| **Log Parsing** | Text-based | Structured | Tool-friendly |

---

## Testing the Changes

### Test 1: Error Level Verification

```python
def test_extraction_errors_use_error_level(caplog):
    """Verify errors are logged at ERROR level, not WARNING."""
    adapter = DocScalpelAdapter()

    result = MagicMock()
    result.success = False
    result.errors = ["Error 1"]
    result.warnings = []
    # ... setup ...

    adapter.extract(pdf_path)

    # Verify ERROR level
    error_records = [r for r in caplog.records if r.levelno >= logging.ERROR]
    assert len(error_records) > 0
    assert any("extraction failed" in r.message.lower() for r in error_records)
    assert any("Error 1" in r.message for r in error_records)
```

### Test 2: Performance Metrics

```python
def test_performance_metrics_logged(caplog):
    """Verify timing metrics are included in logs."""
    adapter = DocScalpelAdapter()
    # ... setup with result.extraction_time_seconds = 2.34 ...

    adapter.extract(pdf_path)

    # Verify timing in logs
    messages = [r.message for r in caplog.records]
    timing_message = next((m for m in messages if "Performance metrics" in m), None)
    assert timing_message is not None
    assert "2.34s" in timing_message
```

