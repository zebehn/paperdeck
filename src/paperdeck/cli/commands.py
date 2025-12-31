"""CLI command implementations.

This module contains the core logic for CLI commands.
"""

import logging
import subprocess
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

from ..ai.orchestrator import AIOrchestrator
from ..ai.retry_helpers import generate_with_retry
from ..ai.service import AIRequest
from ..core.config import AppConfiguration
from ..core.exceptions import (
    CompilationError,
    ExtractionError,
    GenerationError,
    PaperDeckError,
)
from ..core.models import Paper
from ..extraction.extractor import PaperExtractor
from ..generation.latex_generator import LaTeXGenerator
from ..generation.slide_organizer import SlideOrganizer
from ..prompts.manager import PromptLibrary
from ..services.generation_service import GenerationService


def generate_presentation(
    pdf_path: Path,
    config: AppConfiguration,
    theme: str = "Madrid",
    prompt_name: str = "default",
    model: Optional[str] = None,
    compile_pdf: bool = True,
    progress_callback: Optional[Callable] = None,
    skip_extraction: bool = False,
    elements_input_dir: Optional[Path] = None,
) -> Dict:
    """Generate presentation from PDF paper.

    Args:
        pdf_path: Path to input PDF
        config: Application configuration
        theme: Beamer theme name
        prompt_name: Name of prompt template to use
        model: Specific model to use (optional)
        compile_pdf: Whether to compile LaTeX to PDF
        progress_callback: Optional callback for progress updates
        skip_extraction: Whether to skip extraction and load pre-extracted elements
        elements_input_dir: Directory containing pre-extracted elements (required if skip_extraction=True)

    Returns:
        Dict with results (tex_path, pdf_path, slide_count, etc.)

    Raises:
        PaperDeckError: If generation fails
    """

    def progress():
        """Call progress callback if provided."""
        if progress_callback:
            progress_callback()

    # Step 1: Prepare paper with text extraction
    try:
        # NEW: Use GenerationService to extract text from PDF
        generation_service = GenerationService(config)
        paper = generation_service.prepare_paper(pdf_path)

        progress()

    except Exception as e:
        raise ExtractionError(f"Failed to prepare paper: {e}")

    # Step 1.5: Extract or load elements (figures, tables, equations)
    try:
        if skip_extraction:
            # NEW: Load pre-extracted elements from directory
            logger.info(f"Skipping extraction, loading pre-extracted elements from {elements_input_dir}")

            # Import the new loader
            from ..extraction.element_loader import ElementLoader

            # Validate directory before loading
            loader = ElementLoader(elements_input_dir)
            is_valid, errors = loader.validate_directory()
            if not is_valid:
                error_msg = "Invalid elements directory:\n" + "\n".join(f"  - {e}" for e in errors)
                raise ExtractionError(error_msg)

            # Load pre-extracted elements
            elements = loader.load_elements(
                element_types=config.extraction_config.element_types,
            )

            if not elements:
                logger.warning(f"No elements loaded from {elements_input_dir}")
            else:
                logger.info(f"Loaded {len(elements)} pre-extracted element(s)")

            # Add elements to paper
            paper.extracted_elements = elements

        else:
            # EXISTING: Extract elements from PDF using DocScalpel
            logger.info(f"Extracting elements from PDF using DocScalpel")

            extractor = PaperExtractor(
                confidence_threshold=config.extraction_config.confidence_threshold,
                output_directory=config.extraction_config.output_directory,
                extraction_config=config.extraction_config,
            )

            # Extract elements (figures, tables, equations)
            elements = extractor.extract(
                paper_path=pdf_path,
                element_types=config.extraction_config.element_types,
            )

            # Add elements to paper
            paper.extracted_elements = elements  # Use the new field from Phase 5

        progress()

    except Exception as e:
        raise ExtractionError(f"Failed to {'load' if skip_extraction else 'extract'} elements: {e}")

    # Step 2: Generate LaTeX using AI
    try:
        logger.info("Generating presentation using AI...")

        # Call AI to generate complete LaTeX document
        latex_code = generate_with_ai(
            paper=paper,
            config=config,
            prompt_name=prompt_name,
            model=model,
            pdf_path=pdf_path,  # Pass PDF file to AI service
        )

        # Extract LaTeX from response if wrapped in markdown code blocks
        if "```latex" in latex_code:
            # Remove markdown code block markers
            latex_code = latex_code.split("```latex")[1].split("```")[0].strip()
        elif "```" in latex_code:
            # Remove generic code block markers
            latex_code = latex_code.split("```")[1].split("```")[0].strip()

        logger.info(f"AI generated {len(latex_code)} characters of LaTeX code")

        # Ensure output directory exists
        config.output_directory.mkdir(parents=True, exist_ok=True)

        # Write LaTeX file
        output_name = pdf_path.stem
        tex_path = config.output_directory / f"{output_name}.tex"
        tex_path.write_text(latex_code)

        logger.info(f"LaTeX file written to {tex_path}")

        progress()

    except Exception as e:
        raise GenerationError(f"Failed to generate LaTeX with AI: {e}")

    # Step 3: Compile to PDF (optional)
    pdf_output_path = None
    if compile_pdf:
        try:
            pdf_output_path = compile_latex(tex_path, config.output_directory)
            progress()

            # Step 3.5: Check for overfull boxes after successful compilation
            log_path = config.output_directory / f"{tex_path.stem}.log"
            overfull_result = parse_latex_log_for_overfull(log_path)

            if overfull_result['has_overfull']:
                logger.warning(f"⚠️  Found {len(overfull_result['warnings'])} overfull warnings in compiled PDF")
                logger.info("Attempting to fix layout issues with AI...")

                try:
                    # Fix overfull boxes with AI
                    corrected_latex = validate_and_fix_overfull_with_llm(
                        latex_code=latex_code,
                        overfull_warnings=overfull_result['warnings'],
                        config=config,
                        model=model,
                    )

                    # Update the .tex file with corrected code
                    tex_path.write_text(corrected_latex)
                    latex_code = corrected_latex  # Update for slide count
                    logger.info(f"Updated {tex_path} with layout-corrected code")

                    # Recompile with fixed code
                    logger.info("Recompiling with layout fixes...")
                    pdf_output_path = compile_latex(tex_path, config.output_directory)

                    # Check if overfull warnings reduced
                    new_overfull_result = parse_latex_log_for_overfull(log_path)
                    if new_overfull_result['has_overfull']:
                        reduction = len(overfull_result['warnings']) - len(new_overfull_result['warnings'])
                        if reduction > 0:
                            logger.info(f"✅ Reduced overfull warnings from {len(overfull_result['warnings'])} to {len(new_overfull_result['warnings'])}")
                        else:
                            logger.warning(f"Still has {len(new_overfull_result['warnings'])} overfull warnings")
                    else:
                        logger.info("✅ All overfull warnings fixed!")

                    progress()

                except Exception as overfull_error:
                    logger.warning(f"Overfull fixing failed: {overfull_error}")
                    # Overfull fixing may have corrupted the LaTeX, so PDF might not exist
                    # Check if PDF still exists, if not set to None
                    if pdf_output_path and not pdf_output_path.exists():
                        logger.error("PDF was deleted during failed overfull fixing attempt")
                        pdf_output_path = None
                    else:
                        logger.info("PDF compiled but may have layout issues")
            else:
                logger.info("✅ No overfull warnings - layout looks good!")

        except CompilationError as e:
            # Compilation failed - try syntax validation and retry once
            logger.warning(f"LaTeX compilation failed: {e}")
            logger.info("Attempting to fix LaTeX syntax errors with AI validation...")

            try:
                # Validate and fix LaTeX code
                corrected_latex = validate_and_fix_latex_with_llm(
                    latex_code=latex_code,
                    config=config,
                    model=model,
                )

                # Update the .tex file with corrected code
                tex_path.write_text(corrected_latex)
                latex_code = corrected_latex  # Update for slide count
                logger.info(f"Updated {tex_path} with corrected LaTeX code")

                # Try compiling again
                logger.info("Retrying LaTeX compilation...")
                pdf_output_path = compile_latex(tex_path, config.output_directory)
                logger.info("✅ Compilation succeeded after validation fixes!")
                progress()

                # After successful retry, check for overfull boxes
                log_path = config.output_directory / f"{tex_path.stem}.log"
                overfull_result = parse_latex_log_for_overfull(log_path)

                if overfull_result['has_overfull']:
                    logger.warning(f"⚠️  Found {len(overfull_result['warnings'])} overfull warnings")
                    logger.info("Consider rerunning with overfull fixes")

            except Exception as retry_error:
                # Validation or retry compilation failed
                logger.error(f"Failed to fix and recompile: {retry_error}")
                pdf_output_path = None
        except Exception as e:
            # Other unexpected errors
            logger.error(f"Unexpected compilation error: {e}")
            pdf_output_path = None

    # Count slides by counting \begin{frame} occurrences
    slide_count = latex_code.count(r"\begin{frame}") + latex_code.count(r"\frame{")

    return {
        "tex_path": tex_path,
        "pdf_path": pdf_output_path,
        "slide_count": slide_count,
        "latex_code": latex_code,
    }


