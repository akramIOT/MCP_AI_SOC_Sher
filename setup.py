from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.read().splitlines()

setup(
    name="mcp-ai-soc-sher",
    version="0.1.0",
    author="Akram Sheriff",
    author_email="YOUR_EMAIL@example.com",  # Replace with actual contact email
    description="An AI-powered SOC Text2SQL MCP Server for converting natural language to SQL queries",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/akramsheriff/mcp-ai-soc-sher",  # Replace with actual repo URL
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "mcp-ai-soc-local=mcp_ai_soc_sher.local.server:main",
            "mcp-ai-soc-remote=mcp_ai_soc_sher.remote.server:main",
            "mcp-ai-soc=mcp_ai_soc_sher.__main__:main",
        ],
    },
    include_package_data=True,
)