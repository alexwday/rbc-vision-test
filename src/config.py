"""
Environment Configuration - Centralized settings from environment variables.

This module provides configuration for the RBC Vision Test project. It supports
dual-environment operation: local development with OpenAI API keys, or RBC
production with OAuth authentication.

All configuration is loaded once at module import from environment variables.
"""

import logging
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logger = logging.getLogger(__name__)


class Config:
    """Application configuration loaded from environment variables at import time."""

    BASE_URL: str = os.getenv("AZURE_BASE_URL") or "https://api.openai.com/v1"

    OAUTH_URL: str = os.getenv("OAUTH_URL", "")
    OAUTH_CLIENT_ID: str = os.getenv("CLIENT_ID", "")
    OAUTH_CLIENT_SECRET: str = os.getenv("CLIENT_SECRET", "")

    @property
    def VISION_MODEL(self) -> str:
        """Get vision model from environment. Raises if not set."""
        model = os.getenv("VISION_MODEL")
        if not model:
            raise ValueError("VISION_MODEL environment variable is required")
        return model

    @classmethod
    def is_local_mode(cls) -> bool:
        """Check if running in local mode with OPENAI_API_KEY.

        Returns:
            True if OPENAI_API_KEY is set, False otherwise.
        """
        return bool(os.getenv("OPENAI_API_KEY"))

    def get_endpoint_info(self) -> dict:
        """Get information about the configured endpoint.

        Returns:
            Dict with base_url, model, and mode (local/rbc).
        """
        return {
            "base_url": self.BASE_URL,
            "model": self.VISION_MODEL,
            "mode": "local" if self.is_local_mode() else "rbc",
        }


config = Config()