def _retry_with_fix(
    tex_path: Path,
    output_dir: Path,
    error_msg: str,
    config: Optional[Any],
    attempt_number: int
) -> bool:
    """Attempt to fix LaTeX errors and retry compilation (T051-T059).

    Args:
        tex_path: Path to .tex file
        output_dir: Output directory
        error_msg: Error message from failed compilation
        config: Application configuration
        attempt_number: Current retry attempt number

    Returns:
        bool: True if fix was attempted, False otherwise
    """
    from ..validation import LaTeXValidator, ValidationConfig, LaTeXFixer, FixerConfig
    import shutil

    # Check if retry is enabled (T055)
    if not config or not getattr(config, 'enable_retry', True):
        return False

    # Log retry attempt (T057)
    logger.info(f"Compilation failed (attempt {attempt_number}). Attempting to fix and retry...")
    logger.debug(f"Error that triggered retry: {error_msg}")

    try:
        # Validate the file to find structural errors (T052)
        validator = LaTeXValidator(
            ValidationConfig(environments=getattr(config, 'validation_environments', None))
        )
        validation_result = validator.validate_file(tex_path)

        if not validation_result.has_errors():
            logger.warning("No structural errors found to fix")
            return False

        logger.info(f"Found {validation_result.error_count()} structural error(s) to fix")

        # Save original if not already backed up
        backup_path = tex_path.with_suffix('.tex.orig')
        if not backup_path.exists():
            shutil.copy2(tex_path, backup_path)
            logger.info(f"Original file backed up to {backup_path.name}")

        # Read and fix content
        original_content = tex_path.read_text(encoding='utf-8')
        fixer = LaTeXFixer(FixerConfig())
        fixed_content, changes = fixer.fix_validation_errors(
            original_content,
            validation_result.errors
        )

        if not changes:
            logger.warning("Auto-fix was unable to fix any errors")
            return False

        # Write fixed content
        tex_path.write_text(fixed_content, encoding='utf-8')

        # Log changes (T057)
        logger.info(f"Applied {len(changes)} fix(es) on retry:")
        for change in changes:
            logger.info(f"  - {change.description}")

        return True

    except Exception as e:
        logger.error(f"Error during retry fix attempt: {e}")
        return False


