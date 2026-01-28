#!/usr/bin/env python3
"""
Basic Vision Test - Test with sample image and endpoint investigation.

Tests the vision capability by encoding a test image and asking the model
to describe it. Also investigates endpoint parameters and response structure
to understand how the API behaves.
"""

import argparse
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
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

TEST_IMAGE_PATH = Path(__file__).parent.parent / "tests" / "sample_image.png"


def encode_image_base64(image_path: Path) -> str:
    """Read and base64 encode an image file."""
    with open(image_path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode("utf-8")


def print_section(title: str, char: str = "="):
    """Print a formatted section header."""
    print(f"\n{char * 60}")
    print(title)
    print(char * 60)


def investigate_endpoint(token: str, base64_image: str, verbose: bool = False) -> dict:
    """Investigate endpoint capabilities and parameter handling.

    Returns dict with investigation results including what parameters work,
    response structure details, and any differences from expected behavior.
    """
    from openai import OpenAI

    results = {
        "endpoint": config.BASE_URL,
        "model_requested": config.VISION_MODEL,
        "tests": [],
        "differences": [],
        "warnings": [],
    }

    client = OpenAI(api_key=token, base_url=config.BASE_URL)

    test_cases = [
        {
            "name": "basic_vision",
            "description": "Standard vision request with detail=auto",
            "params": {
                "model": config.VISION_MODEL,
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "List the shapes and colors you see. Be concise."},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}",
                                "detail": "auto"
                            }
                        }
                    ]
                }],
                "max_tokens": 150,
            }
        },
        {
            "name": "detail_low",
            "description": "Vision with detail=low (should use fewer tokens)",
            "params": {
                "model": config.VISION_MODEL,
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "What colors do you see?"},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}",
                                "detail": "low"
                            }
                        }
                    ]
                }],
                "max_tokens": 100,
            }
        },
        {
            "name": "detail_high",
            "description": "Vision with detail=high (should use more tokens)",
            "params": {
                "model": config.VISION_MODEL,
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "What colors do you see?"},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}",
                                "detail": "high"
                            }
                        }
                    ]
                }],
                "max_tokens": 100,
            }
        },
    ]

    for test in test_cases:
        print(f"\n  Testing: {test['name']} - {test['description']}")
        test_result = {
            "name": test["name"],
            "description": test["description"],
            "status": None,
            "model_returned": None,
            "prompt_tokens": None,
            "completion_tokens": None,
            "finish_reason": None,
            "response_preview": None,
            "error": None,
        }

        try:
            response = client.chat.completions.create(**test["params"])

            test_result["status"] = "success"
            test_result["model_returned"] = response.model
            test_result["finish_reason"] = response.choices[0].finish_reason
            test_result["response_preview"] = response.choices[0].message.content[:100]

            if response.usage:
                test_result["prompt_tokens"] = response.usage.prompt_tokens
                test_result["completion_tokens"] = response.usage.completion_tokens

            if response.model != config.VISION_MODEL:
                results["differences"].append(
                    f"Model mismatch: requested '{config.VISION_MODEL}', got '{response.model}'"
                )

            print(f"    Status: SUCCESS")
            print(f"    Model returned: {response.model}")
            print(f"    Tokens: {test_result['prompt_tokens']} prompt, {test_result['completion_tokens']} completion")

            if verbose:
                print(f"    Response: {test_result['response_preview']}...")

        except Exception as e:
            test_result["status"] = "failed"
            test_result["error"] = f"{type(e).__name__}: {str(e)}"
            print(f"    Status: FAILED - {test_result['error']}")

            if hasattr(e, "body"):
                print(f"    Error body: {e.body}")

        results["tests"].append(test_result)

    low_test = next((t for t in results["tests"] if t["name"] == "detail_low"), None)
    high_test = next((t for t in results["tests"] if t["name"] == "detail_high"), None)

    if low_test and high_test and low_test["status"] == "success" and high_test["status"] == "success":
        if low_test["prompt_tokens"] and high_test["prompt_tokens"]:
            if low_test["prompt_tokens"] >= high_test["prompt_tokens"]:
                results["warnings"].append(
                    f"Detail level may not affect token usage: low={low_test['prompt_tokens']}, high={high_test['prompt_tokens']}"
                )
            else:
                results["differences"].append(
                    f"Detail affects tokens as expected: low={low_test['prompt_tokens']}, high={high_test['prompt_tokens']}"
                )

    return results


