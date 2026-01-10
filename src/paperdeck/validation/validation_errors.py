"""Data models for LaTeX validation errors and results."""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set


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
        column_number: Character position in line (1-indexed)
        line_content: The actual line content for context
        error_context: Surrounding lines for context (±2 lines)
        fix_confidence: Confidence in suggested fix (0.0-1.0)
        auto_fixable: Whether fix can be applied automatically
        related_errors: Related error line numbers
        parent_error_line: Line number of parent error (for cascading)
    """

    line_number: int
    error_type: str
    environment: str
    message: str
    suggested_fix: str
    severity: str = "error"

    # New fields for enhanced reporting (FR-010)
    column_number: Optional[int] = None
    line_content: Optional[str] = None
    error_context: Optional[List[str]] = None

    # New fields for auto-fix decision (FR-005, SC-003, SC-006)
    fix_confidence: float = 0.0
    auto_fixable: bool = False

    # New fields for error relationships
    related_errors: List[int] = field(default_factory=list)
    parent_error_line: Optional[int] = None

    def __str__(self) -> str:
        """Format error as human-readable string with column number and context."""
        result = f"Line {self.line_number}"
        if self.column_number:
            result += f", Column {self.column_number}"
        result += f": {self.message}"

        if self.line_content:
            result += f"\n  > {self.line_content.rstrip()}"
            if self.column_number and self.column_number <= len(self.line_content):
                # Add caret indicator
                indent = "    "
                caret_pos = self.column_number - 1
                result += f"\n{indent}{' ' * caret_pos}^"

        result += f"\n  Suggested fix: {self.suggested_fix}"

        if self.auto_fixable and self.fix_confidence > 0:
            result += f" (auto-fixable with {self.fix_confidence:.0%} confidence)"

        return result


@dataclass
class ValidationResult:
    """Result of LaTeX validation.

    Attributes:
        is_valid: True if no errors were found
        errors: List of validation errors
        warnings: List of validation warnings
        file_path: Path to validated file
        validation_time: Seconds taken for validation
        total_lines: Total lines in file
        auto_fixable_count: Number of errors that can be auto-fixed
        manual_fix_count: Number of errors requiring manual fixes
        error_types_count: Dictionary mapping error_type to count
        affected_lines: Set of unique line numbers with errors
    """

    is_valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)

    # New fields for reporting (FR-009, FR-010)
    file_path: Optional[Path] = None
    validation_time: float = 0.0
    total_lines: int = 0

    # New fields for statistics (SC-004)
    auto_fixable_count: int = 0
    manual_fix_count: int = 0
    error_types_count: Dict[str, int] = field(default_factory=dict)
    affected_lines: Set[int] = field(default_factory=set)

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

    def get_auto_fixable_errors(self) -> List[ValidationError]:
        """Get only errors that can be auto-fixed."""
        return [e for e in self.errors if e.auto_fixable]

    def get_manual_fix_errors(self) -> List[ValidationError]:
        """Get only errors requiring manual fixes."""
        return [e for e in self.errors if not e.auto_fixable]

    def group_by_type(self) -> Dict[str, List[ValidationError]]:
        """Group errors by error_type for organized reporting."""
        groups: Dict[str, List[ValidationError]] = {}
        for error in self.errors:
            if error.error_type not in groups:
                groups[error.error_type] = []
            groups[error.error_type].append(error)
        return groups

    def get_summary(self) -> str:
        """Generate one-line summary of validation results."""
        if self.is_valid:
            return f"✓ LaTeX is valid ({self.total_lines} lines, {self.validation_time:.2f}s)"

        auto = self.auto_fixable_count
        manual = self.manual_fix_count
        return f"✗ Found {len(self.errors)} error(s): {auto} auto-fixable, {manual} manual ({self.validation_time:.2f}s)"

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
        column_number: Character position where fix applied
        confidence: Confidence score for this fix (0.0-1.0)
        timestamp: When fix was applied (ISO format)
        lines_added: Number of lines added
        lines_removed: Number of lines removed
        lines_modified: Number of lines changed
    """

    line_number: int
    fix_type: str
    environment: str
    description: str
    before: Optional[str] = None
    after: Optional[str] = None

    # New fields for enhanced tracking
    column_number: Optional[int] = None
    confidence: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    # New fields for diff generation (FR-015)
    lines_added: int = 0
    lines_removed: int = 0
    lines_modified: int = 0

    def __str__(self) -> str:
        """Format fix change as human-readable string."""
        msg = f"Line {self.line_number}: {self.description}"
        if self.before and self.after:
            msg += f"\n  Before: {self.before}\n  After: {self.after}"
        return msg

    def to_diff_format(self) -> str:
        """Generate unified diff format for this change."""
        lines = []
        lines.append(f"@@ -{self.line_number} +{self.line_number} @@ {self.description}")

        if self.before:
            lines.append(f"- {self.before}")
        if self.after:
            lines.append(f"+ {self.after}")

        return '\n'.join(lines)


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
