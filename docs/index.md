# Text2SQL MCP Server Documentation

Welcome to the Text2SQL MCP Server documentation!

## Overview

The Text2SQL MCP Server is a framework for converting natural language to SQL queries using large language models, with support for:
- Multiple database backends (SQLite, Snowflake)
- Security threat analysis
- Both local and remote server modes
- STDIO and SSE-based interface options

## Table of Contents

- [Installation](installation.md)
- [Configuration](configuration.md)
- [Usage](usage.md)
  - [Local Server](usage_local.md)
  - [Remote Server](usage_remote.md)
- [Security](security.md)
- [API Reference](api_reference.md)
- [Advanced Topics](advanced_topics.md)
- [Contributing](../CONTRIBUTING.md)
- [License](../LICENSE)

## Quick Start

```bash
# Install the package
pip install text2sql-mcp-server

# Create a .env file with your configuration
cp .env.example .env

# Edit the .env file
nano .env

# Run the local server
python -m mcp_server --type local --stdio --sse

# Run the remote server
python -m mcp_server --type remote
```

For more detailed instructions, see the [Installation](installation.md) and [Usage](usage.md) guides.