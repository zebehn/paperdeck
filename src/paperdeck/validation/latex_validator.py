"""LaTeX structure validation for beamer presentations.

This module provides the main validation logic for detecting structural errors
in LaTeX beamer documents.
"""

from pathlib import Path
from typing import List, Optional

from .environment_matcher import EnvironmentMatcher
from .validation_errors import ValidationError, ValidationResult, ERROR_MESSAGES, SUGGESTED_FIXES


class ValidationConfig:
    """Configuration for LaTeX validation.

    Attributes:
        environments: List of environment names to validate
        strict_mode: If True, treat warnings as errors
    """

    def __init__(
        self,
        environments: Optional[List[str]] = None,
        strict_mode: bool = False
    ):
        """Initialize validation configuration.

        Args:
            environments: List of environment names to validate.
                         If None, uses default from EnvironmentMatcher.
            strict_mode: If True, warnings are treated as errors
        """
        self.environments = environments
        self.strict_mode = strict_mode


class LaTeXValidator:
    """Validates LaTeX structure for beamer presentations.

    This validator checks for:
    - Missing \\end{...} tags
    - Unmatched \\begin{...} / \\end{...} pairs
    - Duplicate environment blocks
    """

    def __init__(self, config: Optional[ValidationConfig] = None):
        """Initialize LaTeX validator.

        Args:
            config: Validation configuration. If None, uses defaults.
        """
        self.config = config or ValidationConfig()
        self.matcher = EnvironmentMatcher(environments=self.config.environments)

    def validate_file(self, tex_path: Path) -> ValidationResult:
        """Validate a .tex file.

        Args:
            tex_path: Path to the .tex file to validate

        Returns:
            ValidationResult with any detected errors

        Raises:
            FileNotFoundError: If tex_path does not exist
            IOError: If file cannot be read
        """
        if not tex_path.exists():
            raise FileNotFoundError(f"LaTeX file not found: {tex_path}")

        try:
            content = tex_path.read_text(encoding='utf-8')
            return self.validate_content(content)
        except Exception as e:
            raise IOError(f"Failed to read LaTeX file {tex_path}: {e}")

    def validate_content(self, content: str) -> ValidationResult:
        """Validate LaTeX content string.

        Args:
            content: LaTeX source code as string

        Returns:
            ValidationResult with any detected errors
        """
        lines = content.splitlines()

        # Check for environment matching errors
        matching_errors = self._check_environment_matching(lines)

        # Check for duplicate blocks
        duplicate_errors = self._check_duplicates(lines)

        # Check for HTML/XML syntax (CRITICAL - prevents compilation failures)
        html_syntax_errors = self._check_html_syntax(lines)

        # Combine all errors
        all_errors = matching_errors + duplicate_errors + html_syntax_errors

        # Sort errors by line number
        all_errors.sort(key=lambda e: e.line_number)

        is_valid = len(all_errors) == 0

        return ValidationResult(
            is_valid=is_valid,
            errors=all_errors,
            warnings=[]  # Future: add warning-level checks
        )

    def _check_environment_matching(self, lines: List[str]) -> List[ValidationError]:
        """Check for matched begin/end pairs.

        Args:
            lines: List of LaTeX file lines

        Returns:
            List of ValidationError objects for unmatched tags
        """
        errors = []
        unmatched = self.matcher.find_unmatched(lines)

        for um in unmatched:
            if um.tag_type == 'begin':
                # Missing \\end{...} tag
                error_type = 'missing_end'
                message = ERROR_MESSAGES[error_type].format(
                    env=um.environment,
                    start_line=um.line_number
                )
                suggested_fix = SUGGESTED_FIXES[error_type].format(env=um.environment)

                errors.append(
                    ValidationError(
                        line_number=um.line_number,
                        error_type=error_type,
                        environment=um.environment,
                        message=message,
                        suggested_fix=suggested_fix,
                        severity='error'
                    )
                )
            else:
                # Unmatched \\end{...} tag
                error_type = 'unmatched_end'
                message = ERROR_MESSAGES[error_type].format(env=um.environment)
                suggested_fix = SUGGESTED_FIXES[error_type].format(env=um.environment)

                errors.append(
                    ValidationError(
                        line_number=um.line_number,
                        error_type=error_type,
                        environment=um.environment,
                        message=message,
                        suggested_fix=suggested_fix,
                        severity='error'
                    )
                )

        return errors

    def _check_duplicates(self, lines: List[str]) -> List[ValidationError]:
        """Check for duplicate environment blocks.

        Args:
            lines: List of LaTeX file lines

        Returns:
            List of ValidationError objects for detected duplicates
        """
        errors = []
        duplicates = self.matcher.find_duplicates(lines)

        for dup in duplicates:
            error_type = 'duplicate_block'
            message = ERROR_MESSAGES[error_type].format(env=dup.environment)
            message += f" (previous at line {dup.previous_line})"
            suggested_fix = SUGGESTED_FIXES[error_type].format(env=dup.environment)

            errors.append(
                ValidationError(
                    line_number=dup.line_number,
                    error_type=error_type,
                    environment=dup.environment,
                    message=message,
                    suggested_fix=suggested_fix,
                    severity='error'
                )
            )

        return errors

    def _check_html_syntax(self, lines: List[str]) -> List[ValidationError]:
        """Check for HTML/XML syntax instead of LaTeX syntax.

        Detects common errors like:
        - </end{...}> instead of \\end{...}
        - <tag> instead of \\tag
        - Wrong closing tag formats

        Args:
            lines: List of LaTeX file lines

        Returns:
            List of ValidationError objects for detected HTML syntax
        """
        import re
        errors = []

        # Patterns to detect HTML/XML syntax
        html_patterns = [
            (r'</end\{[^}]+\}>', 'html_closing_tag',
             'HTML closing tag found: "{match}". Use LaTeX syntax: \\end{{...}}'),
            (r'<end\{[^}]+\}>', 'html_opening_tag',
             'HTML tag found: "{match}". Use LaTeX syntax: \\end{{...}}'),
            (r'</[a-zA-Z]+>', 'html_xml_tag',
             'HTML/XML closing tag found: "{match}". Use LaTeX syntax with backslash: \\end{{...}}'),
            (r'<begin\{[^}]+\}>', 'html_begin_tag',
             'HTML tag found: "{match}". Use LaTeX syntax: \\begin{{...}}'),
        ]

        for line_num, line in enumerate(lines, start=1):
            # Skip comment lines
            if line.strip().startswith('%'):
                continue

            for pattern, error_type, message_template in html_patterns:
                matches = re.finditer(pattern, line)
                for match in matches:
                    matched_text = match.group(0)

                    # Determine correct LaTeX syntax
                    if 'end' in matched_text.lower():
                        # Extract environment name if possible
                        env_match = re.search(r'\{([^}]+)\}', matched_text)
                        if env_match:
                            env_name = env_match.group(1)
                            suggested_fix = f'Replace with: \\end{{{env_name}}}'
                        else:
                            suggested_fix = 'Replace with: \\end{environment_name}'
                    elif 'begin' in matched_text.lower():
                        env_match = re.search(r'\{([^}]+)\}', matched_text)
                        if env_match:
                            env_name = env_match.group(1)
                            suggested_fix = f'Replace with: \\begin{{{env_name}}}'
                        else:
                            suggested_fix = 'Replace with: \\begin{environment_name}'
                    else:
                        suggested_fix = 'Use LaTeX syntax with backslash (\\) instead of angle brackets'

                    errors.append(
                        ValidationError(
                            line_number=line_num,
                            error_type=error_type,
                            environment='html_syntax',
                            message=message_template.format(match=matched_text),
                            suggested_fix=suggested_fix,
                            severity='error'
                        )
                    )

        return errors
