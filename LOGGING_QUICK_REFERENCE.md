# Python Logging Quick Reference: Third-Party Library Integration

## TL;DR - Copy-Paste Ready Patterns

### Pattern 1: Import with Graceful Degradation

```python
import logging

logger = logging.getLogger(__name__)

try:
    import third_party_lib
    LIBRARY_AVAILABLE = True
    logger.info("Third-party library loaded")
except ImportError:
    LIBRARY_AVAILABLE = False
    logger.warning("Third-party library not available. Feature disabled.")
```

### Pattern 2: Handle Result with Errors/Warnings

```python
# WRONG - uses WARNING for failures
if not result.success:
    logger.warning(f"Failed: {result.errors}")  # ❌

# RIGHT - uses ERROR for failures
if not result.success:
    logger.error(f"Extraction failed")
    for i, error in enumerate(result.errors, 1):
        logger.error(f"  [{i}/{len(result.errors)}] {error}")

# Log warnings at WARNING level (even if success=True)
if result.warnings:
    logger.warning(f"Reported {len(result.warnings)} warning(s)")
    for i, warning in enumerate(result.warnings, 1):
        logger.warning(f"  [{i}/{len(result.warnings)}] {warning}")
```

### Pattern 3: Log Performance Metrics

```python
import time

start = time.perf_counter()

result = library.process(data)
library_time = result.extraction_time_seconds
elapsed = time.perf_counter() - start

# Log timing at INFO (operational metric)
logger.info(f"Processing took {elapsed:.2f}s (library: {library_time:.2f}s)")

# Detect overhead at DEBUG level
overhead = elapsed - library_time
logger.debug(f"Overhead: {overhead:.2f}s ({(overhead/elapsed)*100:.1f}%)")

# Warn if significant
if overhead > max(2.0, library_time * 0.2):  # >2s or >20%
    logger.warning(f"High overhead detected: {overhead:.2f}s")
```

### Pattern 4: Graceful Degradation with Empty Return

```python
def extract(self, pdf_path):
    """Always return default value, never raise on library errors."""

    if not self.library_available:
        logger.info("Library unavailable, returning empty results")
        return []

    try:
        result = self.library.process(pdf_path)
        return self._convert(result)
    except Exception as e:
        logger.error(f"Processing failed: {e}", exc_info=True)
        logger.info("Returning empty results due to error")
        return []  # Never raise!
```

---

## Log Level Decision Tree

```
Does the code work as expected?
├─ YES
│  ├─ Just informing user? → INFO
│  │  logger.info("Processing completed successfully")
│  │
│  └─ Performance metric? → INFO (or DEBUG for details)
│     logger.info(f"Processed in {time:.2f}s")
│
└─ NO (something went wrong)
   ├─ Third-party returned success=False? → ERROR
   │  logger.error("Library reported extraction failed")
   │
   ├─ Third-party returned warnings but success=True? → WARNING
   │  logger.warning("Library reported warnings")
   │
   ├─ Exception/unexpected error? → ERROR + exc_info=True
   │  logger.error(f"Unexpected error: {e}", exc_info=True)
   │
   └─ Graceful fallback applied? → INFO
      logger.info("Falling back to empty results")
```

---

## Quick Comparison Table

| Scenario | Logger Level | Example |
|----------|--------------|---------|
| Library import succeeds | INFO | `logger.info("Library loaded")` |
| Library import fails | WARNING | `logger.warning("Library not available")` |
| Operation succeeds | INFO | `logger.info("Extracted 5 items")` |
| Operation returns success=False | ERROR | `logger.error("Operation failed")` |
| Operation returns warnings | WARNING | `logger.warning("Warnings encountered")` |
| Unexpected exception | ERROR | `logger.error("Error: {e}", exc_info=True)` |
| Performance timing | INFO | `logger.info(f"Time: {elapsed:.2f}s")` |
| Performance diagnosis | DEBUG | `logger.debug(f"Overhead: {overhead:.2f}s")` |
| Config disabled feature | INFO | `logger.info("Feature disabled by config")` |
| Graceful degradation | INFO | `logger.info("Falling back to default")` |

---

## Common Mistakes & Fixes

### Mistake 1: Wrong Level for Library Failures

```python
# WRONG ❌
if not result.success:
    logger.warning(f"Extraction failed: {result.errors}")

# RIGHT ✅
if not result.success:
    logger.error(f"Extraction failed: {result.errors}")
```

### Mistake 2: Batch Logging Without Count

```python
# WRONG ❌
for error in result.errors:
    logger.error(error)  # No context!

# RIGHT ✅
for i, error in enumerate(result.errors, 1):
    logger.error(f"  [{i}/{len(result.errors)}] {error}")
```

### Mistake 3: Logging Metrics with Wrong Precision

```python
# WRONG ❌
logger.info(f"Took {elapsed}s")  # Too precise: 2.3421342134s

# RIGHT ✅
logger.info(f"Took {elapsed:.2f}s")  # Clean: 2.34s
```

### Mistake 4: Raising on Library Errors

