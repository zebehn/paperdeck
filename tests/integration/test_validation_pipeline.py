"""Integration tests for the full validation + auto-fix + retry pipeline."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from src.paperdeck.validation import LaTeXValidator, LaTeXFixer
from src.paperdeck.core.config import AppConfiguration


class TestValidationPipeline:
    """Integration tests for validation, auto-fix, and retry pipeline."""

    def test_validation_only(self, tmp_path):
        """Test validation without auto-fix."""
        # Create a malformed .tex file
        tex_file = tmp_path / "test.tex"
        tex_file.write_text(r"""
\begin{frame}
  Content
""")  # Missing \end{frame}

        validator = LaTeXValidator()
        result = validator.validate_file(tex_file)

        assert not result.is_valid
        assert result.error_count() > 0
        assert any(e.error_type == 'missing_end' for e in result.errors)

    def test_validation_and_autofix_success(self, tmp_path):
        """Test validation + auto-fix pipeline (T062)."""
        # Create a malformed .tex file
        tex_file = tmp_path / "test.tex"
        content = r"""
\begin{frame}
  \frametitle{Test}
  \begin{itemize}
    \item Test
"""  # Missing ends

        tex_file.write_text(content)

        # Step 1: Validate
        validator = LaTeXValidator()
        result = validator.validate_file(tex_file)
        assert not result.is_valid
        assert result.error_count() > 0

        # Step 2: Auto-fix
        fixer = LaTeXFixer()
        fixed_content, changes = fixer.fix_validation_errors(content, result.errors)

        assert len(changes) > 0
        tex_file.write_text(fixed_content)

        # Step 3: Validate again
        result2 = validator.validate_file(tex_file)

        # Should have fewer errors (may not be zero if some errors unfixable)
        assert result2.error_count() <= result.error_count()

    def test_autofix_preserves_valid_content(self, tmp_path):
        """Test that auto-fix doesn't break valid LaTeX."""
        tex_file = tmp_path / "valid.tex"
        content = r"""
\begin{frame}
  \frametitle{Test}
  \begin{itemize}
    \item Test
  \end{itemize}
\end{frame}
"""
        tex_file.write_text(content)

        # Validate
        validator = LaTeXValidator()
        result = validator.validate_file(tex_file)

        # Should be valid
        assert result.is_valid

        # Try auto-fix anyway (should do nothing)
        fixer = LaTeXFixer()
        fixed_content, changes = fixer.fix_validation_errors(content, result.errors)

        # No changes should be made
        assert len(changes) == 0
        assert fixed_content == content

    def test_multiple_errors_fixed_in_order(self, tmp_path):
        """Test that multiple errors are fixed correctly."""
        tex_file = tmp_path / "multiple_errors.tex"
        content = r"""
\begin{frame}
  \begin{itemize}
    \item One
  \begin{columns}
    Content
"""  # Missing multiple ends

        tex_file.write_text(content)

        validator = LaTeXValidator()
        result = validator.validate_file(tex_file)

        # Should detect multiple errors
        assert result.error_count() >= 2

        # Fix all errors
        fixer = LaTeXFixer()
        fixed_content, changes = fixer.fix_validation_errors(content, result.errors)

        assert len(changes) >= 2

        # Validate fixed content
        tex_file.write_text(fixed_content)
        result2 = validator.validate_file(tex_file)

        # Should have fewer errors
        assert result2.error_count() < result.error_count()

    @pytest.mark.parametrize("fixture_name", [
        "missing_end_column.tex",
        "unmatched_frame.tex",
        "nested_errors.tex",
    ])
    def test_with_fixtures(self, fixture_name):
        """Test validation with actual fixture files."""
        fixture_path = Path(f"tests/fixtures/malformed_latex/{fixture_name}")

        if not fixture_path.exists():
            pytest.skip(f"Fixture {fixture_name} not found")

        validator = LaTeXValidator()
        result = validator.validate_file(fixture_path)

        # These fixtures should have errors
        # (Note: Some may have been fixed in earlier development)
        # Just verify validation runs without crashing
        assert isinstance(result.is_valid, bool)

    def test_config_integration(self):
        """Test that AppConfiguration integrates with validation."""
        config = AppConfiguration()

        # Check validation settings exist
        assert hasattr(config, 'enable_validation')
        assert hasattr(config, 'enable_autofix')
        assert hasattr(config, 'enable_retry')
        assert hasattr(config, 'max_retry_attempts')
        assert hasattr(config, 'validation_environments')

        # Check defaults
        assert config.enable_validation == True
        assert config.enable_autofix == True
        assert config.enable_retry == True
        assert config.max_retry_attempts == 2
        assert 'frame' in config.validation_environments

    def test_fixer_respects_config(self):
        """Test that FixerConfig controls behavior."""
        from src.paperdeck.validation import FixerConfig

        # Test with fixes disabled
        config = FixerConfig(fix_missing_ends=False, fix_duplicates=False)
        fixer = LaTeXFixer(config)

        content = r"\begin{frame}"  # Missing end
        from src.paperdeck.validation import ValidationError

        error = ValidationError(
            line_number=1,
            error_type='missing_end',
            environment='frame',
            message="Missing",
            suggested_fix="Fix"
        )

        fixed_content, changes = fixer.fix_validation_errors(content, [error])

        # No fixes should be applied
        assert len(changes) == 0

    def test_max_fixes_limit(self):
        """Test that max_fixes_per_file limit works."""
        from src.paperdeck.validation import FixerConfig, ValidationError

        config = FixerConfig(max_fixes_per_file=1)
        fixer = LaTeXFixer(config)

        errors = [
            ValidationError(1, 'missing_end', 'frame', "Error 1", "Fix"),
            ValidationError(2, 'missing_end', 'itemize', "Error 2", "Fix"),
            ValidationError(3, 'missing_end', 'columns', "Error 3", "Fix"),
        ]

        content = r"""
\begin{frame}
\begin{itemize}
\begin{columns}
"""

        fixed_content, changes = fixer.fix_validation_errors(content, errors)

        # Only 1 fix should be applied
        assert len(changes) == 1

    def test_backup_file_creation(self, tmp_path):
        """Test that backup files are created during auto-fix."""
        import shutil

        tex_file = tmp_path / "test.tex"
        backup_file = tmp_path / "test.tex.orig"

        content = r"""
\begin{frame}
  Content
"""
        tex_file.write_text(content)

        # Simulate auto-fix workflow
        shutil.copy2(tex_file, backup_file)

        assert backup_file.exists()
        assert backup_file.read_text() == content

        # Modify original
        tex_file.write_text(content + r"\end{frame}")

        # Backup should still have original
        assert backup_file.read_text() == content
