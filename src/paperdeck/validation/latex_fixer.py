"""Automatic fixing of LaTeX structural errors.

This module provides functionality to automatically fix common LaTeX structural
errors detected during validation.
"""

import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

from .validation_errors import ValidationError, FixChange


@dataclass
class FixerConfig:
    """Configuration for LaTeX auto-fix.

    Attributes:
        max_fixes_per_file: Maximum number of fixes to apply per file (safety limit)
        preserve_formatting: Whether to preserve original indentation and formatting
        fix_missing_ends: Enable fixing of missing \\end{...} tags
        fix_duplicates: Enable fixing of duplicate blocks
    """

    max_fixes_per_file: int = 50
    preserve_formatting: bool = True
    fix_missing_ends: bool = True
    fix_duplicates: bool = True


class LaTeXFixer:
    """Automatically fixes common LaTeX structural errors.

    This fixer can:
    - Add missing \\end{...} tags
    - Remove duplicate environment blocks
    - Log all changes made
    """

    def __init__(self, config: Optional[FixerConfig] = None):
        """Initialize LaTeX fixer.

        Args:
            config: Fixer configuration. If None, uses defaults.
        """
        self.config = config or FixerConfig()
        self.changes_log: List[FixChange] = []

    def fix_validation_errors(
        self,
        content: str,
        errors: List[ValidationError]
    ) -> Tuple[str, List[FixChange]]:
        """Apply fixes for validation errors.

        Args:
            content: Original LaTeX content
            errors: List of validation errors to fix

        Returns:
            Tuple of (fixed_content, changes_log)
        """
        self.changes_log = []
        lines = content.splitlines(keepends=True)

        # Sort errors by line number (descending) to avoid line number shifts
        sorted_errors = sorted(errors, key=lambda e: e.line_number, reverse=True)

        # Track how many fixes we've applied
        fixes_applied = 0

        for error in sorted_errors:
            if fixes_applied >= self.config.max_fixes_per_file:
                break

            if error.error_type == 'missing_end' and self.config.fix_missing_ends:
                lines, changed = self._add_missing_end(lines, error)
                if changed:
                    fixes_applied += 1

            elif error.error_type == 'duplicate_block' and self.config.fix_duplicates:
                lines, changed = self._remove_duplicate(lines, error)
                if changed:
                    fixes_applied += 1

        # Reconstruct content
        fixed_content = ''.join(lines)
        return fixed_content, self.changes_log

    def _add_missing_end(
        self,
        lines: List[str],
        error: ValidationError
    ) -> Tuple[List[str], bool]:
        """Add missing \\end{...} tag.

        Args:
            lines: List of file lines (with line endings)
            error: ValidationError with missing_end type

        Returns:
            Tuple of (modified_lines, was_changed)
        """
        # Find the line with the unmatched \\begin{...}
        begin_line_idx = error.line_number - 1

        if begin_line_idx >= len(lines):
            return lines, False

        # Determine indentation from the begin line
        begin_line = lines[begin_line_idx]
        indent = len(begin_line) - len(begin_line.lstrip())
        indent_str = begin_line[:indent]

        # Find where to insert the \\end{...}
        # Strategy: Look for the next environment begin/end or end of file
        insert_idx = self._find_insertion_point(lines, begin_line_idx, error.environment)

        # Create the end tag with proper indentation
        end_tag = f"{indent_str}\\end{{{error.environment}}}\n"

        # Insert the end tag
        lines.insert(insert_idx, end_tag)

        # Log the change
        self.changes_log.append(
            FixChange(
                line_number=insert_idx + 1,  # Convert to 1-indexed
                fix_type='add_missing_end',
                environment=error.environment,
                description=f"Added missing \\end{{{error.environment}}} tag",
                before=None,
                after=end_tag.strip()
            )
        )

        return lines, True

    def _find_insertion_point(
        self,
        lines: List[str],
        begin_idx: int,
        environment: str
    ) -> int:
        """Find appropriate insertion point for missing \\end{...} tag.

        Args:
            lines: List of file lines
            begin_idx: Index of the \\begin{...} line
            environment: Environment name

        Returns:
            Line index where \\end{...} should be inserted
        """
        # Look for the next begin of a different environment or end of current scope
        env_pattern = re.compile(r'\\(begin|end)\{([^}]+)\}')

        for idx in range(begin_idx + 1, len(lines)):
            match = env_pattern.search(lines[idx])
            if match:
                tag_type, env_name = match.groups()
                # If we hit a begin of different environment or an end, insert before it
                if tag_type == 'begin' or tag_type == 'end':
                    return idx

        # If no suitable point found, insert at end
        return len(lines)

    def _remove_duplicate(
        self,
        lines: List[str],
        error: ValidationError
    ) -> Tuple[List[str], bool]:
        """Remove duplicate environment block.

        Args:
            lines: List of file lines (with line endings)
            error: ValidationError with duplicate_block type

        Returns:
            Tuple of (modified_lines, was_changed)
        """
        # The duplicate is at error.line_number
        dup_line_idx = error.line_number - 1

        if dup_line_idx >= len(lines) or dup_line_idx < 0:
            return lines, False

        # Find the matching \\end{...} for this duplicate begin
        end_idx = self._find_matching_end(lines, dup_line_idx, error.environment)

        if end_idx is None:
            # Just remove the begin line if no matching end
            removed_content = lines[dup_line_idx]
            del lines[dup_line_idx]

            self.changes_log.append(
                FixChange(
                    line_number=error.line_number,
                    fix_type='remove_duplicate',
                    environment=error.environment,
                    description=f"Removed duplicate \\begin{{{error.environment}}} tag",
                    before=removed_content.strip(),
                    after=None
                )
            )
            return lines, True

        # Remove the entire duplicate block (begin to end, inclusive)
        removed_lines = lines[dup_line_idx:end_idx + 1]
        removed_content = ''.join(removed_lines)

        del lines[dup_line_idx:end_idx + 1]

        self.changes_log.append(
            FixChange(
                line_number=error.line_number,
                fix_type='remove_duplicate',
                environment=error.environment,
                description=f"Removed duplicate \\begin{{{error.environment}}} block (lines {error.line_number}-{end_idx + 1})",
                before=removed_content.strip(),
                after=None
            )
        )

        return lines, True

    def _find_matching_end(
        self,
        lines: List[str],
        begin_idx: int,
        environment: str
    ) -> Optional[int]:
        """Find the matching \\end{...} for a \\begin{...}.

        Args:
            lines: List of file lines
            begin_idx: Index of the \\begin{...} line
            environment: Environment name

        Returns:
            Index of matching \\end{...}, or None if not found
        """
        begin_pattern = re.compile(rf'\\begin\{{{re.escape(environment)}\}}')
        end_pattern = re.compile(rf'\\end\{{{re.escape(environment)}\}}')

        depth = 1  # Start with depth 1 (we're at a begin)

        for idx in range(begin_idx + 1, len(lines)):
            if begin_pattern.search(lines[idx]):
                depth += 1
            elif end_pattern.search(lines[idx]):
                depth -= 1
                if depth == 0:
                    return idx

        return None

    def get_changes_log(self) -> List[FixChange]:
        """Get log of all changes made.

        Returns:
            List of FixChange objects describing each fix applied
        """
        return self.changes_log.copy()

    def clear_log(self) -> None:
        """Clear the changes log."""
        self.changes_log = []
