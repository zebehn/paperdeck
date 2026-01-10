"""Integration tests for CLI validation integration."""

import pytest
import tempfile
import shutil
from pathlib import Path

from paperdeck.validation.cli_integration import (
    validate_and_fix_latex_file,
    validate_latex_file,
    report_validation_results,
    get_validation_summary
)
from paperdeck.validation import ValidationConfig, FixerConfig


class TestCLIIntegration:
    """Integration tests for CLI validation helpers."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        shutil.rmtree(temp_path)

    @pytest.mark.integration
    @pytest.mark.validation
    def test_validate_and_fix_with_errors(self, temp_dir):
        """Test validate_and_fix_latex_file with errors."""
        # Create file with error
        test_file = temp_dir / "test.tex"
        test_file.write_text(r"""\documentclass{beamer}
\begin{document}
\begin{frame}
\textbf{Missing brace
\end{frame}
\end{document}
""")

        # Validate and fix
        fixed, backup_metadata, num_fixes = validate_and_fix_latex_file(
            test_file,
            temp_dir
        )

        # Should have fixed
        assert fixed is True
        assert backup_metadata is not None
        assert num_fixes >= 1

        # File should be modified
        content = test_file.read_text()
        assert '}' in content

        # Backup should exist
        assert backup_metadata.backup_path.exists()

    @pytest.mark.integration
    @pytest.mark.validation
    def test_validate_and_fix_no_errors(self, temp_dir):
        """Test validate_and_fix_latex_file with no errors."""
        test_file = temp_dir / "valid.tex"
        test_file.write_text(r"""\documentclass{beamer}
\begin{document}
\begin{frame}
\textbf{Valid content}
\end{frame}
\end{document}
""")

        # Validate and fix
        fixed, backup_metadata, num_fixes = validate_and_fix_latex_file(
            test_file,
            temp_dir
        )

        # Should not need fixing
        assert fixed is False
        assert num_fixes == 0

    @pytest.mark.integration
    @pytest.mark.validation
    def test_validate_latex_file(self, temp_dir):
        """Test validate_latex_file function."""
        test_file = temp_dir / "test.tex"
        test_file.write_text(r"\textbf{Missing brace")

        # Validate
        result = validate_latex_file(test_file)

        # Should have errors
        assert not result.is_valid
        assert len(result.errors) >= 1

        # Should have brace error
        brace_errors = [e for e in result.errors if 'brace' in e.error_type.lower()]
        assert len(brace_errors) >= 1

    @pytest.mark.integration
    @pytest.mark.validation
    def test_get_validation_summary_valid(self, temp_dir):
        """Test get_validation_summary for valid file."""
        test_file = temp_dir / "valid.tex"
        test_file.write_text(r"\textbf{valid}")

        result = validate_latex_file(test_file)
        summary = get_validation_summary(result)

        assert "✅" in summary
        assert "Valid" in summary

    @pytest.mark.integration
    @pytest.mark.validation
    def test_get_validation_summary_invalid(self, temp_dir):
        """Test get_validation_summary for invalid file."""
        test_file = temp_dir / "invalid.tex"
        test_file.write_text(r"\textbf{missing")

        result = validate_latex_file(test_file)
        summary = get_validation_summary(result)

        assert "❌" in summary
        assert "error(s)" in summary
        assert "auto-fixable" in summary

    @pytest.mark.integration
    @pytest.mark.validation
    def test_validate_and_fix_multiple_attempts(self, temp_dir):
        """Test validate_and_fix_latex_file tracks attempt number."""
        test_file = temp_dir / "test.tex"
        test_file.write_text(r"\textbf{Missing brace")

        # First attempt
        fixed1, backup1, num_fixes1 = validate_and_fix_latex_file(
            test_file,
            temp_dir,
            attempt_number=1
        )

        assert fixed1 is True
        assert num_fixes1 >= 1

        # Create another error
        test_file.write_text(r"\textit{Another error")

        # Second attempt
        fixed2, backup2, num_fixes2 = validate_and_fix_latex_file(
            test_file,
            temp_dir,
            attempt_number=2
        )

        assert fixed2 is True
        assert backup1.backup_path != backup2.backup_path

    @pytest.mark.integration
    @pytest.mark.validation
    def test_custom_configs(self, temp_dir):
        """Test validate_and_fix with custom configurations."""
        test_file = temp_dir / "test.tex"
        test_file.write_text(r"\textbf{Missing brace")

        # Custom configs
        val_config = ValidationConfig(validate_braces=True)
        fix_config = FixerConfig(
            fix_missing_braces=True,
            confidence_threshold=0.70
        )

        # Validate and fix
        fixed, backup_metadata, num_fixes = validate_and_fix_latex_file(
            test_file,
            temp_dir,
            config=val_config,
            fixer_config=fix_config
        )

        assert fixed is True
        assert num_fixes >= 1

    @pytest.mark.integration
    @pytest.mark.validation
    def test_backup_on_failed_fix(self, temp_dir):
        """Test backup is created even if fix fails."""
        test_file = temp_dir / "test.tex"
        test_file.write_text(r"\textbf{error")

        # Use config that prevents fixes
        fix_config = FixerConfig(
            fix_missing_braces=False,
            fix_extra_braces=False
        )

        fixed, backup_metadata, num_fixes = validate_and_fix_latex_file(
            test_file,
            temp_dir,
            fixer_config=fix_config
        )

        # Should not fix (config disabled)
        assert fixed is False
        assert num_fixes == 0

        # But backup should still be created
        assert backup_metadata is not None
        assert backup_metadata.backup_path.exists()
