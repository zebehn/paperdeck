# DocScalpelAdapter Logging Architecture

## Overview

The updated DocScalpelAdapter implements a layered logging approach that separates concerns and provides different levels of detail for different audiences.

```
┌─────────────────────────────────────────────────────────────────┐
│ User Application / CLI                                          │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│ PaperExtractor (Orchestrator)                                   │
│ - Validates inputs                                              │
│ - Manages extraction pipeline                                   │
│ - Logs high-level status                                        │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│ DocScalpelAdapter (Third-Party Integration)                     │
│                                                                  │
│ ┌──────────────────────────────────────────────────────────┐   │
│ │ extract() - Public interface                            │   │
│ │ - Library availability check                            │   │
│ │ - Configuration filtering                               │   │
│ │ - Timing tracking                                        │   │
│ │ - Exception handling                                     │   │
│ └───────────────┬──────────────────────────────────────────┘   │
│                 │                                                │
│ ┌───────────────▼──────────────────────────────────────────┐   │
│ │ _handle_extraction_result() - Result processing         │   │
│ │ - Validates result structure                            │   │
│ │ - Delegates to specific loggers                         │   │
│ │ - Orchestrates conversion                               │   │
│ └───────┬───────────────┬─────────────────┬───────────────┘   │
│         │               │                 │                     │
│ ┌───────▼────┐ ┌───────▼────┐ ┌─────────▼────┐ ┌────────────┐ │
│ │ _log_      │ │ _log_      │ │ _log_        │ │ _convert_  │ │
│ │ extraction_│ │ extraction_│ │ performance_ │ │ elements() │ │
│ │ errors()   │ │ warnings() │ │ metrics()    │ └────────────┘ │
│ │            │ │            │ │              │                 │
│ │ Log Level: │ │ Log Level: │ │ Log Level:   │                 │
│ │ ERROR      │ │ WARNING    │ │ INFO/DEBUG   │                 │
│ └────────────┘ └────────────┘ └──────────────┘                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│ Third-Party Library (docscalpel v1.0.0)                         │
│ ExtractionResult {                                              │
│   success: bool,                                                │
│   errors: List[str],                                            │
│   warnings: List[str],                                          │
│   extraction_time_seconds: float,                               │
│   elements: List[Element],                                      │
│   figure_count: int,                                            │
│   table_count: int                                              │
│ }                                                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## Logging Flow: Success Case

```
extract(pdf_path)
  ↓
  INFO: "Extracting elements from paper.pdf using DocScalpel..."
  ↓
  [Calls library]
  ↓
  result.success == True
  ↓
  INFO: "DocScalpel extraction succeeded for paper.pdf"
  ↓
  result.warnings is empty?
  ├─ YES: Skip warning logging
  └─ NO:
     ↓
     WARNING: "DocScalpel reported 2 warning(s):"
     WARNING: "  [1/2] Warning text here"
     WARNING: "  [2/2] Warning text here"
  ↓
  INFO: "Performance metrics for paper.pdf: total=2.45s, library=2.34s"
  ↓
  DEBUG: "Extraction overhead: 0.11s (4.5% of total time)"
  ↓
  Convert elements (with error handling)
  ↓
  INFO: "Successfully converted 5 element(s) from paper.pdf: 3 figures, 2 tables"
  ↓
  RETURN: [ExtractedElement, ...]
```

---

## Logging Flow: Failure Case

```
extract(pdf_path)
  ↓
  INFO: "Extracting elements from paper.pdf using DocScalpel..."
  ↓
  [Calls library]
  ↓
  result.success == False
  ↓
  ERROR: "DocScalpel extraction failed for paper.pdf"
  ↓
  _log_extraction_errors():
  ERROR: "DocScalpel reported 2 error(s):"
  ERROR: "  [1/2] PDF parsing error at page 5"
  ERROR: "  [2/2] Insufficient memory for large image"
  ↓
  result.warnings?
  ├─ YES:
  │  WARNING: "DocScalpel reported 1 warning(s):"
  │  WARNING: "  [1/1] Confidence score below threshold"
  └─ NO: Skip warning logging
  ↓
  INFO: "Performance metrics for paper.pdf: total=3.12s, library=3.05s"
  ↓
  Convert elements (with graceful degradation)
  ↓
  result.elements has items?
  ├─ YES:
  │  INFO: "Successfully converted X element(s) from paper.pdf"
  │  RETURN: [Partial results]
  └─ NO:
     WARNING: "No elements extracted from paper.pdf due to errors. Returning empty list."
     RETURN: []