def compile_latex(tex_path: Path, output_dir: Path, config: Optional[Any] = None) -> Path:
    """Compile LaTeX file to PDF with optional validation and error recovery.

    Args:
        tex_path: Path to .tex file
        output_dir: Output directory
        config: Application configuration (optional)

    Returns:
        Path: Path to generated PDF

    Raises:
        CompilationError: If compilation fails after retries
    """
    from ..validation import LaTeXValidator, ValidationConfig, LaTeXFixer, FixerConfig
    import shutil

    # Track if auto-fix was already applied (T056)
    autofix_applied = False

    # Perform validation if enabled (Feature 005)
    if config and getattr(config, 'enable_validation', True):
        try:
            validator = LaTeXValidator(
                ValidationConfig(environments=getattr(config, 'validation_environments', None))
            )
            validation_result = validator.validate_file(tex_path)

            if validation_result.has_errors():
                logger.warning(
                    f"LaTeX validation found {validation_result.error_count()} error(s) in {tex_path.name}"
                )
                for error in validation_result.errors:
                    logger.warning(f"  Line {error.line_number}: {error.message}")
                    logger.info(f"    Suggestion: {error.suggested_fix}")

                # Apply auto-fix if enabled (T046-T050)
                if getattr(config, 'enable_autofix', True):
                    try:
                        logger.info("Attempting to auto-fix detected errors...")

                        # Save original file as .tex.orig (T047)
                        backup_path = tex_path.with_suffix('.tex.orig')
                        shutil.copy2(tex_path, backup_path)
                        logger.info(f"Original file backed up to {backup_path.name}")

                        # Read file content
                        original_content = tex_path.read_text(encoding='utf-8')

                        # Apply fixes
                        fixer = LaTeXFixer(FixerConfig())
                        fixed_content, changes = fixer.fix_validation_errors(
                            original_content,
                            validation_result.errors
                        )

                        # Write fixed content back to file (T048)
                        tex_path.write_text(fixed_content, encoding='utf-8')

                        # Log changes (T050)
                        if changes:
                            logger.info(f"Applied {len(changes)} fix(es):")
                            for change in changes:
                                logger.info(f"  - {change.description}")
                            autofix_applied = True  # Mark that auto-fix was applied
                        else:
                            logger.warning("Auto-fix was unable to fix any errors")

                    except Exception as fix_error:
                        logger.error(f"Auto-fix failed: {fix_error}")
                        # Restore original if fix failed
                        if backup_path.exists():
                            shutil.copy2(backup_path, tex_path)
                            logger.info("Restored original file after fix failure")

            else:
                logger.debug(f"LaTeX validation passed for {tex_path.name}")

        except Exception as e:
            # Don't fail compilation if validation itself fails
            logger.warning(f"LaTeX validation failed: {e}")

    # Retry compilation with auto-fix if enabled (T053-T054)
    max_attempts = getattr(config, 'max_retry_attempts', 2) if config else 2
    attempt = 0

    while attempt < max_attempts:
        attempt += 1

        try:
            # Run pdflatex twice for references
            for _ in range(2):
                result = subprocess.run(
                    [
                        "pdflatex",
                        "-interaction=nonstopmode",
                        "-output-directory",
                        str(output_dir),
                        str(tex_path),
                    ],
                    capture_output=True,
                    text=True,
                    timeout=60,
                )

                if result.returncode != 0:
                    # Try to extract error message from log
                    log_path = output_dir / f"{tex_path.stem}.log"
                    error_msg = "LaTeX compilation failed"
                    if log_path.exists():
                        log_content = log_path.read_text()
                        # Extract first error line
                        for line in log_content.split("\n"):
                            if line.startswith("!"):
                                error_msg = line
                                break

                    # If this isn't the last attempt and auto-fix wasn't already applied,
                    # try to fix and retry (T054, T056)
                    if attempt < max_attempts and not autofix_applied:
                        if _retry_with_fix(tex_path, output_dir, error_msg, config, attempt):
                            # Fix was applied, break inner loop to retry compilation
                            break
                        else:
                            # Fix failed or not applicable, fail now
                            raise CompilationError(f"{error_msg}\n\nSee {log_path} for details")
                    else:
                        # Last attempt or auto-fix already applied, fail (T058)
                        if attempt >= max_attempts:
                            logger.error(f"Compilation failed after {max_attempts} attempt(s)")
                            # Save error log (T059)
                            error_log_path = output_dir / f"{tex_path.stem}.error.log"
                            error_log_path.write_text(
                                f"Compilation attempts: {attempt}\n"
                                f"Last error: {error_msg}\n\n"
                                f"Full log in: {log_path}"
                            )
                        raise CompilationError(f"{error_msg}\n\nSee {log_path} for details")

            # If we reach here, compilation succeeded
            break

        except subprocess.TimeoutExpired:
            raise CompilationError("LaTeX compilation timed out after 60 seconds")
        except FileNotFoundError:
            raise CompilationError(
                "pdflatex not found. Please install TeX Live or MiKTeX."
            )
        except CompilationError:
            # If this is the last attempt, re-raise
            if attempt >= max_attempts:
                raise
            # Otherwise, continue to next attempt
            logger.info(f"Attempt {attempt} failed, retrying...")
        except Exception as e:
            raise CompilationError(f"Compilation error: {e}")

    # Return path to PDF (after successful compilation)
    pdf_path = output_dir / f"{tex_path.stem}.pdf"
    if not pdf_path.exists():
        raise CompilationError(f"PDF was not generated: {pdf_path}")

    logger.info(f"Compilation successful after {attempt} attempt(s)")
    return pdf_path


