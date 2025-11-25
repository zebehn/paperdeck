"""Configuration models for PaperDeck.

This module defines configuration schemas for application settings, AI services,
and extraction parameters.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import ElementType


@dataclass
class ExtractionConfiguration:
    """Configuration for DocScalpel PDF element extraction."""

    confidence_threshold: float = 0.75
    element_types: List[ElementType] = field(
        default_factory=lambda: [ElementType.FIGURE, ElementType.TABLE, ElementType.EQUATION]
    )
    boundary_padding: int = 5
    max_pages: Optional[int] = None
    output_directory: Path = field(default_factory=lambda: Path("./extracted"))
    overwrite_existing: bool = False

    def __post_init__(self):
        """Validate extraction configuration."""
        if not 0.0 <= self.confidence_threshold <= 1.0:
            raise ValueError("confidence_threshold must be in range [0.0, 1.0]")

        if not self.element_types:
            raise ValueError("element_types must not be empty")

        valid_types = {ElementType.FIGURE, ElementType.TABLE, ElementType.EQUATION}
        if not set(self.element_types).issubset(valid_types):
            raise ValueError(f"element_types must be subset of {valid_types}")

        if self.boundary_padding < 0:
            raise ValueError("boundary_padding must be >= 0")

        if self.max_pages is not None and self.max_pages < 1:
            raise ValueError("max_pages must be > 0 if specified")

        # Ensure output_directory is Path object
        if isinstance(self.output_directory, str):
            self.output_directory = Path(self.output_directory)


@dataclass
class AIServiceConfiguration:
    """Configuration for AI service selection and credentials."""

    default_provider: str = "ollama"  # Changed to ollama for easier testing
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    ollama_base_url: str = "http://localhost:11434"
    lmstudio_base_url: str = "http://localhost:1234"
    max_retries: int = 3
    timeout_seconds: int = 60
    rate_limits: Dict[str, int] = field(
        default_factory=lambda: {"openai": 20, "anthropic": 15, "ollama": 100, "lmstudio": 100}
    )

    def __post_init__(self):
        """Validate AI service configuration."""
        valid_providers = {"openai", "anthropic", "ollama", "lmstudio"}
        if self.default_provider not in valid_providers:
            raise ValueError(f"default_provider must be in {valid_providers}")

        # Cloud providers require API keys
        if self.default_provider in ["openai", "anthropic"]:
            key_attr = f"{self.default_provider}_api_key"
            if not getattr(self, key_attr):
                raise ValueError(f"API key required for default_provider '{self.default_provider}'")

        if self.max_retries < 0:
            raise ValueError("max_retries must be >= 0")

        if self.timeout_seconds < 1:
            raise ValueError("timeout_seconds must be > 0")

    def validate_provider(self, provider: str) -> bool:
        """Validate that a specific provider is properly configured.

        Args:
            provider: Provider name to validate

        Returns:
            bool: True if provider is properly configured

        Raises:
            ValueError: If provider configuration is invalid
        """
        if provider not in {"openai", "anthropic", "ollama", "lmstudio"}:
            raise ValueError(f"Unknown provider: {provider}")

        # Cloud providers require API keys
        if provider in ["openai", "anthropic"]:
            key_attr = f"{provider}_api_key"
            if not getattr(self, key_attr):
                raise ValueError(f"API key required for provider '{provider}'")

        return True


@dataclass
class TextExtractionConfig:
    """Configuration for PDF text extraction."""

    # Feature toggle
    enabled: bool = True                # Whether to extract text at all

    # Extraction parameters
    header_margin: int = 50            # Pixels to exclude from top (headers)
    footer_margin: int = 50            # Pixels to exclude from bottom (footers)
    remove_image_text: bool = True     # Skip text embedded in images

    # Sanitization
    remove_page_numbers: bool = True   # Remove standalone page numbers
    remove_headers_footers: bool = True  # Pattern-based header/footer removal
    min_line_length: int = 3           # Minimum line length to keep

    # Context management
    max_tokens: Optional[int] = None   # Max tokens (None = use model default)
    reserve_output_fraction: float = 0.25  # Fraction reserved for output
    truncation_strategy: str = "end"   # "end" | "middle" | "priority_sections"

    # Performance
    timeout_seconds: float = 30.0      # Max time for extraction
    cache_extracted_text: bool = False  # Whether to cache extracted text

    @property
    def available_input_fraction(self) -> float:
        """Fraction of context available for input."""
        return 1.0 - self.reserve_output_fraction

    def validate(self) -> list[str]:
        """Validate configuration values.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        if self.header_margin < 0 or self.footer_margin < 0:
            errors.append("Margins must be non-negative")

        if not 0 < self.reserve_output_fraction < 1:
            errors.append("Reserve fraction must be between 0 and 1")

        if self.truncation_strategy not in ("end", "middle", "priority_sections"):
            errors.append(f"Invalid truncation strategy: {self.truncation_strategy}")

        if self.timeout_seconds <= 0:
            errors.append("Timeout must be positive")

        if self.min_line_length < 0:
            errors.append("min_line_length must be non-negative")

        return errors


