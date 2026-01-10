"""Automatic fixing of LaTeX structural errors.

This module provides functionality to automatically fix common LaTeX structural
errors detected during validation.
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from .backup_manager import BackupManager, BackupMetadata
from .error_types import ErrorType
from .validation_errors import ValidationError, FixChange


@dataclass
class FixerConfig:
    """Configuration for LaTeX auto-fix.

    Attributes:
        max_fixes_per_file: Maximum number of fixes to apply per file (safety limit)
        preserve_formatting: Whether to preserve original indentation and formatting
        fix_missing_ends: Enable fixing of missing \\end{...} tags
        fix_duplicates: Enable fixing of duplicate blocks
        fix_missing_braces: Auto-fix missing closing braces
        fix_extra_braces: Auto-fix extra closing braces
        fix_html_syntax: Auto-fix HTML/XML syntax
        fix_unmatched_brackets: Auto-fix unmatched brackets
        fix_unmatched_parens: Auto-fix unmatched parentheses
        fix_nesting_errors: Auto-fix nesting errors
        confidence_threshold: Minimum confidence for auto-fix (0.0-1.0)
        create_backup: Create backup before fixing
        backup_dir: Backup directory
        max_retry_attempts: Max compilation retries
        retry_on_failure: Retry if compilation fails
    """

    max_fixes_per_file: int = 50
    preserve_formatting: bool = True
    fix_missing_ends: bool = True
    fix_duplicates: bool = True

    # New fields for delimiter fixing
    fix_missing_braces: bool = True
    fix_extra_braces: bool = True
    fix_html_syntax: bool = True
    fix_unmatched_brackets: bool = False  # Report only by default
    fix_unmatched_parens: bool = False    # Report only by default
    fix_nesting_errors: bool = False       # Report only (complex)

    # New fields for safety
    confidence_threshold: float = 0.80  # Min confidence for auto-fix
    create_backup: bool = True          # Create backup before fixing (FR-008)
    backup_dir: str = ".backup"         # Backup directory

    # New fields for retry behavior (FR-013)
    max_retry_attempts: int = 3
    retry_on_failure: bool = True

    @classmethod
    def safe(cls) -> 'FixerConfig':
        """Conservative fixing configuration."""
        return cls(
            max_fixes_per_file=10,  # Low limit
            confidence_threshold=0.90,  # High threshold
            fix_missing_braces=True,
            fix_extra_braces=False,  # Don't remove braces
            fix_unmatched_brackets=False,
            fix_unmatched_parens=False,
            create_backup=True,
        )

    @classmethod
    def aggressive(cls) -> 'FixerConfig':
        """Aggressive fixing configuration."""
        return cls(
            max_fixes_per_file=100,
            confidence_threshold=0.70,  # Lower threshold
            fix_missing_braces=True,
            fix_extra_braces=True,
            fix_unmatched_brackets=True,  # Fix brackets too
            fix_html_syntax=True,
            create_backup=True,
        )


class LaTeXFixer:
    """Automatically fixes common LaTeX structural errors.

    This fixer can:
    - Add missing \\end{...} tags
    - Remove duplicate environment blocks
    - Fix delimiter errors
    - Create backups before applying fixes
    - Log all changes made
    """

    def __init__(
        self,
        config: Optional[FixerConfig] = None,
        backup_manager: Optional[BackupManager] = None
    ):
        """Initialize LaTeX fixer.

        Args:
            config: Fixer configuration. If None, uses defaults.
            backup_manager: Backup manager for creating file backups. If None and
                          config.create_backup is True, creates default BackupManager.
        """
        self.config = config or FixerConfig()
        self.changes_log: List[FixChange] = []
        self.last_backup: Optional[BackupMetadata] = None

        # Initialize backup manager if needed
        if self.config.create_backup:
            if backup_manager is None:
                self.backup_manager = BackupManager(backup_dir=self.config.backup_dir)
            else:
                self.backup_manager = backup_manager
        else:
            self.backup_manager = None

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

            # Check confidence threshold
            if error.fix_confidence < self.config.confidence_threshold:
                continue  # Skip low-confidence fixes

            if error.error_type == 'missing_end' and self.config.fix_missing_ends:
                lines, changed = self._add_missing_end(lines, error)
                if changed:
                    fixes_applied += 1

            elif error.error_type == 'duplicate_block' and self.config.fix_duplicates:
                lines, changed = self._remove_duplicate(lines, error)
                if changed:
                    fixes_applied += 1

            elif error.error_type == ErrorType.UNMATCHED_BRACE_OPEN.value and self.config.fix_missing_braces:
                lines, changed = self._fix_missing_closing_brace(lines, error)
                if changed:
                    fixes_applied += 1

            elif error.error_type == ErrorType.UNMATCHED_BRACE_CLOSE.value and self.config.fix_extra_braces:
                lines, changed = self._fix_extra_closing_brace(lines, error)
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

    def _fix_missing_closing_brace(
        self,
        lines: List[str],
        error: ValidationError
    ) -> Tuple[List[str], bool]:
        """Fix missing closing brace.

        Args:
            lines: List of file lines (with line endings)
            error: ValidationError with unmatched_brace_open type

        Returns:
            Tuple of (modified_lines, was_changed)
        """
        line_idx = error.line_number - 1

        if line_idx >= len(lines) or line_idx < 0:
            return lines, False

        # Get the line content
        line = lines[line_idx]
        has_newline = line.endswith('\n')

        # Strategy: Add closing brace at end of line (simple heuristic)
        # More sophisticated: find logical end point (before next command, etc.)
        if has_newline:
            fixed_line = line.rstrip('\n') + '}' + '\n'
        else:
            fixed_line = line + '}'

        before_content = line.strip()
        after_content = fixed_line.strip()

        lines[line_idx] = fixed_line

        # Log the change
        self.changes_log.append(
            FixChange(
                line_number=error.line_number,
                column_number=error.column_number,
                fix_type='fix_missing_closing_brace',
                environment='',
                description='Added missing closing brace',
                before=before_content,
                after=after_content,
                confidence=error.fix_confidence,
                lines_modified=1
            )
        )

        return lines, True

    def _fix_extra_closing_brace(
        self,
        lines: List[str],
        error: ValidationError
    ) -> Tuple[List[str], bool]:
        """Fix extra closing brace by removing it.

        Args:
            lines: List of file lines (with line endings)
            error: ValidationError with unmatched_brace_close type

        Returns:
            Tuple of (modified_lines, was_changed)
        """
        line_idx = error.line_number - 1

        if line_idx >= len(lines) or line_idx < 0:
            return lines, False

        line = lines[line_idx]

        # Remove the brace at the specified column
        # column_number is 1-indexed
        col = error.column_number - 1

        if col < 0 or col >= len(line):
            return lines, False

        # Verify it's actually a closing brace
        if line[col] != '}':
            # Column might not be accurate, try to find the extra brace
            # For now, return unchanged
            return lines, False

        # Remove the brace
        fixed_line = line[:col] + line[col + 1:]

        before_content = line.strip()
        after_content = fixed_line.strip()

        lines[line_idx] = fixed_line

        # Log the change
        self.changes_log.append(
            FixChange(
                line_number=error.line_number,
                column_number=error.column_number,
                fix_type='fix_extra_closing_brace',
                environment='',
                description='Removed extra closing brace',
                before=before_content,
                after=after_content,
                confidence=error.fix_confidence,
                lines_modified=1
            )
        )

        return lines, True

    def fix_file(
        self,
        file_path: Path,
        errors: List[ValidationError],
        in_place: bool = True
    ) -> Tuple[str, List[FixChange], Optional[BackupMetadata]]:
        """Fix validation errors in a file with automatic backup.

        Args:
            file_path: Path to LaTeX file to fix
            errors: List of validation errors to fix
            in_place: If True, modifies file in place. If False, returns fixed content only.

        Returns:
            Tuple of (fixed_content, changes_log, backup_metadata)

        Raises:
            FileNotFoundError: If file does not exist
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Create backup if enabled
        backup_metadata = None
        if self.config.create_backup and self.backup_manager:
            backup_metadata = self.backup_manager.create_backup(file_path)
            self.last_backup = backup_metadata

        # Read file content
        content = file_path.read_text(encoding='utf-8')

        # Apply fixes
        fixed_content, changes = self.fix_validation_errors(content, errors)

        # Write back if in_place
        if in_place and changes:  # Only write if changes were made
            file_path.write_text(fixed_content, encoding='utf-8')

        return fixed_content, changes, backup_metadata

    def get_changes_log(self) -> List[FixChange]:
        """Get log of all changes made.

        Returns:
            List of FixChange objects describing each fix applied
        """
        return self.changes_log.copy()

    def get_last_backup(self) -> Optional[BackupMetadata]:
        """Get metadata for the last backup created.

        Returns:
            BackupMetadata object or None if no backup was created
        """
        return self.last_backup

    def clear_log(self) -> None:
        """Clear the changes log."""
        self.changes_log = []
        self.last_backup = None
