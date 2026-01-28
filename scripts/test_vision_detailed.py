#!/usr/bin/env python3
"""
Detailed Vision Test - Comprehensive exploration of vision capabilities.

Tests vision with different detail levels and inspects full response structure.
Useful for understanding how the endpoint handles various image parameters.
"""

import base64
import json
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

TEST_IMAGE_PATH = Path(__file__).parent.parent / "tests" / "sample_image.png"


def encode_image_base64(image_path: Path) -> str:
    """Read and base64 encode an image file."""
    with open(image_path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode("utf-8")


def test_vision_with_detail(token: str, base64_image: str, detail: str) -> dict:
    """Run a vision test with a specific detail level."""
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Describe this image in one sentence."},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{base64_image}",
                        "detail": detail
                    }
                }
            ]
        }
    ]

    response, usage = execute_llm_call(
        oauth_token=token,
        messages=messages,
        max_tokens=150,
    )

    return {
        "detail_level": detail,
        "response": response.choices[0].message.content,
        "model_used": response.model,
        "finish_reason": response.choices[0].finish_reason,
        "usage": usage,
    }


def main():
    print("=" * 60)
    print("DETAILED VISION TEST")
    print("=" * 60)

    endpoint_info = config.get_endpoint_info()
    print(f"\nEndpoint Configuration:")
    print(f"  Mode:     {endpoint_info['mode']}")
    print(f"  Base URL: {endpoint_info['base_url']}")
    print(f"  Model:    {endpoint_info['model']}")

    if not TEST_IMAGE_PATH.exists():
        print(f"\nERROR: Test image not found at {TEST_IMAGE_PATH}")
        return 1

    print(f"\nTest image: {TEST_IMAGE_PATH}")
    print(f"Image size: {TEST_IMAGE_PATH.stat().st_size} bytes")

    print("\n1. Configuring RBC security...")
    cert_status = configure_rbc_security_certs()
    print(f"   Certificate status: {cert_status or 'Not required'}")

    print("\n2. Fetching authentication token...")
    try:
        token, auth_info = fetch_oauth_token()
        print(f"   Auth method: {auth_info['method']}")
    except Exception as e:
        print(f"   ERROR: {e}")
        return 1

    print("\n3. Encoding image...")
    base64_image = encode_image_base64(TEST_IMAGE_PATH)
    print(f"   Encoded length: {len(base64_image)} characters")

    detail_levels = ["low", "high", "auto"]
    results = []

    print("\n4. Testing different detail levels...")
    print("-" * 60)

    for detail in detail_levels:
        print(f"\n   Testing detail='{detail}'...")
        try:
            result = test_vision_with_detail(token, base64_image, detail)
            results.append(result)
            print(f"   SUCCESS")
            print(f"   Model: {result['model_used']}")
            print(f"   Tokens: {result['usage']['total_tokens'] if result['usage'] else 'N/A'}")
            print(f"   Response: {result['response'][:80]}...")
        except Exception as e:
            print(f"   FAILED: {type(e).__name__}: {e}")
            results.append({
                "detail_level": detail,
                "error": str(e),
            })

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    for result in results:
        print(f"\nDetail Level: {result['detail_level']}")
        if "error" in result:
            print(f"  Status: FAILED - {result['error']}")
        else:
            print(f"  Status: SUCCESS")
            print(f"  Model: {result['model_used']}")
            print(f"  Finish Reason: {result['finish_reason']}")
            if result['usage']:
                print(f"  Prompt Tokens: {result['usage']['prompt_tokens']}")
                print(f"  Completion Tokens: {result['usage']['completion_tokens']}")
                print(f"  Response Time: {result['usage']['response_time_ms']}ms")

    print("\n" + "=" * 60)
    print("FULL RESPONSE DATA (JSON)")
    print("=" * 60)
    print(json.dumps(results, indent=2, default=str))

    successful = sum(1 for r in results if "error" not in r)
    print(f"\n{successful}/{len(results)} detail levels tested successfully")

    return 0 if successful > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