```

---

## Logging Flow: Exception Case

```
extract(pdf_path)
  ↓
  INFO: "Extracting elements from paper.pdf using DocScalpel..."
  ↓
  [Calls library]
  ↓
  EXCEPTION: TimeoutError / MemoryError / Generic Exception
  ↓
  elapsed_time = actual elapsed time
  ↓
  ERROR: "Error during DocScalpel extraction of paper.pdf (after 30.15s): TimeoutError: ..."
  ERROR: [Full exception traceback - exc_info=True]
  ↓
  INFO: "Returning empty results for paper.pdf"
  ↓
  RETURN: []
```

---

## Logging Flow: Graceful Degradation (Library Not Available)

```
__init__()
  ↓
  ImportError: docscalpel not found
  ↓
  WARNING: "DocScalpel not installed. Figure/table extraction will be skipped. Install with: ..."
  ↓
  self.docscalpel_available = False
  ↓
extract(pdf_path)
  ↓
  if not self.docscalpel_available:
    INFO: "DocScalpel not available, skipping element extraction"
    RETURN: []
```

---

## Message Format Examples

### INFO Messages (Operational)

```
✓ "DocScalpel library loaded successfully"
✓ "Extracting elements from paper.pdf using DocScalpel..."
✓ "DocScalpel extraction succeeded for paper.pdf"
✓ "Performance metrics for paper.pdf: total=2.45s, library=2.34s"
✓ "Successfully converted 5 element(s) from paper.pdf: 3 figures, 2 tables"
✓ "Figure extraction disabled by configuration"
✓ "No element types enabled for extraction"
✓ "Returning empty results for paper.pdf"
```

### WARNING Messages (Non-Fatal Issues)

```
✓ "DocScalpel not installed. Feature will be skipped. Install with: ..."
✓ "DocScalpel reported 2 warning(s):"
✓ "  [1/2] Confidence score below threshold"
✓ "  [2/2] Missing caption in element"
✓ "High overhead for paper.pdf: 0.85s (library=2.34s, total=3.19s)"
✓ "No elements extracted from paper.pdf due to errors. Returning empty list."
```

### ERROR Messages (Failures)

```
✓ "DocScalpel extraction failed for paper.pdf"
✓ "DocScalpel reported 2 error(s):"
✓ "  [1/2] PDF parsing error at page 5"
✓ "  [2/2] Insufficient memory for large image"
✓ "Error during DocScalpel extraction of paper.pdf (after 30.15s): TimeoutError: ..."
✓ "Failed to convert element 3/10: AttributeError: 'Element' has no attribute 'bbox'"
```

### DEBUG Messages (Diagnostic)

```
✓ "Extraction overhead for paper.pdf: 0.11s (4.5% of total time)"
✓ "Full warning list: [...all warnings...]"
✓ "Extracted diagnostics: library_time=2.34s, total=2.45s, overhead=0.11s"
```

---

## Error/Warning Count Logging

### Few Items (≤10): Log All

```
WARNING: "DocScalpel reported 2 warning(s):"
WARNING: "  [1/2] Confidence score too low"
WARNING: "  [2/2] Missing caption metadata"
```

### Many Items (>10): Summary + Sample

```
ERROR: "DocScalpel reported 47 error(s):"
ERROR: "  [1/47] PDF page 1: parsing failed"
ERROR: "  [2/47] PDF page 2: image extraction failed"
ERROR: "  [3/47] PDF page 3: text extraction failed"
ERROR: "  [4/47] PDF page 4: layout detection failed"
ERROR: "  [5/47] PDF page 5: element positioning failed"
ERROR: "  ... and 42 more errors"
DEBUG: "Full error list: [...]"  # All errors for detailed analysis
```

---

## Performance Metric Logging Tiers

### Tier 1: INFO (Operational)
Always logged for production visibility:
```
logger.info(f"Total time: {elapsed:.2f}s, Library time: {lib_time:.2f}s")
```

### Tier 2: WARNING (Anomaly Detection)
Logged when overhead is significant (>2s or >20% of total):
```
logger.warning(f"High overhead: {overhead:.2f}s ({pct:.1f}% of total)")
```

### Tier 3: DEBUG (Diagnostic)
Logged for development/profiling:
```
logger.debug(f"Detailed timing: total={elapsed:.2f}s, library={lib_time:.2f}s, overhead={overhead:.2f}s, {pct:.1f}%")
```

---

## Integration with Existing Logging

### Current Logging in PaperExtractor

```python
class PaperExtractor:
    def extract(self, paper_path: Path, element_types=None):
        logger.info(f"Extracting elements from {paper_path.name} using DocScalpel")

        try:
            extracted_elements = self.adapter.extract(paper_path, element_types)
            # ...existing code...
        except Exception as e:
            logger.error(f"Error extracting elements from {paper_path}: {e}", exc_info=True)
            return []
