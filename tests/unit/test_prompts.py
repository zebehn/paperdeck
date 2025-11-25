"""Unit tests for prompt management models."""

import pytest
from pathlib import Path

from paperdeck.prompts.manager import PromptLibrary, PromptTemplate


class TestPromptTemplate:
    """Tests for PromptTemplate model."""

    def test_valid_prompt_template(self):
        """Test creating a valid prompt template."""
        template = PromptTemplate(
            name="default",
            description="Default prompt",
            content="Generate a presentation from this paper: {paper_content}",
            style="technical",
            detail_level="medium",
        )
        assert template.name == "default"
        assert template.style == "technical"
        assert "{paper_content}" in template.content

    def test_placeholders_extracted_automatically(self):
        """Test that placeholders are extracted from content."""
        template = PromptTemplate(
            name="test",
            description="Test",
            content="Paper: {paper_content}, Author: {authors}, Title: {title}",
            style="technical",
            detail_level="medium",
        )
        assert "paper_content" in template.placeholders
        assert "authors" in template.placeholders
        assert "title" in template.placeholders
        assert len(template.placeholders) == 3

    def test_missing_required_placeholder_raises_error(self):
        """Test that missing {paper_content} raises ValueError."""
        with pytest.raises(ValueError, match="must contain {paper_content} placeholder"):
            PromptTemplate(
                name="invalid",
                description="Invalid",
                content="This template is missing the required placeholder",
                style="technical",
                detail_level="medium",
            )

    def test_unbalanced_braces_raise_error(self):
        """Test that unbalanced braces raise ValueError."""
        with pytest.raises(ValueError, match="balanced braces"):
            PromptTemplate(
                name="invalid",
                description="Invalid",
                content="Paper: {paper_content with unclosed brace",
                style="technical",
                detail_level="medium",
            )

        with pytest.raises(ValueError, match="balanced braces"):
            PromptTemplate(
                name="invalid",
                description="Invalid",
                content="Paper: }paper_content} extra closing",
                style="technical",
                detail_level="medium",
            )

    def test_invalid_style_raises_error(self):
        """Test that invalid style raises ValueError."""
        with pytest.raises(ValueError, match="style must be in"):
            PromptTemplate(
                name="test",
                description="Test",
                content="Paper: {paper_content}",
                style="invalid_style",
                detail_level="medium",
            )

    def test_invalid_detail_level_raises_error(self):
        """Test that invalid detail level raises ValueError."""
        with pytest.raises(ValueError, match="detail_level must be in"):
            PromptTemplate(
                name="test",
                description="Test",
                content="Paper: {paper_content}",
                style="technical",
                detail_level="invalid",
            )

    def test_render_with_valid_context(self):
        """Test rendering template with valid context."""
        template = PromptTemplate(
            name="test",
            description="Test",
            content="Paper: {paper_content}, Title: {title}",
            style="technical",
            detail_level="medium",
        )
        result = template.render({
            "paper_content": "This is a paper about AI",
            "title": "AI Research",
        })
        assert result == "Paper: This is a paper about AI, Title: AI Research"

    def test_render_missing_placeholder_raises_error(self):
        """Test that missing placeholder in context raises KeyError."""
        template = PromptTemplate(
            name="test",
            description="Test",
            content="Paper: {paper_content}, Title: {title}",
            style="technical",
            detail_level="medium",
        )
        with pytest.raises(KeyError, match="Required placeholder"):
            template.render({"paper_content": "Some content"})  # Missing 'title'

    def test_validate_returns_true_for_valid_template(self):
        """Test that validate returns True for valid template."""
        template = PromptTemplate(
            name="test",
            description="Test",
            content="Paper: {paper_content}",
            style="technical",
            detail_level="medium",
        )
        is_valid, error = template.validate()
        assert is_valid is True
        assert error is None

    def test_validate_detects_unbalanced_braces(self):
        """Test that validate detects unbalanced braces."""
        # Create template with valid constructor, then break it
        template = PromptTemplate(
            name="test",
            description="Test",
            content="Paper: {paper_content}",
            style="technical",
            detail_level="medium",
        )
        # Manually break the content to test validation
        template.content = "Paper: {paper_content with unclosed"

        is_valid, error = template.validate()
        assert is_valid is False
        assert "Unbalanced braces" in error

    def test_validate_detects_missing_required_placeholder(self):
        """Test that validate detects missing required placeholder."""
        template = PromptTemplate(
            name="test",
            description="Test",
            content="Paper: {paper_content}",
            style="technical",
            detail_level="medium",
        )
        # Manually remove required placeholder
        template.content = "Paper: just some text"

        is_valid, error = template.validate()
        assert is_valid is False
        assert "paper_content" in error

    def test_validate_detects_excessive_length(self):
        """Test that validate detects content over 10,000 characters."""
        template = PromptTemplate(
            name="test",
            description="Test",
            content="Paper: {paper_content}",
            style="technical",
            detail_level="medium",
        )
        # Make content too long
        template.content = "a" * 10001 + " {paper_content}"

        is_valid, error = template.validate()
        assert is_valid is False
        assert "10,000 characters" in error