def generate_with_ai(
    paper: Paper,
    config: AppConfiguration,
    prompt_name: str,
    model: Optional[str],
    pdf_path: Optional[Path] = None,
) -> str:
    """Generate complete LaTeX presentation using AI.

    Args:
        paper: Paper model with text content and extracted elements
        config: Application configuration
        prompt_name: Name of prompt template or path to custom prompt file
        model: Model to use
        pdf_path: Optional path to PDF file to send to AI service

    Returns:
        str: Complete LaTeX beamer document generated by AI

    Raises:
        GenerationError: If AI generation fails
    """
    import logging
    logger = logging.getLogger(__name__)

    # Load prompt template - check if it's a file path or template name
    prompt_path = Path(prompt_name)
    if prompt_path.exists() and prompt_path.is_file():
        # Load custom prompt file
        logger.info(f"Loading custom prompt from file: {prompt_path}")
        try:
            from ..prompts.manager import PromptTemplate

            content = prompt_path.read_text()
            template = PromptTemplate(
                name=prompt_path.stem,
                description=f"Custom prompt from {prompt_path.name}",
                content=content,
                style="custom",
                detail_level="medium",
                is_builtin=False,
            )
            logger.info(f"Successfully loaded custom prompt: {template.name}")
        except Exception as e:
            raise GenerationError(f"Failed to load custom prompt file '{prompt_path}': {e}")
    else:
        # Load template from library
        logger.info(f"Loading prompt template from library: {prompt_name}")
        prompt_library_path = Path(__file__).parent.parent.parent.parent / "prompts" / "templates"
        library = PromptLibrary(library_path=prompt_library_path)
        try:
            template = library.get_template(prompt_name)
            logger.info(f"Successfully loaded template: {template.name}")
        except KeyError:
            raise GenerationError(f"Prompt template '{prompt_name}' not found in library")

    # Prepare context - if PDF file is provided, use minimal text; otherwise use full extracted content
    if pdf_path:
        # When PDF file is attached, provide minimal context
        paper_content = f"**PDF file attached: {pdf_path.name}**\n\n"
        paper_content += f"Title: {paper.title or 'Untitled'}\n"
        paper_content += f"Authors: {', '.join(paper.authors) if paper.authors else 'Unknown'}\n\n"
        paper_content += "**Please read the attached PDF file for full paper content.**\n\n"

        # Add only extracted figure/table metadata for reference
        if paper.extracted_elements:
            figures = [e for e in paper.extracted_elements if e.element_type.value == "figure"]
            tables = [e for e in paper.extracted_elements if e.element_type.value == "table"]

            if figures:
                paper_content += "Extracted Figures:\n"
                for fig in figures:
                    filename = fig.output_filename.name if fig.output_filename else "unknown"
                    paper_content += f"- {filename} (page {fig.page_number})\n"
                paper_content += "\n"

            if tables:
                paper_content += "Extracted Tables:\n"
                for tbl in tables:
                    filename = tbl.output_filename.name if tbl.output_filename else "unknown"
                    paper_content += f"- {filename} (page {tbl.page_number})\n"
                paper_content += "\n"
    else:
        # No PDF file - use full extracted text content
        paper_content = f"Title: {paper.title or 'Untitled'}\n"
        paper_content += f"Authors: {', '.join(paper.authors) if paper.authors else 'Unknown'}\n\n"

        # Add full text content if available
        if paper.text_content:
            paper_content += "Full Text Content:\n"
            paper_content += "=" * 80 + "\n"
            paper_content += paper.text_content[:30000]  # Limit to first 30k chars to avoid token limits
            if len(paper.text_content) > 30000:
                paper_content += "\n\n[Content truncated for length...]"
            paper_content += "\n" + "=" * 80 + "\n\n"

        # Add section information
        if paper.sections:
            paper_content += "Paper Sections:\n"
            for section in paper.sections:
                paper_content += f"- {section.title}\n"
                if section.content:
                    # Include first 500 chars of each section
                    content_preview = section.content[:500]
                    paper_content += f"  {content_preview}...\n"
            paper_content += "\n"

        # Add extracted figures information
        if paper.extracted_elements:
            figures = [e for e in paper.extracted_elements if e.element_type.value == "figure"]
            tables = [e for e in paper.extracted_elements if e.element_type.value == "table"]

            if figures:
                paper_content += "Extracted Figures:\n"
                for fig in figures:
                    filename = fig.output_filename.name if fig.output_filename else "unknown"
                    paper_content += f"- {filename} (page {fig.page_number}, confidence: {fig.confidence_score:.2f})\n"
                paper_content += "\n"

            if tables:
                paper_content += "Extracted Tables:\n"
                for tbl in tables:
                    filename = tbl.output_filename.name if tbl.output_filename else "unknown"
                    paper_content += f"- {filename} (page {tbl.page_number}, confidence: {tbl.confidence_score:.2f})\n"
                paper_content += "\n"

    # Render prompt (no placeholder replacement needed - PDF is sent directly to LLM)
    prompt = template.render()

    logger.info("Sending prompt to AI service for LaTeX generation...")
    logger.debug(f"Prompt length: {len(prompt)} characters")

    # Log the full prompt in verbose mode for debugging
    logger.info("=" * 80)
    logger.info("PROMPT SENT TO LLM SERVICE:")
    logger.info("=" * 80)
    logger.info(prompt)
    logger.info("=" * 80)

    # Get AI service
    orchestrator = AIOrchestrator(config.ai_services)
    service = orchestrator.get_default_service()

    # Determine model - use more capable models for LaTeX generation
    if not model:
        if config.ai_services.default_provider == "openai":
            model = "gpt-5.1"  # Use GPT-5.1 for better LaTeX generation
        elif config.ai_services.default_provider == "anthropic":
            model = "claude-3-5-sonnet-20241022"  # Use Claude 3.5 Sonnet
        else:
            model = "default"

    # Create request with higher token limit for full LaTeX document
    request = AIRequest(
        prompt=prompt,
        model=model,
        max_tokens=16000,  # Increased for full LaTeX document
        temperature=0.3,  # Lower temperature for more structured output
        pdf_file_path=pdf_path,  # Include PDF file for direct access
    )

    # Generate with retry
    logger.info(f"Calling AI service ({model})...")
    response = generate_with_retry(service, request)

    logger.info(f"Received response from AI service ({len(response.content)} characters)")

    return response.content


