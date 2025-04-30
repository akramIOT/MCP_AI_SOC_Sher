#!/bin/bash
# Build and install the MCP AI SOC Sher package

# Ensure we're in the project root directory
cd "$(dirname "$0")" || exit 1

echo "=== Building MCP AI SOC Sher package ==="

# Clean up any previous builds
rm -rf dist/ build/ *.egg-info/

# Install dependencies
pip install --upgrade pip setuptools wheel build

# Create the distributable packages
python -m build

echo -e "\n=== Installing MCP AI SOC Sher package ==="
pip install -e .

echo -e "\n=== Installation complete! ==="
echo "You can now run MCP AI SOC Sher with:"
echo "  mcp-ai-soc --type local --stdio --sse"
echo "  or"
echo "  python -m mcp_ai_soc_sher --type local --stdio --sse"
echo "  or"
echo "  ./run_mcp_ai_soc.py --type local --stdio --sse"
echo ""
echo "Don't forget to set your OPENAI_API_KEY in .env file or as an environment variable!"