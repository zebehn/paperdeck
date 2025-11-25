"""Retry logic for AI service calls.

This module provides retry functionality with exponential backoff for handling
transient failures and rate limits.
"""

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .service import AIRequest, AIResponse, AIService
from ..core.exceptions import RateLimitExceededError, ServiceUnavailableError


@retry(
    retry=retry_if_exception_type((ServiceUnavailableError, RateLimitExceededError)),
    wait=wait_exponential(multiplier=2, min=1, max=120),
    stop=stop_after_attempt(5),
)
def generate_with_retry(service: AIService, request: AIRequest) -> AIResponse:
    """Generate content with automatic retry on transient failures.

    Args:
        service: AIService instance to use
        request: AIRequest with generation parameters

    Returns:
        AIResponse: Generated content

    Raises:
        ServiceUnavailableError: If service remains unavailable after retries
        RateLimitExceededError: If rate limit persists after retries
        AIServiceError: For other non-retryable errors

    Note:
        Automatically retries on:
        - ServiceUnavailableError (503 errors)
        - RateLimitExceededError (429 errors)

        Does NOT retry on:
        - Authentication errors (401, 403)
        - Validation errors (400)
        - Other permanent failures
    """
    return service.generate(request)
