"""Performance tests for validation and auto-fix systems."""

import pytest
import time
from pathlib import Path
from src.paperdeck.validation import LaTeXValidator, LaTeXFixer, ValidationConfig, FixerConfig


class TestValidationPerformance:
    """Performance tests to ensure validation is fast enough."""

    def test_validation_performance_50_slides(self, tmp_path):
        """Test that validation completes in <100ms for 50-slide presentation (T074)."""
        # Generate a 50-slide presentation
        slides = []
        for i in range(50):
            slides.append(f"""
\\begin{{frame}}
  \\frametitle{{Slide {i + 1}}}
  \\begin{{itemize}}
    \\item Point 1
    \\item Point 2
    \\item Point 3
  \\end{{itemize}}
\\end{{frame}}
""")

        content = "\\n".join(slides)
        tex_file = tmp_path / "large_presentation.tex"
        tex_file.write_text(content)

        # Measure validation time
        validator = LaTeXValidator()
        start_time = time.time()
        result = validator.validate_file(tex_file)
        elapsed_ms = (time.time() - start_time) * 1000

        # Should complete in <100ms
        assert elapsed_ms < 100, f"Validation took {elapsed_ms:.2f}ms (target: <100ms)"

        # Should be valid
        assert result.is_valid
        assert result.error_count() == 0

    def test_validation_performance_complex_nesting(self, tmp_path):
        """Test validation performance with complex nested structures."""
        # Generate complex nested structure
        content = """
\\begin{frame}
  \\frametitle{Complex Slide}
  \\begin{columns}
    \\begin{column}{0.5\\textwidth}
      \\begin{itemize}
        \\item Item 1
        \\begin{enumerate}
          \\item Subitem A
          \\item Subitem B
        \\end{enumerate}
        \\item Item 2
      \\end{itemize}
    \\end{column}
    \\begin{column}{0.5\\textwidth}
      \\begin{itemize}
        \\item Item 3
        \\item Item 4
      \\end{itemize}
    \\end{column}
  \\end{columns}
\\end{frame}
"""

        # Repeat 20 times for complexity
        content = content * 20
        tex_file = tmp_path / "complex.tex"
        tex_file.write_text(content)

        validator = LaTeXValidator()
        start_time = time.time()
        result = validator.validate_file(tex_file)
        elapsed_ms = (time.time() - start_time) * 1000

        # Should still be under 100ms
        assert elapsed_ms < 100, f"Complex validation took {elapsed_ms:.2f}ms"
        assert result.is_valid


class TestAutoFixPerformance:
    """Performance tests for auto-fix system."""

    def test_autofix_performance_typical_errors(self, tmp_path):
        """Test that auto-fix completes in <200ms for typical errors (T075)."""
        # Create content with 10 missing end tags (typical error count)
        # Actually omit the end tags to create real errors
        content = ""
        for i in range(10):
            content += f"""
\\begin{{frame}}
  \\frametitle{{Slide {i + 1}}}
  \\begin{{itemize}}
    \\item Point 1
    \\item Point 2
"""

        tex_file = tmp_path / "errors.tex"
        tex_file.write_text(content)

        # Validate to get errors
        validator = LaTeXValidator()
        result = validator.validate_file(tex_file)
        assert result.error_count() > 0

        # Measure auto-fix time
        fixer = LaTeXFixer()
        start_time = time.time()
        fixed_content, changes = fixer.fix_validation_errors(content, result.errors)
        elapsed_ms = (time.time() - start_time) * 1000

        # Should complete in <200ms
        assert elapsed_ms < 200, f"Auto-fix took {elapsed_ms:.2f}ms (target: <200ms)"

        # Should have made fixes
        assert len(changes) > 0

    def test_autofix_performance_many_errors(self, tmp_path):
        """Test auto-fix performance with many errors (stress test)."""
        # Create content with 50 missing end tags
        content = ""
        for i in range(50):
            content += f"""
\\begin{{frame}}
  Content {i + 1}
"""

        validator = LaTeXValidator()
        result = validator.validate_content(content)

        # Should detect many errors
        assert result.error_count() >= 40

        # Measure fix time
        fixer = LaTeXFixer()
        start_time = time.time()
        fixed_content, changes = fixer.fix_validation_errors(content, result.errors)
        elapsed_ms = (time.time() - start_time) * 1000

        # Even with many errors, should be reasonably fast (<500ms)
        assert elapsed_ms < 500, f"Many errors took {elapsed_ms:.2f}ms"
        assert len(changes) > 0


class TestEndToEndPerformance:
    """End-to-end performance tests for the full validation pipeline."""

    def test_full_pipeline_performance(self, tmp_path):
        """Test full validation + auto-fix pipeline performance."""
        # Create realistic presentation with some errors
        content = """
\\begin{frame}
  \\frametitle{Introduction}
  \\begin{itemize}
    \\item Point 1
    \\item Point 2
  \\end{itemize}
\\end{frame}

\\begin{frame}
  \\frametitle{Problem}
  \\begin{columns}
    \\begin{column}{0.5\\textwidth}
      Text here
    \\end{column}
    \\begin{column}{0.5\\textwidth}
      More text

\\begin{frame}
  \\frametitle{Solution}
  Content
"""

        tex_file = tmp_path / "realistic.tex"
        tex_file.write_text(content)

        # Measure full pipeline
        start_time = time.time()

        # Step 1: Validate
        validator = LaTeXValidator()
        result = validator.validate_file(tex_file)

        # Step 2: Auto-fix if needed
        if result.has_errors():
            fixer = LaTeXFixer()
            fixed_content, changes = fixer.fix_validation_errors(content, result.errors)
            tex_file.write_text(fixed_content)

            # Step 3: Re-validate
            result2 = validator.validate_file(tex_file)

        elapsed_ms = (time.time() - start_time) * 1000

        # Full pipeline should complete quickly (<300ms)
        assert elapsed_ms < 300, f"Full pipeline took {elapsed_ms:.2f}ms"

    def test_validation_scales_linearly(self, tmp_path):
        """Test that validation time scales linearly with file size."""
        validator = LaTeXValidator()
        times = []

        # Test with 10, 20, 40 slides
        for num_slides in [10, 20, 40]:
            content = ""
            for i in range(num_slides):
                content += f"""
\\begin{{frame}}
  \\frametitle{{Slide {i + 1}}}
  \\begin{{itemize}}
    \\item Point 1
  \\end{{itemize}}
\\end{{frame}}
"""

            tex_file = tmp_path / f"test_{num_slides}.tex"
            tex_file.write_text(content)

            start_time = time.time()
            validator.validate_file(tex_file)
            elapsed_ms = (time.time() - start_time) * 1000
            times.append(elapsed_ms)

        # Time should roughly double when slides double
        # Allow some variance (within 3x factor)
        ratio = times[1] / times[0]
        assert 0.5 < ratio < 4.0, f"Performance not linear: {times}"
