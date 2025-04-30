# Configuration

This guide covers how to configure the Text2SQL MCP Server.

## Environment Variables

The Text2SQL MCP Server uses environment variables for configuration. You can set these variables directly in your environment or use a `.env` file.

### Core Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | Your OpenAI API key (required) | None |
| `MCP_DB_URI` | Database URI | `sqlite:///database.db` |
| `MCP_DB_TYPE` | Database type (sqlite, snowflake) | `sqlite` |
| `MCP_SERVER_HOST` | Server host address | `0.0.0.0` |
| `MCP_SERVER_PORT` | Server port | `8000` |
| `MCP_SERVER_DEBUG` | Enable debug mode | `false` |
| `MCP_SERVER_API_KEY` | API key for authentication | None |

### Agent Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `MCP_AGENT_MODEL` | LLM model to use | `gpt-4` |
| `MCP_AGENT_TEMPERATURE` | Temperature for LLM generation | `0.0` |
| `MCP_AGENT_MAX_TOKENS` | Maximum tokens for LLM response | `1000` |
| `MCP_AGENT_USE_EXAMPLES` | Whether to include examples in the prompt | `true` |
| `MCP_AGENT_EXAMPLES_COUNT` | Number of examples to include | `5` |

### Server Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `MCP_SERVER_ALLOW_CORS` | Allow CORS | `true` |
| `MCP_SERVER_CORS_ORIGINS` | CORS origins | `*` |
| `MCP_SERVER_USE_SSE` | Enable Server-Sent Events | `true` |
| `MCP_SERVER_USE_STDIO` | Enable STDIO interface | `true` |

### Security Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `MCP_SECURITY_ENABLE_THREAT_ANALYSIS` | Enable security threat analysis | `false` |
| `MCP_SECURITY_THREAT_ANALYSIS_MODEL` | LLM model for threat analysis | `gpt-4` |
| `MCP_SECURITY_SENSITIVE_TABLES` | Comma-separated list of sensitive tables | None |
| `MCP_SECURITY_SUSPICIOUS_PATTERNS` | Comma-separated list of suspicious patterns | None |
| `MCP_SECURITY_REMOTE_ENDPOINT` | Remote security server endpoint | None |

### Snowflake Configuration

For Snowflake support, you need to set the following variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `MCP_DB_USERNAME` | Snowflake username | None |
| `MCP_DB_PASSWORD` | Snowflake password | None |
| `MCP_SNOWFLAKE_ACCOUNT` | Snowflake account identifier | None |
| `MCP_SNOWFLAKE_WAREHOUSE` | Snowflake warehouse name | None |
| `MCP_SNOWFLAKE_DATABASE` | Snowflake database name | None |
| `MCP_SNOWFLAKE_SCHEMA` | Snowflake schema name | None |
| `MCP_SNOWFLAKE_ROLE` | Snowflake role name | None |

## Configuration File

You can use a `.env` file to store your configuration. Copy the example file and edit it:

```bash
cp .env.example .env
```

## Command Line Configuration

You can also configure the server using command line arguments, which will override the environment variables:

```bash
python -m mcp_server --type local --host 127.0.0.1 --port 8080 --debug --stdio --sse
```

See the full list of command line options with:

```bash
python -m mcp_server --help
```