```python
# WRONG ❌
try:
    result = library.process()
except Exception as e:
    logger.error(f"Failed: {e}")
    raise  # Never!

# RIGHT ✅
try:
    result = library.process()
except Exception as e:
    logger.error(f"Failed: {e}", exc_info=True)
    return []  # Graceful fallback
```

### Mistake 5: Missing exc_info=True for Exceptions

```python
# WRONG ❌
except Exception as e:
    logger.error(f"Failed: {e}")  # No traceback!

# RIGHT ✅
except Exception as e:
    logger.error(f"Failed: {e}", exc_info=True)  # Includes traceback
```

### Mistake 6: INFO Level for Optional Warnings

```python
# WRONG ❌
if result.warnings:
    logger.info(f"Warnings: {result.warnings}")  # Too low level!

# RIGHT ✅
if result.warnings:
    logger.warning(f"Warnings encountered")  # Proper level
    for w in result.warnings:
        logger.warning(f"  - {w}")
```

---

## Code Template: Complete Adapter

```python
import logging
import time
from typing import Optional, List

logger = logging.getLogger(__name__)

class ThirdPartyAdapter:
    """Adapter with proper logging for third-party library."""

    def __init__(self):
        """Initialize with graceful import handling."""
        try:
            import third_party_lib
            self.lib = third_party_lib
            self.available = True
            logger.info("Third-party library loaded successfully")
        except ImportError:
            self.available = False
            logger.warning(
                "Third-party library not available. "
                "Install with: pip install third-party-lib"
            )

    def process(self, data):
        """Process with full error handling and metrics."""
        if not self.available:
            logger.info("Library unavailable, returning None")
            return None

        start_time = time.perf_counter()

        try:
            logger.info(f"Processing started...")
            result = self.lib.process(data)
            elapsed = time.perf_counter() - start_time

            return self._handle_result(result, elapsed)

        except Exception as e:
            elapsed = time.perf_counter() - start_time
            logger.error(
                f"Error during processing (after {elapsed:.2f}s): {e}",
                exc_info=True
            )
            logger.info("Returning None due to error")
            return None

    def _handle_result(self, result, elapsed):
        """Handle result with structured logging."""
        # Log status
        if not result.success:
            logger.error("Processing failed")
            self._log_errors(result.errors)
        else:
            logger.info("Processing succeeded")

        # Log warnings
        if result.warnings:
            self._log_warnings(result.warnings)

        # Log metrics
        self._log_metrics(result, elapsed)

        return result

    def _log_errors(self, errors: Optional[List[str]]):
        """Log errors individually."""
        if not errors:
            return
        for i, error in enumerate(errors, 1):
            logger.error(f"  [{i}/{len(errors)}] {error}")

    def _log_warnings(self, warnings: Optional[List[str]]):
        """Log warnings individually."""
        if not warnings:
            return
        for i, warning in enumerate(warnings, 1):
            logger.warning(f"  [{i}/{len(warnings)}] {warning}")

    def _log_metrics(self, result, elapsed):
        """Log performance metrics."""
        logger.info(
            f"Performance: total={elapsed:.2f}s, "
            f"library={result.execution_time:.2f}s"
        )
        overhead = elapsed - result.execution_time
        if overhead > max(2.0, result.execution_time * 0.2):
            logger.warning(f"High overhead: {overhead:.2f}s")
```

---

## Testing Pattern

```python
import logging
import pytest

def test_errors_logged_at_error_level(caplog):
    """Verify errors use ERROR level."""
    adapter = ThirdPartyAdapter()
    adapter.process_with_errors()

    error_records = [r for r in caplog.records if r.levelno == logging.ERROR]
    assert len(error_records) > 0
    assert any("failed" in r.message.lower() for r in error_records)

def test_warnings_logged_at_warning_level(caplog):
    """Verify warnings use WARNING level."""
    adapter = ThirdPartyAdapter()
    adapter.process_with_warnings()

    warning_records = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(warning_records) > 0
    assert any("warning" in r.message.lower() for r in warning_records)

def test_metrics_included_in_logs(caplog):
    """Verify timing metrics are logged."""
    adapter = ThirdPartyAdapter()
    adapter.process()

    assert any(".2f" in r.message or "s" in r.message for r in caplog.records)
```

---

## Environment/Config Setup

### For Development

```python
# Enable DEBUG logging to see all messages
import logging
logging.basicConfig(level=logging.DEBUG)
```

### For Production

```python
# Disable verbose library logging
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('requests').setLevel(logging.WARNING)
```

### For Log Aggregation (ELK, Datadog, etc.)

```python
# Structured logging formatter
import json
import logging

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        return json.dumps(log_data)

# Use in handler
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
```

---

## Key Takeaways

1. **Import Failures**: WARNING level (expected in some environments)
2. **Operation Failures** (success=False): ERROR level
3. **Warnings** (warnings list): WARNING level (even if success=True)
4. **Metrics**: INFO level for operational, DEBUG for diagnostic
5. **Exceptions**: ERROR level + exc_info=True
6. **Always**: Return default value, never raise on library errors
7. **Always**: Include context (filename, operation, timing)
8. **Always**: Log errors/warnings individually, not as batch
9. **Avoid**: Using WARNING for actual failures (use ERROR)
10. **Avoid**: Missing exc_info=True for exceptions

