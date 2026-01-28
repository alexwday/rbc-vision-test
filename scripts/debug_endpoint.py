#!/usr/bin/env python3
"""
Debug Endpoint - Exploratory script for debugging endpoint issues.

Provides detailed information about the endpoint configuration and makes
a simple request with full error output. Useful for troubleshooting
connection or parameter issues in the RBC environment.
"""

import base64
import json
import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import config
from src.oauth import fetch_oauth_token
from src.rbc_security import configure_rbc_security_certs

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

TEST_IMAGE_PATH = Path(__file__).parent.parent / "tests" / "sample_image.png"


def main():
    print("=" * 70)
    print("ENDPOINT DEBUG TOOL")
    print("=" * 70)

    print("\n" + "-" * 70)
    print("ENVIRONMENT VARIABLES")
    print("-" * 70)
    env_vars = [
        "AZURE_BASE_URL",
        "OAUTH_URL",
        "CLIENT_ID",
        "CLIENT_SECRET",
        "OPENAI_API_KEY",
        "VISION_MODEL",
    ]
    for var in env_vars:
        value = os.getenv(var, "")
        if var in ["CLIENT_SECRET", "OPENAI_API_KEY"] and value:
            display = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "***"
        else:
            display = value or "(not set)"
        print(f"  {var}: {display}")

    print("\n" + "-" * 70)
    print("RESOLVED CONFIGURATION")
    print("-" * 70)
    print(f"  BASE_URL:          {config.BASE_URL}")
    print(f"  OAUTH_URL:         {config.OAUTH_URL or '(not set)'}")
    print(f"  OAUTH_CLIENT_ID:   {config.OAUTH_CLIENT_ID or '(not set)'}")
    print(f"  VISION_MODEL:      {config.VISION_MODEL}")
    print(f"  Mode:              {'local' if config.is_local_mode() else 'rbc'}")

    print("\n" + "-" * 70)
    print("RBC SECURITY")
    print("-" * 70)
    cert_status = configure_rbc_security_certs()
    print(f"  Status: {cert_status or 'Not available (using system certs)'}")

    print("\n" + "-" * 70)
    print("AUTHENTICATION")
    print("-" * 70)
    try:
        token, auth_info = fetch_oauth_token()
        print(f"  Method: {auth_info['method']}")
        print(f"  Token acquired: Yes (length: {len(token)})")
    except Exception as e:
        print(f"  FAILED: {type(e).__name__}: {e}")
        return 1

    print("\n" + "-" * 70)
    print("TEST IMAGE")
    print("-" * 70)
    if TEST_IMAGE_PATH.exists():
        print(f"  Path: {TEST_IMAGE_PATH}")
        print(f"  Size: {TEST_IMAGE_PATH.stat().st_size} bytes")
        with open(TEST_IMAGE_PATH, "rb") as f:
            base64_image = base64.standard_b64encode(f.read()).decode("utf-8")
        print(f"  Base64 length: {len(base64_image)}")
    else:
        print(f"  NOT FOUND: {TEST_IMAGE_PATH}")
        base64_image = None

    print("\n" + "-" * 70)
    print("MAKING RAW API CALL")
    print("-" * 70)

    from openai import OpenAI

    client = OpenAI(api_key=token, base_url=config.BASE_URL)

    if base64_image:
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Say 'I can see the image' if you see an image."},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}",
                            "detail": "low"
                        }
                    }
                ]
            }
        ]
    else:
        messages = [
            {"role": "user", "content": "Say 'hello' to confirm the connection works."}
        ]

    request_params = {
        "model": config.VISION_MODEL,
        "messages": messages,
        "max_tokens": 50,
    }

    print(f"\nRequest Parameters:")
    print(f"  model: {request_params['model']}")
    print(f"  max_tokens: {request_params['max_tokens']}")
    print(f"  message type: {'vision' if base64_image else 'text'}")

    print("\nSending request...")
    try:
        response = client.chat.completions.create(**request_params)

        print("\n" + "=" * 70)
        print("RAW RESPONSE")
        print("=" * 70)
        print(json.dumps(response.model_dump(), indent=2, default=str))

        print("\n" + "-" * 70)
        print("EXTRACTED VALUES")
        print("-" * 70)
        print(f"  Response Model: {response.model}")
        print(f"  Finish Reason: {response.choices[0].finish_reason}")
        print(f"  Content: {response.choices[0].message.content}")
        if response.usage:
            print(f"  Prompt Tokens: {response.usage.prompt_tokens}")
            print(f"  Completion Tokens: {response.usage.completion_tokens}")
            print(f"  Total Tokens: {response.usage.total_tokens}")

        print("\n" + "=" * 70)
        print("SUCCESS")
        print("=" * 70)
        return 0

    except Exception as e:
        print("\n" + "=" * 70)
        print("ERROR DETAILS")
        print("=" * 70)
        print(f"Exception Type: {type(e).__name__}")
        print(f"Exception Message: {e}")

        if hasattr(e, "response"):
            print(f"\nHTTP Response Status: {e.response.status_code}")
            print(f"HTTP Response Headers: {dict(e.response.headers)}")
            try:
                print(f"HTTP Response Body: {e.response.text}")
            except Exception:
                pass

        if hasattr(e, "body"):
            print(f"\nError Body: {e.body}")

        import traceback
        print("\nFull Traceback:")
        traceback.print_exc()

        return 1


if __name__ == "__main__":
    sys.exit(main())
