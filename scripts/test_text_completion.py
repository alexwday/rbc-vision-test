#!/usr/bin/env python3
"""
Text Completion Test - Sanity check that the LLM connection works.

Run this first to verify basic connectivity before testing vision capabilities.
"""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import config
from src.oauth import fetch_oauth_token
from src.rbc_security import configure_rbc_security_certs
from src.llm import execute_llm_call

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    print("=" * 60)
    print("TEXT COMPLETION TEST")
    print("=" * 60)

    endpoint_info = config.get_endpoint_info()
    print(f"\nEndpoint Configuration:")
    print(f"  Mode:     {endpoint_info['mode']}")
    print(f"  Base URL: {endpoint_info['base_url']}")
    print(f"  Model:    {endpoint_info['model']}")

    print("\n1. Configuring RBC security (if available)...")
    cert_status = configure_rbc_security_certs()
    print(f"   Certificate status: {cert_status or 'Not required (local mode)'}")

    print("\n2. Fetching authentication token...")
    try:
        token, auth_info = fetch_oauth_token()
        print(f"   Auth method: {auth_info['method']}")
    except Exception as e:
        print(f"   ERROR: Failed to get token: {e}")
        return 1

    print("\n3. Sending text completion request...")
    messages = [
        {"role": "user", "content": "Hello! Please respond with a brief greeting."}
    ]

    try:
        response, usage = execute_llm_call(
            oauth_token=token,
            messages=messages,
            max_tokens=100,
        )

        print("\n" + "=" * 60)
        print("RESPONSE")
        print("=" * 60)
        print(response.choices[0].message.content)

        if usage:
            print("\n" + "-" * 40)
            print("Token Usage:")
            print(f"  Prompt tokens:     {usage['prompt_tokens']}")
            print(f"  Completion tokens: {usage['completion_tokens']}")
            print(f"  Total tokens:      {usage['total_tokens']}")
            print(f"  Response time:     {usage['response_time_ms']}ms")

        print("\n" + "=" * 60)
        print("SUCCESS - Text completion working!")
        print("=" * 60)
        return 0

    except Exception as e:
        print(f"\nERROR: {type(e).__name__}: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
