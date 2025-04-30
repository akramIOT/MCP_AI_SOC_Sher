"""
Configuration utilities for MCP AI SOC Sher.
"""
import os
from typing import Dict, Optional, Any
from pydantic import BaseModel, Field
import dotenv
from pathlib import Path


class DatabaseConfig(BaseModel):
    """Database configuration for the MCP Server."""
    uri: str = Field(..., description="Database connection URI")
    type: str = Field("sqlite", description="Database type (sqlite, snowflake, etc.)")
    username: Optional[str] = Field(None, description="Database username")
    password: Optional[str] = Field(None, description="Database password")
    account: Optional[str] = Field(None, description="Snowflake account identifier")
    warehouse: Optional[str] = Field(None, description="Snowflake warehouse name")
    database: Optional[str] = Field(None, description="Snowflake database name")
    schema: Optional[str] = Field(None, description="Snowflake schema name")
    role: Optional[str] = Field(None, description="Snowflake role name")


class AgentConfig(BaseModel):
    """Configuration for the Text2SQL agent."""
    model: str = Field("gpt-4", description="LLM model to use for the agent")
    temperature: float = Field(0.0, description="Temperature for LLM generation")
    max_tokens: int = Field(1000, description="Maximum tokens for LLM response")
    top_p: float = Field(1.0, description="Top p for LLM generation")
    use_examples: bool = Field(True, description="Whether to include examples in the prompt")
    examples_count: int = Field(5, description="Number of examples to include in the prompt")


class ServerConfig(BaseModel):
    """Configuration for the MCP Server."""
    host: str = Field("0.0.0.0", description="Server host address")
    port: int = Field(8000, description="Server port")
    debug: bool = Field(False, description="Enable debug mode")
    allow_cors: bool = Field(True, description="Allow CORS")
    cors_origins: list = Field(["*"], description="CORS origins")
    api_key: Optional[str] = Field(None, description="API key for authentication")
    use_sse: bool = Field(True, description="Enable Server-Sent Events")
    use_stdio: bool = Field(True, description="Enable STDIO interface")


class SecurityConfig(BaseModel):
    """Security configuration for the MCP Server."""
    enable_threat_analysis: bool = Field(False, description="Enable security threat analysis")
    threat_analysis_model: str = Field("gpt-4", description="LLM model to use for threat analysis")
    suspicious_patterns: list = Field(default_factory=list, description="List of suspicious patterns to check for")
    sensitive_tables: list = Field(default_factory=list, description="List of sensitive tables to monitor")
    remote_security_endpoint: Optional[str] = Field(None, description="Remote security server endpoint")


class MCPConfig(BaseModel):
    """Main configuration for the MCP Server."""
    database: DatabaseConfig
    agent: AgentConfig
    server: ServerConfig
    security: SecurityConfig
    openai_api_key: str = Field(..., description="OpenAI API key")
    env_file: Optional[str] = Field(".env", description="Environment file path")


class ConfigProvider:
    """Provider for configuration values."""
    
    def __init__(self, env_file: Optional[str] = None):
        """Initialize the config provider."""
        if env_file:
            dotenv.load_dotenv(env_file)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return os.environ.get(key, default)


def load_config(config_path: Optional[str] = None) -> MCPConfig:
    """Load the MCP server configuration."""
    # Try loading from env file first
    env_file = config_path or os.environ.get("MCP_CONFIG_FILE", ".env")
    if os.path.exists(env_file):
        dotenv.load_dotenv(env_file)
    
    # Database configuration
    db_config = DatabaseConfig(
        uri=os.environ.get("MCP_DB_URI", "sqlite:///database.db"),
        type=os.environ.get("MCP_DB_TYPE", "sqlite"),
        username=os.environ.get("MCP_DB_USERNAME"),
        password=os.environ.get("MCP_DB_PASSWORD"),
        account=os.environ.get("MCP_SNOWFLAKE_ACCOUNT"),
        warehouse=os.environ.get("MCP_SNOWFLAKE_WAREHOUSE"),
        database=os.environ.get("MCP_SNOWFLAKE_DATABASE"),
        schema=os.environ.get("MCP_SNOWFLAKE_SCHEMA"),
        role=os.environ.get("MCP_SNOWFLAKE_ROLE")
    )
    
    # Agent configuration
    agent_config = AgentConfig(
        model=os.environ.get("MCP_AGENT_MODEL", "gpt-4"),
        temperature=float(os.environ.get("MCP_AGENT_TEMPERATURE", 0.0)),
        max_tokens=int(os.environ.get("MCP_AGENT_MAX_TOKENS", 1000)),
        top_p=float(os.environ.get("MCP_AGENT_TOP_P", 1.0)),
        use_examples=os.environ.get("MCP_AGENT_USE_EXAMPLES", "true").lower() == "true",
        examples_count=int(os.environ.get("MCP_AGENT_EXAMPLES_COUNT", 5))
    )
    
    # Server configuration
    server_config = ServerConfig(
        host=os.environ.get("MCP_SERVER_HOST", "0.0.0.0"),
        port=int(os.environ.get("MCP_SERVER_PORT", 8000)),
        debug=os.environ.get("MCP_SERVER_DEBUG", "false").lower() == "true",
        allow_cors=os.environ.get("MCP_SERVER_ALLOW_CORS", "true").lower() == "true",
        cors_origins=os.environ.get("MCP_SERVER_CORS_ORIGINS", "*").split(","),
        api_key=os.environ.get("MCP_SERVER_API_KEY"),
        use_sse=os.environ.get("MCP_SERVER_USE_SSE", "true").lower() == "true",
        use_stdio=os.environ.get("MCP_SERVER_USE_STDIO", "true").lower() == "true"
    )
    
    # Security configuration
    security_config = SecurityConfig(
        enable_threat_analysis=os.environ.get("MCP_SECURITY_ENABLE_THREAT_ANALYSIS", "false").lower() == "true",
        threat_analysis_model=os.environ.get("MCP_SECURITY_THREAT_ANALYSIS_MODEL", "gpt-4"),
        suspicious_patterns=os.environ.get("MCP_SECURITY_SUSPICIOUS_PATTERNS", "").split(",") if os.environ.get("MCP_SECURITY_SUSPICIOUS_PATTERNS") else [],
        sensitive_tables=os.environ.get("MCP_SECURITY_SENSITIVE_TABLES", "").split(",") if os.environ.get("MCP_SECURITY_SENSITIVE_TABLES") else [],
        remote_security_endpoint=os.environ.get("MCP_SECURITY_REMOTE_ENDPOINT")
    )
    
    # Create and return the full configuration
    return MCPConfig(
        database=db_config,
        agent=agent_config,
        server=server_config,
        security=security_config,
        openai_api_key=os.environ.get("OPENAI_API_KEY", ""),
        env_file=env_file
    )