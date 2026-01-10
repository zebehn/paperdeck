"""Unit tests for LaTeXFixer."""

import pytest
from src.paperdeck.validation.latex_fixer import LaTeXFixer, FixerConfig
from src.paperdeck.validation.validation_errors import ValidationError


class TestLaTeXFixer:
    """Test cases for LaTeXFixer class."""

    def test_fix_missing_end_simple(self):
        """Test adding missing \\end{...} tag."""
        fixer = LaTeXFixer()
        content = r"""
\begin{frame}
  Content here
\begin{itemize}
  \item Test
"""
        error = ValidationError(
            line_number=3,
            error_type='missing_end',
            environment='frame',
            message="Missing \\end{frame}",
            suggested_fix="Add \\end{frame} tag",
            fix_confidence=1.0  # High confidence for auto-fix
        )

        fixed_content, changes = fixer.fix_validation_errors(content, [error])

        assert r'\end{frame}' in fixed_content
        assert len(changes) == 1
        assert changes[0].fix_type == 'add_missing_end'
        assert changes[0].environment == 'frame'

    def test_fix_multiple_missing_ends(self):
        """Test fixing multiple missing end tags."""
        fixer = LaTeXFixer()
        content = r"""
\begin{frame}
  \begin{itemize}
    \item Test
"""
        errors = [
            ValidationError(
                line_number=2,
                error_type='missing_end',
                environment='frame',
                message="Missing \\end{frame}",
                suggested_fix="Add \\end{frame}",
                fix_confidence=1.0
            ),
            ValidationError(
                line_number=3,
                error_type='missing_end',
                environment='itemize',
                message="Missing \\end{itemize}",
                suggested_fix="Add \\end{itemize}",
                fix_confidence=1.0
            )
        ]

        fixed_content, changes = fixer.fix_validation_errors(content, errors)

        assert r'\end{frame}' in fixed_content
        assert r'\end{itemize}' in fixed_content
        assert len(changes) == 2

    def test_remove_duplicate_block(self):
        """Test removing duplicate environment block."""
        fixer = LaTeXFixer()
        content = r"""
\begin{columns}
  \begin{column}{0.5\textwidth}
    First column
  \begin{column}{0.5\textwidth}
    Duplicate!
  \end{column}
\end{columns}
"""
        error = ValidationError(
            line_number=4,
            error_type='duplicate_block',
            environment='column',
            message="Duplicate \\begin{column}",
            suggested_fix="Remove duplicate",
            fix_confidence=1.0
        )

        fixed_content, changes = fixer.fix_validation_errors(content, [error])

        # The duplicate block should be removed
        assert len(changes) == 1
        assert changes[0].fix_type == 'remove_duplicate'

    def test_preserve_indentation(self):
        """Test that indentation is preserved."""
        fixer = LaTeXFixer(FixerConfig(preserve_formatting=True))
        content = r"""
\begin{frame}
  \begin{itemize}
    \item Test
"""
        error = ValidationError(
            line_number=3,
            error_type='missing_end',
            environment='itemize',
            message="Missing \\end{itemize}",
            suggested_fix="Add \\end{itemize}",
            fix_confidence=1.0
        )

        fixed_content, changes = fixer.fix_validation_errors(content, [error])

        # Check that the added end tag has proper indentation
        assert '  \\end{itemize}' in fixed_content or '\t\\end{itemize}' in fixed_content

    def test_max_fixes_limit(self):
        """Test that max_fixes_per_file limit is respected."""
        fixer = LaTeXFixer(FixerConfig(max_fixes_per_file=1))
        content = r"""
\begin{frame}
\begin{itemize}
\begin{enumerate}
"""
        errors = [
            ValidationError(2, 'missing_end', 'frame', "Missing", "Fix", fix_confidence=1.0),
            ValidationError(3, 'missing_end', 'itemize', "Missing", "Fix", fix_confidence=1.0),
            ValidationError(4, 'missing_end', 'enumerate', "Missing", "Fix", fix_confidence=1.0),
        ]

        fixed_content, changes = fixer.fix_validation_errors(content, errors)

        # Only 1 fix should be applied due to limit
        assert len(changes) == 1

    def test_config_disable_missing_ends(self):
        """Test that missing end fixes can be disabled."""
        fixer = LaTeXFixer(FixerConfig(fix_missing_ends=False))
        content = r"""
\begin{frame}
  Content
"""
        error = ValidationError(
            line_number=2,
            error_type='missing_end',
            environment='frame',
            message="Missing \\end{frame}",
            suggested_fix="Add \\end{frame}",
            fix_confidence=1.0
        )

        fixed_content, changes = fixer.fix_validation_errors(content, [error])

        # No fixes should be applied
        assert len(changes) == 0
        assert fixed_content == content

    def test_config_disable_duplicates(self):
        """Test that duplicate fixes can be disabled."""
        fixer = LaTeXFixer(FixerConfig(fix_duplicates=False))
        content = r"""
\begin{column}{0.5\textwidth}
\begin{column}{0.5\textwidth}
"""
        error = ValidationError(
            line_number=3,
            error_type='duplicate_block',
            environment='column',
            message="Duplicate",
            suggested_fix="Remove",
            fix_confidence=1.0
        )

        fixed_content, changes = fixer.fix_validation_errors(content, [error])

        # No fixes should be applied
        assert len(changes) == 0

    def test_get_changes_log(self):
        """Test retrieving changes log."""
        fixer = LaTeXFixer()
        content = r"""
\begin{frame}
  Content
"""
        error = ValidationError(
            line_number=2,
            error_type='missing_end',
            environment='frame',
            message="Missing",
            suggested_fix="Fix",
            fix_confidence=1.0
        )

        _, changes = fixer.fix_validation_errors(content, [error])
        log = fixer.get_changes_log()

        assert log == changes
        assert len(log) == 1

    def test_clear_log(self):
        """Test clearing the changes log."""
        fixer = LaTeXFixer()
        content = r"""
\begin{frame}
  Content
"""
        error = ValidationError(2, 'missing_end', 'frame', "Missing", "Fix", fix_confidence=1.0)

        fixer.fix_validation_errors(content, [error])
        assert len(fixer.get_changes_log()) > 0

        fixer.clear_log()
        assert len(fixer.get_changes_log()) == 0

    def test_no_changes_for_valid_content(self):
        """Test that valid content produces no changes."""
        fixer = LaTeXFixer()
        content = r"""
\begin{frame}
  \frametitle{Test}
  Content
\end{frame}
"""
        # No errors
        fixed_content, changes = fixer.fix_validation_errors(content, [])

        assert fixed_content == content
        assert len(changes) == 0

    def test_fix_with_nested_environments(self):
        """Test fixing in nested environment structure."""
        fixer = LaTeXFixer()
        content = r"""
\begin{frame}
  \begin{columns}
    \begin{column}{0.5\textwidth}
      \begin{itemize}
        \item Test
"""
        error = ValidationError(
            line_number=5,
            error_type='missing_end',
            environment='itemize',
            message="Missing \\end{itemize}",
            suggested_fix="Add \\end{itemize}",
            fix_confidence=1.0
        )

        fixed_content, changes = fixer.fix_validation_errors(content, [error])

        assert r'\end{itemize}' in fixed_content
        assert len(changes) == 1