def parse_latex_log_for_overfull(log_path: Path) -> Dict[str, any]:
    """Parse LaTeX .log file for overfull box warnings.

    Args:
        log_path: Path to the .log file

    Returns:
        Dict with:
        - 'has_overfull': bool - Whether any overfull warnings found
        - 'warnings': List of overfull warning strings
        - 'hbox_count': Number of overfull hbox warnings
        - 'vbox_count': Number of overfull vbox warnings
        - 'serious_count': Number of serious warnings (>10pt overflow)
    """
    import re
    import logging
    logger = logging.getLogger(__name__)

    result = {
        'has_overfull': False,
        'warnings': [],
        'hbox_count': 0,
        'vbox_count': 0,
        'serious_count': 0,
    }

    if not log_path.exists():
        return result

    try:
        log_content = log_path.read_text()

        # Pattern for overfull hbox: Overfull \hbox (15.0pt too wide) in paragraph at lines 42--43
        hbox_pattern = r'Overfull \\hbox \((\d+\.?\d*)pt too wide\).*?(?:at lines? (\d+(?:--\d+)?)|detected at line (\d+))'

        # Pattern for overfull vbox: Overfull \vbox (8.0pt too high) detected at line 67
        vbox_pattern = r'Overfull \\vbox \((\d+\.?\d*)pt too high\).*?(?:at lines? (\d+(?:--\d+)?)|detected at line (\d+))'

        # Find all overfull hbox warnings
        for match in re.finditer(hbox_pattern, log_content):
            overflow_amount = float(match.group(1))
            line_num = match.group(2) or match.group(3)
            warning = f"Overfull \\hbox ({overflow_amount}pt too wide) at lines {line_num}"
            result['warnings'].append(warning)
            result['hbox_count'] += 1
            if overflow_amount > 10.0:
                result['serious_count'] += 1

        # Find all overfull vbox warnings
        for match in re.finditer(vbox_pattern, log_content):
            overflow_amount = float(match.group(1))
            line_num = match.group(2) or match.group(3)
            warning = f"Overfull \\vbox ({overflow_amount}pt too high) at lines {line_num}"
            result['warnings'].append(warning)
            result['vbox_count'] += 1
            if overflow_amount > 10.0:
                result['serious_count'] += 1

        result['has_overfull'] = len(result['warnings']) > 0

        if result['has_overfull']:
            logger.info(f"Found {len(result['warnings'])} overfull warnings:")
            logger.info(f"  - Horizontal (hbox): {result['hbox_count']}")
            logger.info(f"  - Vertical (vbox): {result['vbox_count']}")
            logger.info(f"  - Serious (>10pt): {result['serious_count']}")

    except Exception as e:
        logger.warning(f"Failed to parse log file for overfull warnings: {e}")

    return result