class TestPromptLibrary:
    """Tests for PromptLibrary model."""

    def test_valid_prompt_library(self, tmp_path):
        """Test creating a valid prompt library."""
        library_path = tmp_path / "prompts"
        library_path.mkdir()
        (library_path / "_metadata.json").write_text("{}")

        library = PromptLibrary(library_path=library_path)
        assert library.library_path == library_path
        assert library.metadata_file == library_path / "_metadata.json"

    def test_nonexistent_library_path_raises_error(self):
        """Test that nonexistent path raises ValueError."""
        with pytest.raises(ValueError, match="does not exist"):
            PromptLibrary(library_path=Path("/nonexistent/path"))

    def test_non_directory_path_raises_error(self, tmp_path):
        """Test that non-directory path raises ValueError."""
        file_path = tmp_path / "not_a_directory"
        file_path.write_text("content")

        with pytest.raises(ValueError, match="not a directory"):
            PromptLibrary(library_path=file_path)

    def test_list_templates_returns_all(self, tmp_path):
        """Test that list_templates returns all loaded templates."""
        library_path = tmp_path / "prompts"
        library_path.mkdir()

        library = PromptLibrary(library_path=library_path)

        # Add some templates
        template1 = PromptTemplate(
            name="template1",
            description="Test 1",
            content="Paper: {paper_content}",
            style="technical",
            detail_level="medium",
        )
        template2 = PromptTemplate(
            name="template2",
            description="Test 2",
            content="Content: {paper_content}",
            style="accessible",
            detail_level="low",
        )

        library.templates["template1"] = template1
        library.templates["template2"] = template2

        templates = library.list_templates()
        assert len(templates) == 2
        assert any(t.name == "template1" for t in templates)
        assert any(t.name == "template2" for t in templates)

    def test_get_template_returns_existing(self, tmp_path):
        """Test that get_template returns existing template."""
        library_path = tmp_path / "prompts"
        library_path.mkdir()

        library = PromptLibrary(library_path=library_path)

        template = PromptTemplate(
            name="test",
            description="Test",
            content="Paper: {paper_content}",
            style="technical",
            detail_level="medium",
        )
        library.templates["test"] = template

        retrieved = library.get_template("test")
        assert retrieved.name == "test"
        assert retrieved == template

    def test_get_template_loads_from_file(self, tmp_path):
        """Test that get_template loads from file if not in memory."""
        library_path = tmp_path / "prompts"
        library_path.mkdir()

        # Create a template file
        template_file = library_path / "fromfile.txt"
        template_file.write_text("Paper content: {paper_content}")

        library = PromptLibrary(library_path=library_path)

        # Template not in memory yet
        assert "fromfile" not in library.templates

        # Get template should load it
        template = library.get_template("fromfile")
        assert template.name == "fromfile"
        assert "fromfile" in library.templates

    def test_get_template_raises_error_if_not_found(self, tmp_path):
        """Test that get_template raises KeyError if template not found."""
        library_path = tmp_path / "prompts"
        library_path.mkdir()

        library = PromptLibrary(library_path=library_path)

        with pytest.raises(KeyError, match="not found"):
            library.get_template("nonexistent")

    def test_add_template_adds_to_library(self, tmp_path):
        """Test that add_template adds template to library."""
        library_path = tmp_path / "prompts"
        library_path.mkdir()

        library = PromptLibrary(library_path=library_path)

        template = PromptTemplate(
            name="new_template",
            description="New",
            content="Paper: {paper_content}",
            style="custom",
            detail_level="high",
        )

        library.add_template(template)
        assert "new_template" in library.templates
        assert library.templates["new_template"] == template

    def test_add_template_raises_error_if_exists(self, tmp_path):
        """Test that add_template raises ValueError if template exists."""
        library_path = tmp_path / "prompts"
        library_path.mkdir()

        library = PromptLibrary(library_path=library_path)

        template1 = PromptTemplate(
            name="duplicate",
            description="First",
            content="Paper: {paper_content}",
            style="technical",
            detail_level="medium",
        )

        library.add_template(template1)

        # Try to add another with same name
        template2 = PromptTemplate(
            name="duplicate",
            description="Second",
            content="Content: {paper_content}",
            style="technical",
            detail_level="medium",
        )

        with pytest.raises(ValueError, match="already exists"):
            library.add_template(template2)

    def test_remove_template_removes_from_library(self, tmp_path):
        """Test that remove_template removes user template."""
        library_path = tmp_path / "prompts"
        library_path.mkdir()

        library = PromptLibrary(library_path=library_path)

        template = PromptTemplate(
            name="removable",
            description="Test",
            content="Paper: {paper_content}",
            style="custom",
            detail_level="medium",
            is_builtin=False,
        )

        library.templates["removable"] = template
        assert "removable" in library.templates

        library.remove_template("removable")
        assert "removable" not in library.templates

    def test_remove_template_raises_error_for_builtin(self, tmp_path):
        """Test that remove_template raises error for builtin templates."""
        library_path = tmp_path / "prompts"
        library_path.mkdir()

        library = PromptLibrary(library_path=library_path)

        template = PromptTemplate(
            name="builtin",
            description="Builtin",
            content="Paper: {paper_content}",
            style="technical",
            detail_level="medium",
            is_builtin=True,
        )

        library.templates["builtin"] = template

        with pytest.raises(ValueError, match="Cannot remove builtin"):
            library.remove_template("builtin")

    def test_validate_all_returns_all_results(self, tmp_path):
        """Test that validate_all returns validation results for all templates."""
        library_path = tmp_path / "prompts"
        library_path.mkdir()

        library = PromptLibrary(library_path=library_path)

        # Add valid template
        template1 = PromptTemplate(
            name="valid",
            description="Valid",
            content="Paper: {paper_content}",
            style="technical",
            detail_level="medium",
        )

        # Add template that will become invalid
        template2 = PromptTemplate(
            name="invalid",
            description="Invalid",
            content="Paper: {paper_content}",
            style="technical",
            detail_level="medium",
        )
        template2.content = "broken content"  # Break it

        library.templates["valid"] = template1
        library.templates["invalid"] = template2

        results = library.validate_all()

        assert len(results) == 2
        assert "valid" in results
        assert "invalid" in results

        valid_result, valid_error = results["valid"]
        assert valid_result is True
        assert valid_error is None

        invalid_result, invalid_error = results["invalid"]
        assert invalid_result is False
        assert invalid_error is not None
