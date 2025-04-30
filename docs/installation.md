# Installation

This guide covers how to install the Text2SQL MCP Server.

## Prerequisites

- Python 3.8 or later
- pip package manager
- Optional: Virtual environment (recommended)
- Optional: Snowflake account for Snowflake database support

## Installation from PyPI

The simplest way to install the Text2SQL MCP Server is from PyPI:

```bash
pip install text2sql-mcp-server
```

## Installation from Source

To install from source:

1. Clone the repository:
   ```bash
   git clone https://github.com/username/text2sql-mcp-server.git
   cd text2sql-mcp-server
   ```

2. Install the package:
   ```bash
   pip install -e .
   ```

## Using a Virtual Environment (recommended)

We recommend using a virtual environment to avoid conflicts with other packages:

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate

# Install the package
pip install text2sql-mcp-server
```

## Configuration

After installation, you need to create a configuration file. The simplest way is to copy the example:

```bash
cp .env.example .env
```

Then edit the `.env` file to add your API keys and configuration settings:

```bash
# Edit the .env file
nano .env
```

See the [Configuration](configuration.md) guide for more details.

## Dependencies

The Text2SQL MCP Server requires the following dependencies, which will be installed automatically:

- langchain
- langchain-openai
- langchain-community
- fastapi
- uvicorn
- sse-starlette
- openai
- faiss-cpu
- python-dotenv
- pydantic
- pandas
- sqlalchemy

For Snowflake support, you also need to install:

```bash
pip install snowflake-connector-python
```

## Verifying Installation

To verify that the installation was successful, run:

```bash
python -m mcp_server --help
```

You should see the help message with available command-line options.