def run_main_test(token: str, base64_image: str) -> tuple:
    """Run the main vision test and return (success, response, usage)."""
    from src.llm import execute_llm_call

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "What's in this image? Please describe it briefly."},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{base64_image}",
                        "detail": "auto"
                    }
                }
            ]
        }
    ]

    response, usage = execute_llm_call(
        oauth_token=token,
        messages=messages,
        max_tokens=300,
    )

    return True, response, usage


def main():
    parser = argparse.ArgumentParser(description="Test vision capabilities with endpoint investigation")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show detailed output")
    parser.add_argument("-i", "--investigate", action="store_true", help="Run endpoint investigation tests")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    print_section("RBC VISION TEST")

    endpoint_info = config.get_endpoint_info()
    print(f"\nEndpoint Configuration:")
    print(f"  Mode:     {endpoint_info['mode']}")
    print(f"  Base URL: {endpoint_info['base_url']}")
    print(f"  Model:    {endpoint_info['model']}")

    if args.verbose:
        print(f"\nEnvironment Check:")
        print(f"  OPENAI_API_KEY: {'set' if os.getenv('OPENAI_API_KEY') else 'not set'}")
        print(f"  AZURE_BASE_URL: {os.getenv('AZURE_BASE_URL', 'not set')}")
        print(f"  OAUTH_URL:      {os.getenv('OAUTH_URL', 'not set')}")
        print(f"  VISION_MODEL:   {os.getenv('VISION_MODEL', 'not set (using default)')}")

    if not TEST_IMAGE_PATH.exists():
        print(f"\nERROR: Test image not found at {TEST_IMAGE_PATH}")
        print("Please ensure tests/sample_image.png exists.")
        return 1

    print(f"\nTest image: {TEST_IMAGE_PATH}")
    print(f"Image size: {TEST_IMAGE_PATH.stat().st_size} bytes")

    print_section("SETUP", "-")

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

    print("\n3. Encoding image as base64...")
    try:
        base64_image = encode_image_base64(TEST_IMAGE_PATH)
        print(f"   Encoded length: {len(base64_image)} characters")
    except Exception as e:
        print(f"   ERROR: Failed to encode image: {e}")
        return 1

    if args.investigate:
        print_section("ENDPOINT INVESTIGATION", "-")
        print("\nRunning parameter investigation tests...")

        investigation = investigate_endpoint(token, base64_image, verbose=args.verbose)

        print_section("INVESTIGATION RESULTS", "-")

        successful = sum(1 for t in investigation["tests"] if t["status"] == "success")
        print(f"\nTest Results: {successful}/{len(investigation['tests'])} passed")

        if investigation["differences"]:
            print("\nObserved Differences from Expected Behavior:")
            for diff in investigation["differences"]:
                print(f"  - {diff}")

        if investigation["warnings"]:
            print("\nWarnings:")
            for warn in investigation["warnings"]:
                print(f"  - {warn}")

        if args.verbose:
            print("\nFull Investigation Data:")
            print(json.dumps(investigation, indent=2, default=str))

    print_section("MAIN VISION TEST", "-")

    print("\n4. Sending vision request...")
    try:
        success, response, usage = run_main_test(token, base64_image)

        print_section("VISION RESPONSE")
        print(response.choices[0].message.content)

        if usage:
            print("\n" + "-" * 40)
            print("Token Usage:")
            print(f"  Prompt tokens:     {usage['prompt_tokens']}")
            print(f"  Completion tokens: {usage['completion_tokens']}")
            print(f"  Total tokens:      {usage['total_tokens']}")
            print(f"  Response time:     {usage['response_time_ms']}ms")

        if args.verbose:
            print("\nResponse Metadata:")
            print(f"  Model used:     {response.model}")
            print(f"  Finish reason:  {response.choices[0].finish_reason}")
            print(f"  Response ID:    {response.id}")

        print_section("SUCCESS - Vision capability working!")
        return 0

    except Exception as e:
        print(f"\nERROR: {type(e).__name__}: {e}")

        if hasattr(e, "body"):
            print(f"\nError Details:")
            print(f"  Body: {e.body}")

        if hasattr(e, "response"):
            print(f"  Status: {e.response.status_code}")

        import traceback
        if args.debug:
            print("\nFull Traceback:")
            traceback.print_exc()

        return 1


if __name__ == "__main__":
    sys.exit(main())
