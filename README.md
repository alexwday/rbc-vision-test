# RBC Vision Test

Minimal project to test vision/image capabilities against RBC's internal endpoint. Supports dual-environment operation (local OpenAI and RBC production).

## Quick Start

### Local Development (OpenAI API)

1. Create a `.env` file:
   ```bash
   cp .env.example .env
   # Edit .env and set OPENAI_API_KEY
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run tests:
   ```bash
   # Test basic connectivity
   python scripts/test_text_completion.py

   # Test vision capability
   python scripts/test_vision_basic.py
   ```

### RBC Production

1. Set environment variables (do not use `.env` file in production):
   ```bash
   export AZURE_BASE_URL=https://your-endpoint.openai.azure.com/
   export OAUTH_URL=https://your-oauth-endpoint/token
   export CLIENT_ID=your-client-id
   export CLIENT_SECRET=your-client-secret
   export VISION_MODEL=your-vision-model-name
   ```

2. Run tests:
   ```bash
   python scripts/test_text_completion.py
   python scripts/test_vision_basic.py
   ```

3. If issues arise, use the debug script:
   ```bash
   python scripts/debug_endpoint.py
   ```

## Project Structure

```
rbc-vision-test/
├── src/
│   ├── config.py        # Environment configuration
│   ├── oauth.py         # Token provider (API key or OAuth)
│   ├── rbc_security.py  # RBC SSL certificate setup
│   └── llm.py           # LLM connector with vision support
├── tests/
│   └── sample_image.png # Test image for vision tests
├── scripts/
│   ├── test_text_completion.py  # Basic connectivity test
│   ├── test_vision_basic.py     # Simple vision test
│   ├── test_vision_detailed.py  # Detailed vision exploration
│   └── debug_endpoint.py        # Endpoint debugging tool
├── .env.example         # Environment variable template
├── requirements.txt     # Python dependencies
└── README.md            # This file
```

## Test Scripts

| Script | Purpose |
|--------|---------|
| `test_text_completion.py` | Sanity check - verifies basic LLM connectivity |
| `test_vision_basic.py` | Tests vision with investigation capabilities |
| `test_vision_detailed.py` | Tests different detail levels (low/high/auto) |
| `debug_endpoint.py` | Detailed debugging with raw response inspection |

### test_vision_basic.py Options

The main test script supports several modes:

```bash
# Basic test - just verify vision works
python scripts/test_vision_basic.py

# Verbose mode - show more details about responses
python scripts/test_vision_basic.py -v

# Investigation mode - test different parameters and compare behavior
python scripts/test_vision_basic.py -i

# Full investigation with verbose output
python scripts/test_vision_basic.py -iv

# Debug mode - enable debug logging
python scripts/test_vision_basic.py --debug
```

Investigation mode (`-i`) tests:
- Different `detail` levels (low, high, auto)
- Token usage differences between detail levels
- Model name matching (requested vs returned)
- Response structure consistency

## Environment Variables

| Variable | Local Mode | RBC Mode | Description |
|----------|------------|----------|-------------|
| `OPENAI_API_KEY` | Required | Not used | OpenAI API key |
| `AZURE_BASE_URL` | Optional | Required | Azure endpoint URL |
| `OAUTH_URL` | Not used | Required | OAuth token endpoint |
| `CLIENT_ID` | Not used | Required | OAuth client ID |
| `CLIENT_SECRET` | Not used | Required | OAuth client secret |
| `VISION_MODEL` | Optional | Required | Model name (default: `gpt-4o`) |

## Vision Message Format

The project uses the standard OpenAI vision message format:

```python
messages = [
    {
        "role": "user",
        "content": [
            {"type": "text", "text": "What's in this image?"},
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{base64_image}",
                    "detail": "auto"  # or "low" or "high"
                }
            }
        ]
    }
]
```

## Troubleshooting

1. **Connection errors**: Run `debug_endpoint.py` to see full error details
2. **Authentication failures**: Verify OAuth credentials or API key
3. **Vision not working**: Check if the model supports vision capabilities
4. **SSL errors in RBC**: Ensure `rbc_security` package is installed
