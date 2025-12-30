"""Unit tests for LaTeXValidator."""

import pytest
from pathlib import Path
from src.paperdeck.validation.latex_validator import LaTeXValidator, ValidationConfig
from src.paperdeck.validation.validation_errors import ValidationResult


class TestLaTeXValidator:
    """Test cases for LaTeXValidator class."""

    def test_validate_content_valid(self):
        """Test validation of properly structured LaTeX."""
        validator = LaTeXValidator()
        content = r"""
\begin{frame}
  \frametitle{Test}
  \begin{itemize}
    \item One
  \end{itemize}
\end{frame}
"""

        result = validator.validate_content(content)

        assert result.is_valid
        assert result.error_count() == 0
        assert not result.has_errors()

    def test_validate_content_missing_end(self):
        """Test detection of missing \\end{...} tag."""
        validator = LaTeXValidator()
        content = r"""
\begin{frame}
  \frametitle{Test}
  \begin{itemize}
    \item One
"""  # Missing \end{itemize} and \end{frame}

        result = validator.validate_content(content)

        assert not result.is_valid
        assert result.error_count() == 2
        assert result.has_errors()

        # Check that errors have line numbers
        for error in result.errors:
            assert error.line_number > 0
            assert error.error_type == 'missing_end'

    def test_validate_content_duplicate_block(self):
        """Test detection of duplicate environment blocks."""
        validator = LaTeXValidator()
        content = r"""
\begin{frame}
  \begin{columns}
    \begin{column}{0.5\textwidth}
      Content
    \begin{column}{0.5\textwidth}
      Duplicate begin without closing previous!
    \end{column}
  \end{columns}
\end{frame}
"""

        result = validator.validate_content(content)

        assert not result.is_valid
        assert result.error_count() > 0
        # Should detect duplicate column OR missing end (both are valid detections)
        error_types = {e.error_type for e in result.errors}
        assert 'duplicate_block' in error_types or 'missing_end' in error_types

    def test_validate_content_unmatched_end(self):
        """Test detection of unmatched \\end{...} tag."""
        validator = LaTeXValidator()
        content = r"""
\begin{frame}
  Content
\end{frame}
\end{frame}
"""  # Extra \end{frame}

        result = validator.validate_content(content)

        assert not result.is_valid
        assert result.error_count() == 1
        assert result.errors[0].error_type == 'unmatched_end'

    def test_validate_file_not_found(self):
        """Test validation of non-existent file."""
        validator = LaTeXValidator()
        fake_path = Path("/nonexistent/file.tex")

        with pytest.raises(FileNotFoundError):
            validator.validate_file(fake_path)

    def test_validate_file_with_fixture(self, tmp_path):
        """Test validation of actual file."""
        validator = LaTeXValidator()

        # Create a temporary .tex file
        tex_file = tmp_path / "test.tex"
        tex_file.write_text(r"""
\begin{frame}
  \frametitle{Test}
  Content
\end{frame}
""")

        result = validator.validate_file(tex_file)

        assert result.is_valid
        assert result.error_count() == 0

    def test_validation_result_str(self):
        """Test string representation of ValidationResult."""
        validator = LaTeXValidator()
        content = r"""
\begin{frame}
  \begin{itemize}
    \item Test
"""  # Missing ends

        result = validator.validate_content(content)

        result_str = str(result)
        assert "Validation failed" in result_str
        assert "error(s)" in result_str

    def test_validation_error_messages(self):
        """Test that errors have proper messages and suggested fixes."""
        validator = LaTeXValidator()
        content = r"""
\begin{frame}
  Content
"""  # Missing \end{frame}

        result = validator.validate_content(content)

        assert result.error_count() == 1
        error = result.errors[0]

        # Check error has all required fields
        assert error.message
        assert error.suggested_fix
        assert error.environment == 'frame'
        assert "Missing" in error.message or "Unmatched" in error.message

    def test_custom_config(self):
        """Test validator with custom configuration."""
        config = ValidationConfig(
            environments=['custom'],
            strict_mode=False
        )
        validator = LaTeXValidator(config)

        content = r"""
\begin{frame}
  Content
"""  # Missing \end{frame}, but 'frame' not in custom list

        result = validator.validate_content(content)

        # Should be valid because 'frame' not being validated
        assert result.is_valid

    def test_errors_sorted_by_line_number(self):
        """Test that errors are returned sorted by line number."""
        validator = LaTeXValidator()
        content = r"""
\begin{frame}
  \begin{itemize}
    \item Test
  \begin{columns}
"""  # Multiple missing ends

        result = validator.validate_content(content)

        if result.error_count() > 1:
            # Check errors are sorted
            line_numbers = [e.line_number for e in result.errors]
            assert line_numbers == sorted(line_numbers)
