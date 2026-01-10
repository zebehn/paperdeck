"""Integration tests for complete validation → fix → validation cycle."""

import pytest
from paperdeck.validation.latex_validator import LaTeXValidator
from paperdeck.validation.latex_fixer import LaTeXFixer


class TestValidationFixCycleUS1:
    """Integration tests for User Story 1: Auto-fix cycle."""

    @pytest.mark.integration
    @pytest.mark.validation
    @pytest.mark.us1
    def test_fix_missing_brace_full_cycle(self):
        """Test complete cycle: detect missing brace → fix → validate passes."""
        content = r"""\documentclass{beamer}
\begin{document}
\begin{frame}
\textbf{Missing closing brace
\end{frame}
\end{document}
"""

        # Step 1: Initial validation detects error
        validator = LaTeXValidator()
        result = validator.validate_content(content)

        assert not result.is_valid
        brace_errors = [e for e in result.errors if 'brace' in e.error_type.lower()]
        assert len(brace_errors) >= 1

        # Step 2: Apply fixes
        fixer = LaTeXFixer()
        fixed_content, changes = fixer.fix_validation_errors(content, result.errors)

        assert len(changes) >= 1
        assert '}' in fixed_content

        # Step 3: Re-validate - should pass now
        result_after = validator.validate_content(fixed_content)

        brace_errors_after = [e for e in result_after.errors if 'brace' in e.error_type.lower()]
        assert len(brace_errors_after) == 0

    @pytest.mark.integration
    @pytest.mark.validation
    @pytest.mark.us1
    def test_fix_extra_brace_full_cycle(self):
        """Test complete cycle: detect extra brace → fix → validate passes."""
        content = r"""\documentclass{beamer}
\begin{document}
\begin{frame}
\textbf{Extra closing brace}}
\end{frame}
\end{document}
"""

        # Step 1: Initial validation detects error
        validator = LaTeXValidator()
        result = validator.validate_content(content)

        assert not result.is_valid
        brace_errors = [e for e in result.errors if 'brace' in e.error_type.lower()]
        assert len(brace_errors) >= 1

        # Step 2: Apply fixes
        fixer = LaTeXFixer()
        fixed_content, changes = fixer.fix_validation_errors(content, result.errors)

        assert len(changes) >= 1

        # Step 3: Re-validate - should pass now
        result_after = validator.validate_content(fixed_content)

        brace_errors_after = [e for e in result_after.errors if 'brace' in e.error_type.lower()]
        assert len(brace_errors_after) == 0

    @pytest.mark.integration
    @pytest.mark.validation
    @pytest.mark.us1
    def test_fix_multiple_errors_full_cycle(self):
        """Test complete cycle with multiple brace errors."""
        content = r"""\documentclass{beamer}
\begin{document}
\begin{frame}
\textbf{Missing brace here
\textit{Also missing brace
\end{frame}
\end{document}
"""

        # Step 1: Initial validation detects multiple errors
        validator = LaTeXValidator()
        result = validator.validate_content(content)

        assert not result.is_valid
        brace_errors = [e for e in result.errors if 'brace' in e.error_type.lower()]
        assert len(brace_errors) >= 1

        # Step 2: Apply fixes
        fixer = LaTeXFixer()
        fixed_content, changes = fixer.fix_validation_errors(content, result.errors)

        assert len(changes) >= 1

        # Step 3: Re-validate - brace errors should be reduced or eliminated
        result_after = validator.validate_content(fixed_content)

        brace_errors_after = [e for e in result_after.errors if 'brace' in e.error_type.lower()]
        assert len(brace_errors_after) < len(brace_errors)

    @pytest.mark.integration
    @pytest.mark.validation
    @pytest.mark.us1
    def test_validate_and_fix_with_mixed_errors(self):
        """Test delimiter fixing alongside other validation."""
        content = r"""\documentclass{beamer}
\begin{document}
\begin{frame}
\textbf{Missing brace
\textit{Valid italic}
\end{frame}
\end{document}
"""

        # Initial validation should detect brace error
        validator = LaTeXValidator()
        result = validator.validate_content(content)

        assert not result.is_valid

        brace_errors = [e for e in result.errors if 'brace' in e.error_type.lower()]
        assert len(brace_errors) >= 1

        # Fix errors
        fixer = LaTeXFixer()
        fixed_content, changes = fixer.fix_validation_errors(content, result.errors)

        # Should have fixes
        assert len(changes) >= 1

        # Re-validate - brace errors should be fixed
        result_after = validator.validate_content(fixed_content)

        brace_errors_after = [e for e in result_after.errors if 'brace' in e.error_type.lower()]
        assert len(brace_errors_after) == 0

    @pytest.mark.integration
    @pytest.mark.validation
    @pytest.mark.us1
    def test_change_log_tracking(self):
        """Test that all changes are properly logged."""
        content = r"""\textbf{Missing brace"""

        validator = LaTeXValidator()
        result = validator.validate_content(content)

        fixer = LaTeXFixer()
        fixed_content, changes = fixer.fix_validation_errors(content, result.errors)

        # Verify change log details
        assert len(changes) >= 1

        for change in changes:
            assert change.line_number > 0
            assert change.fix_type in ['fix_missing_closing_brace', 'fix_extra_closing_brace', 'add_missing_end']
            assert change.confidence > 0
            assert change.before is not None or change.after is not None

    @pytest.mark.integration
    @pytest.mark.validation
    @pytest.mark.us1
    def test_preserves_valid_content(self):
        """Test that valid content remains unchanged."""
        content = r"""\documentclass{beamer}
\begin{document}
\begin{frame}
\frametitle{Valid Frame}
\textbf{This is bold} and \textit{this is italic}.
\end{frame}
\end{document}
"""

        validator = LaTeXValidator()
        result = validator.validate_content(content)

        # Should be valid with no delimiter errors
        brace_errors = [e for e in result.errors if 'brace' in e.error_type.lower()]
        assert len(brace_errors) == 0

        # Fixer should make no changes
        fixer = LaTeXFixer()
        fixed_content, changes = fixer.fix_validation_errors(content, result.errors)

        # Content should remain unchanged
        assert fixed_content == content
