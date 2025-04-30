# MCP AI SOC Sher

A powerful AI-driven Security Operations Center (SOC) Text2SQL framework  based  MCP Server (Local and Remote) for converting natural language Prompts  to SQL queries dynamically, with integrated security threat analysis and monitoring.

## Features

- **Text2SQL Conversion**: Convert natural language queries to optimized SQL
- **Multiple Interfaces**: Support for STDIO, SSE, and REST API
- **Security Threat Analysis**: Built-in SQL query security analysis
- **Multiple Database Support**: Connect to SQLite or Snowflake databases
- **Streaming Responses**: Real-time query processing feedback
- **SOC Monitoring**: Security Operations Center monitoring capabilities

## Installation

```bash
pip install mcp-ai-soc-sher
```

## Quick Start

```python
# Set your OpenAI API key
import os
os.environ["OPENAI_API_KEY"] = "your-api-key-here"

# Use as local server
from mcp_ai_soc_sher.local import LocalMCPServer

server = LocalMCPServer()
server.start()

# Or run from command line
# mcp-ai-soc --type local --stdio --sse
```

## Command Line Usage

```bash
# Run local server with STDIO interface
mcp-ai-soc --type local --stdio

# Run local server with SSE interface
mcp-ai-soc --type local --sse

# Run remote server with REST API
mcp-ai-soc --type remote
```

## Configuration

Create a `.env` file with your configuration:

```
OPENAI_API_KEY=your_openai_api_key_here
MCP_DB_URI=sqlite:///your_database.db
MCP_SECURITY_ENABLE_THREAT_ANALYSIS=true
```

See the [documentation](docs/configuration.md) for all configuration options.

## Example

```python
import json
import requests

# Query the server
response = requests.post(
    "http://localhost:8000/api/sql",
    headers={"Content-Type": "application/json", "X-API-Key": "your-api-key"},
    json={
        "query": "Find all suspicious login attempts in the last 24 hours",
        "optimize": True,
        "execute": True
    }
)

# Process the response
result = response.json()
print(f"SQL Query: {result['sql']}")
if result['results']:
    print("Results:")
    for row in result['results']:
        print(row)
```

## Security Features

- Rule-based and AI-powered SQL query security analysis
- Detection of potential SQL injection attacks
- Sensitive table access monitoring
- Configurable security levels and actions

## License

MIT License with Additional Conditions. Copyright (c) 2025 Akram Sheriff.

See [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.
