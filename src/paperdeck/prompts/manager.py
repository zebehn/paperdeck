"""Prompt template management.

This module defines models for prompt templates and the prompt library,
enabling users to customize AI-generated presentations.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple


@dataclass
class PromptTemplate:
    """Represents a reusable prompt template for presentation generation."""

    name: str
    description: str
    content: str
    style: str
    detail_level: str
    is_builtin: bool = False
    placeholders: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate and initialize prompt template."""
        # Validate name uniqueness (will be enforced by library)
        if not self.name:
            raise ValueError("name must not be empty")

        # Validate balanced braces
        if not self._has_balanced_braces(self.content):
            raise ValueError("content must have balanced braces")

        # Validate style
        valid_styles = {"technical", "accessible", "pedagogical", "custom"}
        if self.style not in valid_styles:
            raise ValueError(f"style must be in {valid_styles}")

        # Validate detail level
        valid_levels = {"low", "medium", "high"}
        if self.detail_level not in valid_levels:
            raise ValueError(f"detail_level must be in {valid_levels}")

        # Extract placeholders (optional - for backward compatibility)
        if not self.placeholders:
            self.placeholders = self._extract_placeholders(self.content)

    def _has_balanced_braces(self, text: str) -> bool:
        """Check if braces are balanced.

        Args:
            text: Text to check

        Returns:
            bool: True if braces are balanced
        """
        count = 0
        for char in text:
            if char == "{":
                count += 1
            elif char == "}":
                count -= 1
            if count < 0:
                return False
        return count == 0

    def _extract_placeholders(self, text: str) -> List[str]:
        """Extract placeholder names from template content.

        Args:
            text: Template content

        Returns:
            List[str]: List of placeholder names (without braces)
        """
        # Match {placeholder_name} pattern
        pattern = r"\{([a-z_]+)\}"
        matches = re.findall(pattern, text)
        return list(set(matches))  # Remove duplicates

    def render(self, context: Optional[Dict[str, str]] = None) -> str:
        """Return template content (placeholder replacement is optional).

        Args:
            context: Optional dictionary mapping placeholder names to values

        Returns:
            str: Template content with optional placeholder replacement

        Note:
            Placeholders are optional. If context is provided, placeholders will be replaced.
            If context is None or empty, template content is returned as-is.
        """
        if not context or not self.placeholders:
            return self.content

        rendered = self.content

        # Replace placeholders if provided in context
        for key, value in context.items():
            placeholder = f"{{{key}}}"
            if placeholder in rendered:
                rendered = rendered.replace(placeholder, value)

        return rendered

    def validate(self) -> Tuple[bool, Optional[str]]:
        """Check template validity.

        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        try:
            # Check balanced braces
            if not self._has_balanced_braces(self.content):
                return False, "Unbalanced braces in template content"

            # Check content length
            if len(self.content) > 10000:
                return False, "Template content exceeds 10,000 characters"

            return True, None

        except Exception as e:
            return False, f"Validation error: {str(e)}"


@dataclass
class PromptLibrary:
    """Collection of available prompt templates."""

    library_path: Path
    templates: Dict[str, PromptTemplate] = field(default_factory=dict)
    metadata_file: Path = field(init=False)

    def __post_init__(self):
        """Initialize prompt library."""
        # Expand user path
        if isinstance(self.library_path, str):
            self.library_path = Path(self.library_path)
        self.library_path = self.library_path.expanduser()

        # Set metadata file path
        self.metadata_file = self.library_path / "_metadata.json"

        # Validate library path
        if not self.library_path.exists():
            raise ValueError(f"Prompt library path does not exist: {self.library_path}")

        if not self.library_path.is_dir():
            raise ValueError(f"Prompt library path is not a directory: {self.library_path}")

    def list_templates(self) -> List[PromptTemplate]:
        """Get all available templates.

        Returns:
            List[PromptTemplate]: All loaded templates
        """
        return list(self.templates.values())

    def get_template(self, name: str) -> PromptTemplate:
        """Load specific template by name.

        Args:
            name: Template name

        Returns:
            PromptTemplate: The requested template

        Raises:
            KeyError: If template not found
        """
        if name not in self.templates:
            # Try to load from file
            template_file = self.library_path / f"{name}.txt"
            if template_file.exists():
                self._load_template_from_file(name, template_file)
            else:
                raise KeyError(f"Template '{name}' not found in library")

        return self.templates[name]

    def _load_template_from_file(self, name: str, file_path: Path) -> None:
        """Load template from file.

        Args:
            name: Template name
            file_path: Path to template file
        """
        import json

        # Read template content
        content = file_path.read_text()

        # Try to load metadata
        metadata = {}
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, "r") as f:
                    all_metadata = json.load(f)
                    metadata = all_metadata.get(name, {})
            except Exception:
                pass  # Use defaults if metadata fails to load

        # Create template with metadata or defaults
        template = PromptTemplate(
            name=metadata.get("name", name),
            description=metadata.get("description", f"Template: {name}"),
            content=content,
            style=metadata.get("style", "custom"),
            detail_level=metadata.get("detail_level", "medium"),
            is_builtin=metadata.get("is_builtin", False),
        )
        self.templates[name] = template

    def add_template(self, template: PromptTemplate) -> None:
        """Add custom template to library.

        Args:
            template: Template to add

        Raises:
            ValueError: If template name already exists
        """
        if template.name in self.templates:
            raise ValueError(f"Template '{template.name}' already exists")

        # Validate template
        is_valid, error = template.validate()
        if not is_valid:
            raise ValueError(f"Invalid template: {error}")

        self.templates[template.name] = template

        # TODO: Persist to file and update metadata

    def remove_template(self, name: str) -> None:
        """Remove user template (cannot remove builtin).

        Args:
            name: Template name to remove

        Raises:
            KeyError: If template not found
            ValueError: If attempting to remove builtin template
        """
        if name not in self.templates:
            raise KeyError(f"Template '{name}' not found")

        if self.templates[name].is_builtin:
            raise ValueError(f"Cannot remove builtin template '{name}'")

        del self.templates[name]

        # TODO: Remove file and update metadata

    def validate_all(self) -> Dict[str, Tuple[bool, Optional[str]]]:
        """Validate all templates.

        Returns:
            Dict[str, Tuple[bool, Optional[str]]]: Validation results per template
        """
        results = {}
        for name, template in self.templates.items():
            results[name] = template.validate()
        return results
