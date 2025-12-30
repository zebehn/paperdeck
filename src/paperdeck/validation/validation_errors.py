"""Data models for LaTeX validation errors and results."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ValidationError:
    """Represents a LaTeX structural error.

    Attributes:
        line_number: Line number where error was detected (1-indexed)
        error_type: Type of error ('missing_end', 'duplicate_block', 'unmatched_begin')
        environment: LaTeX environment name ('frame', 'column', 'columns', etc.)
        message: Human-readable error description
        suggested_fix: Suggestion for how to fix the error
        severity: Error severity level ('error' or 'warning')
    """

    line_number: int
    error_type: str
    environment: str
    message: str
    suggested_fix: str
    severity: str = "error"

    def __str__(self) -> str:
        """Format error as human-readable string."""
        return f"Line {self.line_number}: {self.message}\n  Suggested fix: {self.suggested_fix}"


@dataclass
class ValidationResult:
    """Result of LaTeX validation.

    Attributes:
        is_valid: True if no errors were found
        errors: List of validation errors
        warnings: List of validation warnings
    """

    is_valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)

    def has_errors(self) -> bool:
        """Check if validation found any errors."""
        return len(self.errors) > 0

    def has_warnings(self) -> bool:
        """Check if validation found any warnings."""
        return len(self.warnings) > 0

    def error_count(self) -> int:
        """Get total number of errors."""
        return len(self.errors)

    def warning_count(self) -> int:
        """Get total number of warnings."""
        return len(self.warnings)

    def __str__(self) -> str:
        """Format validation result as human-readable string."""
        if self.is_valid:
            return "Validation passed: No errors found"

        lines = [f"Validation failed: {self.error_count()} error(s) found\n"]

        if self.errors:
            lines.append("Errors:")
            for error in self.errors:
                lines.append(f"  {error}")

        if self.warnings:
            lines.append(f"\nWarnings ({self.warning_count()}):")
            for warning in self.warnings:
                lines.append(f"  {warning}")

        return "\n".join(lines)


@dataclass
class FixChange:
    """Represents a change made by auto-fix.

    Attributes:
        line_number: Line number where change was made (1-indexed)
        fix_type: Type of fix applied ('add_missing_end', 'remove_duplicate', etc.)
        environment: LaTeX environment affected
        description: Human-readable description of the change
        before: Content before the fix (optional)
        after: Content after the fix (optional)
    """

    line_number: int
    fix_type: str
    environment: str
    description: str
    before: Optional[str] = None
    after: Optional[str] = None

    def __str__(self) -> str:
        """Format fix change as human-readable string."""
        msg = f"Line {self.line_number}: {self.description}"
        if self.before and self.after:
            msg += f"\n  Before: {self.before}\n  After: {self.after}"
        return msg


# Error message templates
ERROR_MESSAGES = {
    "missing_end": "Missing \\end{{{env}}} tag for environment started at line {start_line}",
    "unmatched_begin": "Unmatched \\begin{{{env}}} tag - no corresponding \\end{{{env}}}",
    "unmatched_end": "Unmatched \\end{{{env}}} tag - no corresponding \\begin{{{env}}}",
    "duplicate_block": "Duplicate \\begin{{{env}}} block detected",
}

SUGGESTED_FIXES = {
    "missing_end": "Add \\end{{{env}}} tag before the next environment or at end of frame",
    "unmatched_begin": "Add \\end{{{env}}} tag or remove \\begin{{{env}}}",
    "unmatched_end": "Add \\begin{{{env}}} tag or remove \\end{{{env}}}",
    "duplicate_block": "Remove the duplicate \\begin{{{env}}} block",
}
