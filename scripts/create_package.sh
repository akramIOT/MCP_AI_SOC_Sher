#!/bin/bash
# Create a distributable package of the Text2SQL MCP Server

# Ensure we're in the project root directory
cd "$(dirname "$0")/.." || exit 1

# Clean up any previous builds
rm -rf dist/ build/ *.egg-info/

# Install dependencies
pip install --upgrade pip setuptools wheel twine

# Create the distributable packages
python setup.py sdist bdist_wheel

echo ""
echo "Package created successfully!"
echo "To upload to PyPI, run: python -m twine upload dist/*"
echo "To install locally, run: pip install dist/*.whl"
echo ""