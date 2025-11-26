"""CLI command implementations.

This module contains the core logic for CLI commands.
"""

import subprocess
from pathlib import Path
from typing import Callable, Dict, Optional

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

    # Step 1.5: Extract elements (figures, tables, equations) from PDF
    try:
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
        raise ExtractionError(f"Failed to extract elements from PDF: {e}")

    # Step 2: Organize into presentation structure
    try:
        organizer = SlideOrganizer(
            max_elements_per_slide=2,
            create_title_slide=True,
            create_outline_slide=False,  # Skip outline if no sections
        )

        presentation = organizer.organize(paper)
        progress()

    except Exception as e:
        raise GenerationError(f"Failed to organize slides: {e}")

    # Step 3: Generate LaTeX code
    try:
        generator = LaTeXGenerator()

        # Generate using Presentation.to_latex()
        latex_code = presentation.to_latex()

        # Ensure output directory exists
        config.output_directory.mkdir(parents=True, exist_ok=True)

        # Write LaTeX file
        output_name = pdf_path.stem
        tex_path = config.output_directory / f"{output_name}.tex"
        tex_path.write_text(latex_code)

        progress()

    except Exception as e:
        raise GenerationError(f"Failed to generate LaTeX: {e}")

    # Step 4: Compile to PDF (optional)
    pdf_output_path = None
    if compile_pdf:
        try:
            pdf_output_path = compile_latex(tex_path, config.output_directory)
            progress()
        except Exception as e:
            # Don't fail if compilation fails, just warn
            pdf_output_path = None

    return {
        "tex_path": tex_path,
        "pdf_path": pdf_output_path,
        "slide_count": len(presentation.slides),
        "presentation": presentation,
    }


def compile_latex(tex_path: Path, output_dir: Path) -> Path:
    """Compile LaTeX file to PDF.

    Args:
        tex_path: Path to .tex file
        output_dir: Output directory

    Returns:
        Path: Path to generated PDF

    Raises:
        CompilationError: If compilation fails
    """
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

                raise CompilationError(f"{error_msg}\n\nSee {log_path} for details")

        # Return path to PDF
        pdf_path = output_dir / f"{tex_path.stem}.pdf"
        if not pdf_path.exists():
            raise CompilationError(f"PDF was not generated: {pdf_path}")

        return pdf_path

    except subprocess.TimeoutExpired:
        raise CompilationError("LaTeX compilation timed out after 60 seconds")
    except FileNotFoundError:
        raise CompilationError(
            "pdflatex not found. Please install TeX Live or MiKTeX."
        )
    except Exception as e:
        if isinstance(e, CompilationError):
            raise
        raise CompilationError(f"Compilation error: {e}")


def generate_with_ai(
    paper: Paper,
    config: AppConfiguration,
    prompt_name: str,
    model: Optional[str],
) -> str:
    """Generate presentation content using AI (placeholder for future).

    Args:
        paper: Paper model
        config: Application configuration
        prompt_name: Name of prompt template
        model: Model to use

    Returns:
        str: AI-generated presentation outline

    Note:
        This is a placeholder for future AI integration.
        Current version uses rule-based slide organization.
    """
    # Load prompt template
    prompt_library_path = Path(__file__).parent.parent.parent.parent / "prompts" / "templates"
    library = PromptLibrary(library_path=prompt_library_path)
    template = library.get_template(prompt_name)

    # Prepare context
    paper_content = f"Title: {paper.title}\nAuthors: {', '.join(paper.authors)}"
    if paper.sections:
        paper_content += "\n\nSections:\n"
        for section in paper.sections:
            paper_content += f"- {section.title}\n"

    context = {"paper_content": paper_content}

    # Render prompt
    prompt = template.render(context)

    # Get AI service
    orchestrator = AIOrchestrator(config.ai_services)
    service = orchestrator.get_default_service()

    # Determine model
    if not model:
        if config.ai_services.default_provider == "openai":
            model = "gpt-4"
        elif config.ai_services.default_provider == "anthropic":
            model = "claude-3-opus-20240229"
        else:
            model = "default"

    # Create request
    request = AIRequest(
        prompt=prompt,
        model=model,
        max_tokens=2000,
        temperature=0.7,
    )

    # Generate with retry
    response = generate_with_retry(service, request)

    return response.content
