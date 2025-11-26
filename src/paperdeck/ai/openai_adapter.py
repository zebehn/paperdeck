"""OpenAI GPT adapter implementation.

This module provides the OpenAIAdapter class that implements the AIService interface
for OpenAI's GPT models.
"""

from typing import Optional

from .service import AIRequest, AIResponse, AIService
from ..core.exceptions import (
    AIServiceError,
    ConfigurationError,
    RateLimitExceededError,
    ServiceUnavailableError,
)


class OpenAIAdapter(AIService):
    """Adapter for OpenAI GPT models."""

    def __init__(self, api_key: str, base_url: Optional[str] = None):
        """Initialize OpenAI adapter.

        Args:
            api_key: OpenAI API key
            base_url: Optional custom API base URL

        Raises:
            ValueError: If API key is None or empty
        """
        if not api_key:
            raise ValueError("OpenAI API key is required")

        self.api_key = api_key
        self.base_url = base_url
        self._client = None

    def _get_client(self):
        """Get or create OpenAI client.

        Returns:
            OpenAI client instance
        """
        if self._client is None:
            try:
                from openai import OpenAI

                if self.base_url:
                    self._client = OpenAI(api_key=self.api_key, base_url=self.base_url)
                else:
                    self._client = OpenAI(api_key=self.api_key)
            except ImportError:
                raise ConfigurationError(
                    "openai package not installed. Install with: pip install openai"
                )

        return self._client

    def generate(self, request: AIRequest) -> AIResponse:
        """Generate content using OpenAI GPT.

        Args:
            request: AIRequest with prompt and parameters

        Returns:
            AIResponse with generated content

        Raises:
            ServiceUnavailableError: If OpenAI service is unavailable
            RateLimitExceededError: If rate limit is exceeded
            AIServiceError: For other API errors
        """
        try:
            import logging
            logger = logging.getLogger(__name__)

            client = self._get_client()

            # Upload PDF file if provided
            file_id = None
            if request.pdf_file_path:
                logger.info(f"Uploading PDF file to OpenAI: {request.pdf_file_path}")
                try:
                    with open(request.pdf_file_path, "rb") as pdf_file:
                        file_obj = client.files.create(
                            file=pdf_file,
                            purpose="assistants"
                        )
                        file_id = file_obj.id
                        logger.info(f"PDF file uploaded successfully: {file_id}")
                except Exception as e:
                    logger.error(f"Failed to upload PDF file: {e}")
                    raise AIServiceError(f"PDF file upload failed: {e}")

            # Build messages
            messages = []
            if request.system_instructions:
                messages.append({"role": "system", "content": request.system_instructions})

            # If PDF file was uploaded, use multipart content
            if file_id:
                user_content = [
                    {"type": "text", "text": request.prompt},
                    {"type": "file", "file": {"file_id": file_id}}
                ]
                messages.append({"role": "user", "content": user_content})
            else:
                # Text-only request
                messages.append({"role": "user", "content": request.prompt})

            # Call OpenAI API
            logger.info(f"Calling OpenAI API with model {request.model}")

            # GPT-5 models use max_completion_tokens instead of max_tokens
            if request.model.startswith("gpt-5"):
                response = client.chat.completions.create(
                    model=request.model,
                    messages=messages,
                    max_completion_tokens=request.max_tokens,
                    temperature=request.temperature,
                )
            else:
                response = client.chat.completions.create(
                    model=request.model,
                    messages=messages,
                    max_tokens=request.max_tokens,
                    temperature=request.temperature,
                )

            # Extract response
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else None
            finish_reason = response.choices[0].finish_reason

            # Clean up uploaded file if it exists
            if file_id:
                try:
                    logger.info(f"Deleting uploaded PDF file: {file_id}")
                    client.files.delete(file_id)
                    logger.info("PDF file deleted successfully")
                except Exception as e:
                    logger.warning(f"Failed to delete uploaded file {file_id}: {e}")

            return AIResponse(
                content=content,
                model=response.model,
                tokens_used=tokens_used,
                finish_reason=finish_reason,
                metadata={"provider": "openai", "file_id": file_id if file_id else None},
            )

        except ImportError as e:
            raise ConfigurationError(f"OpenAI package not available: {e}")
        except Exception as e:
            error_msg = str(e).lower()

            # Map OpenAI errors to our exceptions
            if "rate" in error_msg and "limit" in error_msg:
                raise RateLimitExceededError(f"OpenAI rate limit exceeded: {e}")
            elif "unavailable" in error_msg or "503" in error_msg:
                raise ServiceUnavailableError(f"OpenAI service unavailable: {e}")
            elif "api key" in error_msg or "401" in error_msg or "403" in error_msg:
                raise ConfigurationError(f"OpenAI authentication failed: {e}")
            else:
                raise AIServiceError(f"OpenAI API error: {e}")

    def is_available(self) -> bool:
        """Check if OpenAI service is available.

        Returns:
            bool: True if service is reachable
        """
        try:
            client = self._get_client()
            # Try to list models as a connectivity check
            models = client.models.list()
            return True
        except:
            return False

    def validate_config(self) -> bool:
        """Validate OpenAI configuration.

        Returns:
            bool: True if configuration is valid

        Raises:
            ConfigurationError: If configuration is invalid
        """
        if not self.api_key:
            raise ConfigurationError("OpenAI API key is required")

        # API key format validation (basic check)
        if not self.api_key.startswith("sk-"):
            raise ConfigurationError("OpenAI API key should start with 'sk-'")

        return True
