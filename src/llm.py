"""
LLM Connector - OpenAI API client with retry logic.

This module provides the interface to OpenAI-compatible APIs (Azure or direct)
for vision and text completion calls. Simplified from IRIS to focus only on
non-streaming chat completions with vision support.

Includes automatic retry on transient failures with configurable attempts
and backoff delay.
"""

import logging
import time
from typing import Any, Optional

from openai import OpenAI, OpenAIError

from .config import config

logger = logging.getLogger(__name__)
logging.getLogger("openai").setLevel(logging.INFO)

_REQUEST_TIMEOUT = 180
_MAX_RETRY_ATTEMPTS = 3
_RETRY_DELAY_SECONDS = 2


class LLMConnectorError(Exception):
    """Exception class for LLM connector errors."""


UsageDetails = Optional[dict[str, Any]]


def _build_usage_details(api_response: Any, response_time_ms: int) -> UsageDetails:
    """Build usage details dict from API response."""
    if not hasattr(api_response, "usage") or not api_response.usage:
        return None

    return {
        "model": api_response.model,
        "prompt_tokens": api_response.usage.prompt_tokens or 0,
        "completion_tokens": api_response.usage.completion_tokens or 0,
        "total_tokens": api_response.usage.total_tokens or 0,
        "response_time_ms": response_time_ms,
    }


def execute_llm_call(oauth_token: str, **params) -> tuple[Any, UsageDetails]:
    """Execute an OpenAI API call with automatic retry on failure.

    Args:
        oauth_token: OAuth token (RBC) or OpenAI API key (local).
        **params: OpenAI API parameters (model, messages, max_tokens, etc.).

    Returns:
        Tuple of (api_response, usage_details).

    Raises:
        LLMConnectorError: If the call fails after all retry attempts.
    """
    base_url = config.BASE_URL
    client = OpenAI(api_key=oauth_token, base_url=base_url)
    logger.info("Connecting to OpenAI API at %s", base_url)

    if "timeout" not in params:
        params["timeout"] = _REQUEST_TIMEOUT

    model_name = params.get("model", config.VISION_MODEL)
    if "model" not in params:
        params["model"] = model_name

    last_exception = None

    for attempt_num in range(1, _MAX_RETRY_ATTEMPTS + 1):
        start_time = time.time()

        try:
            api_response = client.chat.completions.create(**params)
            response_time_ms = int((time.time() - start_time) * 1000)

            return api_response, _build_usage_details(api_response, response_time_ms)

        except (
            ValueError,
            TypeError,
            KeyError,
            RuntimeError,
            OSError,
            OpenAIError,
        ) as exc:
            last_exception = exc
            logger.warning(
                "LLM call attempt %d/%d failed after %.2f seconds: %s - %s",
                attempt_num,
                _MAX_RETRY_ATTEMPTS,
                time.time() - start_time,
                type(exc).__name__,
                str(exc),
            )

            if attempt_num < _MAX_RETRY_ATTEMPTS:
                time.sleep(_RETRY_DELAY_SECONDS)

    logger.error("LLM call failed after %d attempts", _MAX_RETRY_ATTEMPTS)
    raise LLMConnectorError(
        f"Failed to complete OpenAI API call: {last_exception}"
    ) from last_exception