```

### Logging Stack

```
┌─ PaperExtractor.extract()
│  ├─ logger.info("Extracting elements from paper.pdf...")
│  │
│  └─ adapter.extract() → DocScalpelAdapter
│     ├─ logger.info("Extracting elements from paper.pdf using DocScalpel...")
│     ├─ logger.error("DocScalpel extraction failed...") [if error]
│     ├─ logger.warning("DocScalpel reported X warning(s)")
│     └─ logger.info("Performance metrics...")
│
└─ Back to PaperExtractor
   ├─ logger.info("Extracted X elements, Y passed confidence threshold")
   └─ logger.error("Error extracting elements...") [if exception]
```

### Log Aggregation View

When viewing logs, you'll see:

```
2024-01-15 10:22:34 INFO  [PaperExtractor]     Extracting elements from paper.pdf...
2024-01-15 10:22:34 INFO  [DocScalpelAdapter] Extracting elements from paper.pdf using DocScalpel...
2024-01-15 10:22:37 INFO  [DocScalpelAdapter] DocScalpel extraction succeeded for paper.pdf
2024-01-15 10:22:37 WARNING [DocScalpelAdapter] DocScalpel reported 1 warning(s):
2024-01-15 10:22:37 WARNING [DocScalpelAdapter]   [1/1] Confidence score below threshold
2024-01-15 10:22:37 INFO   [DocScalpelAdapter] Performance metrics for paper.pdf: total=3.45s, library=3.34s
2024-01-15 10:22:37 INFO   [DocScalpelAdapter] Successfully converted 5 element(s) from paper.pdf: 3 figures, 2 tables
2024-01-15 10:22:37 INFO   [PaperExtractor]     Extracted 5 elements, 5 passed confidence threshold
```

---

## Structured Logging (JSON Format)

For log aggregation systems (ELK Stack, Datadog, etc.):

```json
{
  "timestamp": "2024-01-15T10:22:37.123Z",
  "level": "INFO",
  "logger": "paperdeck.extraction.docscalpel_adapter",
  "message": "Extracting elements from paper.pdf using DocScalpel...",
  "pdf_file": "paper.pdf",
  "operation": "extract",
  "module": "docscalpel_adapter",
  "function": "extract",
  "line": 95
}
```

Error with structured context:

```json
{
  "timestamp": "2024-01-15T10:22:40.456Z",
  "level": "ERROR",
  "logger": "paperdeck.extraction.docscalpel_adapter",
  "message": "DocScalpel extraction failed for paper.pdf",
  "pdf_file": "paper.pdf",
  "error_count": 2,
  "errors": [
    "PDF parsing error at page 5",
    "Insufficient memory for large image"
  ],
  "extraction_time_seconds": 3.15,
  "module": "docscalpel_adapter",
  "function": "_handle_extraction_result",
  "line": 180
}
```

---

## Logging Configuration Recommendations

### Development Environment
```python
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Production Environment
```python
import logging.handlers

handler = logging.handlers.RotatingFileHandler(
    'paperdeck.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
handler.setLevel(logging.INFO)  # Only INFO+ in production
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)
logging.getLogger().addHandler(handler)
```

### Testing Environment
```python
import logging

# Capture logs for assertions
@pytest.fixture
def caplog_info(caplog):
    caplog.set_level(logging.INFO)
    return caplog

def test_extraction_error_logging(caplog_info):
    # Verify ERROR level was used, not WARNING
    error_logs = [r for r in caplog_info.records if r.levelno >= logging.ERROR]
    assert len(error_logs) > 0
```

---

## Monitoring & Alerting Rules

### Log-Based Alerts

```
1. ERROR frequency spike
   - Pattern: Count ERROR logs from DocScalpelAdapter
   - Alert: > 5 ERRORs in 5 minutes
   - Action: Check for PDF format issues or library bugs

2. High overhead detection
   - Pattern: Match "High overhead" in logs
   - Alert: Any match
   - Action: Investigate I/O or configuration issues

3. Library unavailability
   - Pattern: Match "DocScalpel not available"
   - Alert: First occurrence in session
   - Action: Ensure proper installation/dependencies

4. Partial extraction
   - Pattern: Match "Returned X partial results despite extraction failure"
   - Alert: Track ratio of partial results
   - Action: Monitor extraction quality
```

---

## Summary

The updated DocScalpelAdapter uses a **tiered logging approach**:

1. **Layer 1 (Public Interface)**: High-level status (extract succeeded/failed)
2. **Layer 2 (Error Details)**: Individual error/warning messages with context
3. **Layer 3 (Performance)**: Timing metrics (operational and diagnostic)
4. **Layer 4 (Conversion)**: Element-level error handling with resilience

This provides:
- **Visibility**: Operational teams see key events (INFO level)
- **Debuggability**: Developers see detailed errors and warnings
- **Observability**: Metrics for performance monitoring
- **Resilience**: Graceful degradation with clear logging