def validate_and_fix_overfull_with_llm(
    latex_code: str,
    overfull_warnings: List[str],
    config: AppConfiguration,
    model: Optional[str] = None,
) -> str:
    """Fix overfull boxes in LaTeX using AI.

    This function sends the LaTeX code along with overfull warnings to an AI
    service to intelligently fix layout issues such as:
    - Images that are too large
    - Tables that are too wide
    - Text that doesn't fit
    - Frames with too much content

    Args:
        latex_code: The LaTeX code to fix
        overfull_warnings: List of overfull warning strings from log file
        config: Application configuration
        model: Model to use for fixing (optional)

    Returns:
        str: Corrected LaTeX code

    Raises:
        GenerationError: If fixing fails
    """
    import logging
    logger = logging.getLogger(__name__)

    logger.info("Fixing overfull boxes with AI...")

    # Create detailed prompt with warnings and fix strategies
    warnings_text = "\n".join([f"  - {w}" for w in overfull_warnings])

    fixing_prompt = f"""You are a LaTeX/Beamer expert. Fix the overfull box warnings in this presentation code.

**Overfull Warnings Detected:**
{warnings_text}

**Common Fixes to Apply:**

1. **Images (Overfull \\hbox with \\includegraphics):**
   - Reduce width: Change `width=0.9\\textwidth` to `width=0.7\\textwidth` or smaller
   - Use `width=0.6\\textwidth, height=0.6\\textheight, keepaspectratio` for better control
   - For very wide images, consider `width=0.5\\textwidth`

2. **Tables (Overfull \\hbox with tabular):**
   - Add `\\small` or `\\footnotesize` before the table
   - Reduce column widths or use `p{{width}}` columns
   - Use `\\resizebox{{0.9\\textwidth}}{{!}}{{...}}` to scale the entire table
   - Break wide tables across multiple slides

3. **Text Content (Overfull \\hbox or \\vbox):**
   - Break long lines or URLs using `\\url{{}}` or `\\path{{}}` commands
   - Add `\\raggedright` for better text flow
   - Use `\\small` or `\\footnotesize` for dense content
   - Shorten bullet points or split into multiple frames

4. **Frames with Too Much Content (Overfull \\vbox):**
   - Split the frame into 2-3 frames with logical breaks
   - Remove less important content
   - Use `\\small` or `\\footnotesize` for the entire frame
   - Add `[allowframebreaks]` option to frame (last resort)

5. **Columns Layout:**
   - Adjust column widths (reduce from 0.5 to 0.45 for each)
   - Use more uneven splits (0.4/0.55 instead of 0.5/0.5)
   - Ensure column contents don't overflow

**CRITICAL RULES:**
- Fix ALL overfull warnings listed above
- Return ONLY the corrected LaTeX code
- Do NOT add explanations or comments
- Do NOT wrap in code blocks (no ```)  - Maintain the same structure and content, just fix sizing/layout issues
- If a frame has too much content, split it intelligently across multiple frames
- Test that all images use reasonable widths (0.5-0.8\\textwidth max)

**LaTeX Code to Fix:**

{latex_code}
"""

    # Get AI service
    orchestrator = AIOrchestrator(config.ai_services)
    service = orchestrator.get_default_service()

    # Determine model
    if not model:
        if config.ai_services.default_provider == "openai":
            model = "gpt-5.1"
        elif config.ai_services.default_provider == "anthropic":
            model = "claude-3-5-sonnet-20241022"
        else:
            model = "default"

    # Create fixing request
    request = AIRequest(
        prompt=fixing_prompt,
        model=model,
        max_tokens=16000,
        temperature=0.1,  # Low temperature for precise fixes
    )

    try:
        logger.info(f"Calling AI service for overfull fixing ({model})...")
        response = generate_with_retry(service, request)
        corrected_code = response.content.strip()

        # Remove markdown code blocks if present
        if "```latex" in corrected_code:
            corrected_code = corrected_code.split("```latex")[1].split("```")[0].strip()
        elif "```" in corrected_code:
            corrected_code = corrected_code.split("```")[1].split("```")[0].strip()

        # Check if any fixes were made
        if corrected_code != latex_code:
            logger.info("Overfull fixing: Layout issues corrected")

            # Log some changes
            original_lines = latex_code.split('\n')
            corrected_lines = corrected_code.split('\n')

            changes = 0
            for i, (orig, corr) in enumerate(zip(original_lines, corrected_lines), 1):
                if orig != corr and changes < 3:  # Log first 3 changes
                    changes += 1
                    logger.info(f"Line {i} modified:")
                    logger.info(f"  Before: {orig[:80]}")
                    logger.info(f"  After:  {corr[:80]}")

            if changes >= 3:
                logger.info("... and more changes applied")
        else:
            logger.info("Overfull fixing: No changes made (code already optimal)")

        return corrected_code

    except Exception as e:
        logger.warning(f"Overfull fixing failed: {e}")
        logger.warning("Continuing with original LaTeX code")
        return latex_code