@dataclass
class AppConfiguration:
    """Top-level application configuration."""

    ai_services: AIServiceConfiguration = field(default_factory=AIServiceConfiguration)
    prompt_library_path: Path = field(default_factory=lambda: Path("~/.paperdeck/prompts"))
    default_prompt: str = "default"
    default_theme: str = "Madrid"
    output_directory: Path = field(default_factory=lambda: Path("./paperdeck_output"))
    log_level: str = "INFO"
    extraction_config: ExtractionConfiguration = field(default_factory=ExtractionConfiguration)
    text_extraction: TextExtractionConfig = field(default_factory=TextExtractionConfig)

    def __post_init__(self):
        """Validate application configuration."""
        # Expand user paths
        if isinstance(self.prompt_library_path, str):
            self.prompt_library_path = Path(self.prompt_library_path)
        self.prompt_library_path = self.prompt_library_path.expanduser()

        if isinstance(self.output_directory, str):
            self.output_directory = Path(self.output_directory)
        self.output_directory = self.output_directory.expanduser()

        # Validate log level
        valid_log_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if self.log_level.upper() not in valid_log_levels:
            raise ValueError(f"log_level must be in {valid_log_levels}")

        # Normalize log level to uppercase
        self.log_level = self.log_level.upper()

    def validate(self) -> List[str]:
        """Validate configuration and return list of errors.

        Returns:
            List[str]: List of validation error messages (empty if valid)
        """
        errors = []

        # Check prompt library path exists
        if not self.prompt_library_path.exists():
            errors.append(f"Prompt library path does not exist: {self.prompt_library_path}")

        # Check output directory is writable (or parent exists for creation)
        if self.output_directory.exists():
            if not self.output_directory.is_dir():
                errors.append(f"Output path is not a directory: {self.output_directory}")
        else:
            parent = self.output_directory.parent
            if not parent.exists():
                errors.append(
                    f"Parent directory for output does not exist: {parent}"
                )

        # Validate extraction config output directory
        extraction_output = self.extraction_config.output_directory
        if extraction_output.exists():
            if not extraction_output.is_dir():
                errors.append(
                    f"Extraction output path is not a directory: {extraction_output}"
                )

        return errors

    @classmethod
    def load_from_file(cls, path: Path) -> "AppConfiguration":
        """Load configuration from YAML/JSON file.

        Args:
            path: Path to configuration file

        Returns:
            AppConfiguration: Loaded configuration

        Note:
            This is a placeholder. Actual implementation will parse YAML/JSON.
        """
        # TODO: Implement actual file loading with PyYAML
        return cls()

    def save_to_file(self, path: Path) -> None:
        """Save configuration to file.

        Args:
            path: Path to save configuration

        Note:
            This is a placeholder. Actual implementation will write YAML/JSON.
        """
        # TODO: Implement actual file saving with PyYAML
        pass
