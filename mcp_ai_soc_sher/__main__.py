"""
Main entry point for the MCP AI SOC Sher package.
"""
import argparse
import sys
import os
from pathlib import Path

# Add the parent directory to sys.path
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)


def main():
    """Main entry point for the MCP AI SOC Sher package."""
    parser = argparse.ArgumentParser(description="MCP AI SOC Sher - Text2SQL with Security Analysis")
    
    # Server type
    parser.add_argument("--type", type=str, choices=["local", "remote"], default="local",
                        help="Server type (local or remote)")
    
    # Common arguments
    parser.add_argument("--config", type=str, help="Path to configuration file")
    parser.add_argument("--host", type=str, help="Server host address")
    parser.add_argument("--port", type=int, help="Server port")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--db-uri", type=str, help="Database URI")
    parser.add_argument("--db-type", type=str, help="Database type")
    parser.add_argument("--openai-api-key", type=str, help="OpenAI API key")
    parser.add_argument("--security", action="store_true", help="Enable security threat analysis")
    
    # Local server specific arguments
    parser.add_argument("--stdio", action="store_true", help="Enable STDIO interface")
    parser.add_argument("--sse", action="store_true", help="Enable SSE interface")
    
    # Remote server specific arguments
    parser.add_argument("--api-key", type=str, help="API key for authentication")
    
    args = parser.parse_args()
    
    # Set environment variables from args
    if args.host:
        os.environ["MCP_SERVER_HOST"] = args.host
    if args.port:
        os.environ["MCP_SERVER_PORT"] = str(args.port)
    if args.debug:
        os.environ["MCP_SERVER_DEBUG"] = "true"
    if args.db_uri:
        os.environ["MCP_DB_URI"] = args.db_uri
    if args.db_type:
        os.environ["MCP_DB_TYPE"] = args.db_type
    if args.openai_api_key:
        os.environ["OPENAI_API_KEY"] = args.openai_api_key
    if args.security:
        os.environ["MCP_SECURITY_ENABLE_THREAT_ANALYSIS"] = "true"
    
    # Local server specific environment variables
    if args.stdio:
        os.environ["MCP_SERVER_USE_STDIO"] = "true"
    if args.sse:
        os.environ["MCP_SERVER_USE_SSE"] = "true"
    
    # Remote server specific environment variables
    if args.api_key:
        os.environ["MCP_SERVER_API_KEY"] = args.api_key
    
    # Start the appropriate server
    if args.type == "local":
        from mcp_ai_soc_sher.local import LocalMCPServer
        server = LocalMCPServer(config_path=args.config)
    else:
        from mcp_ai_soc_sher.remote import RemoteMCPServer
        server = RemoteMCPServer(config_path=args.config)
    
    try:
        server.start()
    except KeyboardInterrupt:
        print("Interrupted by user, shutting down...")
    finally:
        server.stop()


if __name__ == "__main__":
    main()