def validate_and_fix_latex_with_llm(
    latex_code: str,
    config: AppConfiguration,
    model: Optional[str] = None,
) -> str:
    """Validate and fix LaTeX syntax errors using AI.

    This function sends the generated LaTeX code to an AI service to check for
    and fix common LaTeX syntax errors such as:
    - Indented \\end{verbatim} statements
    - Unbalanced braces
    - Incorrect escape sequences
    - Other LaTeX-specific syntax issues

    Args:
        latex_code: The generated LaTeX code to validate
        config: Application configuration
        model: Model to use for validation (optional)

    Returns:
        str: Corrected LaTeX code

    Raises:
        GenerationError: If validation fails
    """
    import logging
    logger = logging.getLogger(__name__)

    logger.info("Validating and fixing LaTeX syntax with AI...")

    # Create validation prompt
    validation_prompt = """You are a LaTeX expert. Please review the following LaTeX Beamer code for syntax errors and fix them.

Common issues to check for:
1. **Verbatim environments**: The \\end{verbatim} command MUST start at column 1 (no leading spaces or tabs)
2. **Unbalanced braces**: Ensure all { have matching }
3. **Escape sequences**: Ensure special characters are properly escaped
4. **Math mode**: Ensure $ symbols are balanced
5. **Environment matching**: Ensure all \\begin{} have matching \\end{}

CRITICAL RULES:
- If you find errors, return ONLY the corrected LaTeX code
- If no errors are found, return the EXACT original code unchanged
- Do NOT add explanations, comments, or markdown formatting
- Do NOT wrap the code in code blocks (no ```)
- Return ONLY the raw LaTeX code

Here is the LaTeX code to validate:

"""
    validation_prompt += latex_code

    # Get AI service
    orchestrator = AIOrchestrator(config.ai_services)
    service = orchestrator.get_default_service()

    # Determine model - use same model as generation if provided
    if not model:
        if config.ai_services.default_provider == "openai":
            model = "gpt-5.1"  # Use GPT-5.1 for validation
        elif config.ai_services.default_provider == "anthropic":
            model = "claude-3-5-sonnet-20241022"
        else:
            model = "default"

    # Create validation request
    request = AIRequest(
        prompt=validation_prompt,
        model=model,
        max_tokens=16000,
        temperature=0.1,  # Very low temperature for precise corrections
    )

    try:
        logger.info(f"Calling AI service for LaTeX validation ({model})...")
        response = generate_with_retry(service, request)
        corrected_code = response.content.strip()

        # Remove markdown code blocks if present
        if "```latex" in corrected_code:
            corrected_code = corrected_code.split("```latex")[1].split("```")[0].strip()
        elif "```" in corrected_code:
            corrected_code = corrected_code.split("```")[1].split("```")[0].strip()

        # Check if any fixes were made
        if corrected_code != latex_code:
            logger.info("LaTeX validation: Syntax errors found and corrected")

            # Calculate and log the differences
            original_lines = latex_code.split('\n')
            corrected_lines = corrected_code.split('\n')

            differences = 0
            for i, (orig, corr) in enumerate(zip(original_lines, corrected_lines), 1):
                if orig != corr:
                    differences += 1
                    if differences <= 5:  # Log first 5 differences
                        logger.info(f"Line {i} changed:")
                        logger.info(f"  Before: {orig[:100]}")
                        logger.info(f"  After:  {corr[:100]}")

            if differences > 5:
                logger.info(f"... and {differences - 5} more lines changed")

            logger.info(f"Total lines modified: {differences}")
        else:
            logger.info("LaTeX validation: No syntax errors found")

        return corrected_code

    except Exception as e:
        logger.warning(f"LaTeX validation failed: {e}")
        logger.warning("Continuing with original LaTeX code")
        return latex_code
