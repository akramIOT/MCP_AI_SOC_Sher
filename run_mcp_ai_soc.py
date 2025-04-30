#!/usr/bin/env python
"""
Quick start script for running the MCP AI SOC Sher server.
"""
import os
import sys
import argparse
from pathlib import Path

# Add the parent directory to sys.path
parent_dir = str(Path(__file__).parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from mcp_ai_soc_sher.local import LocalMCPServer
from mcp_ai_soc_sher.remote import RemoteMCPServer


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="MCP AI SOC Sher - Text2SQL with Security Analysis")
    parser.add_argument("--type", choices=["local", "remote"], default="local",
                        help="Server type (local or remote)")
    parser.add_argument("--config", help="Path to configuration file (.env)")
    parser.add_argument("--host", default="0.0.0.0", help="Server host address")
    parser.add_argument("--port", type=int, default=8000, help="Server port")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--stdio", action="store_true", help="Enable STDIO interface (local only)")
    parser.add_argument("--sse", action="store_true", help="Enable SSE interface (local only)")
    parser.add_argument("--db-path", help="Path to SQLite database file")
    parser.add_argument("--openai-key", help="OpenAI API key")
    parser.add_argument("--security", action="store_true", help="Enable security threat analysis")
    return parser.parse_args()


def main():
    """Run the MCP AI SOC Sher server."""
    args = parse_args()
    
    # Set environment variables
    if args.host:
        os.environ["MCP_SERVER_HOST"] = args.host
    if args.port:
        os.environ["MCP_SERVER_PORT"] = str(args.port)
    if args.debug:
        os.environ["MCP_SERVER_DEBUG"] = "true"
    if args.stdio:
        os.environ["MCP_SERVER_USE_STDIO"] = "true"
    if args.sse:
        os.environ["MCP_SERVER_USE_SSE"] = "true"
    if args.db_path:
        os.environ["MCP_DB_URI"] = f"sqlite:///{args.db_path}"
    if args.openai_key:
        os.environ["OPENAI_API_KEY"] = args.openai_key
    if args.security:
        os.environ["MCP_SECURITY_ENABLE_THREAT_ANALYSIS"] = "true"
    
    # Create and start the server
    try:
        if args.type == "local":
            server = LocalMCPServer(config_path=args.config)
            print(f"Starting MCP AI SOC Sher local server...")
            if args.stdio:
                print("STDIO interface enabled")
            if args.sse:
                print(f"SSE interface enabled on http://{args.host}:{args.port}")
        else:
            server = RemoteMCPServer(config_path=args.config)
            print(f"Starting MCP AI SOC Sher remote server on http://{args.host}:{args.port}...")
        
        server.start()
    except KeyboardInterrupt:
        print("\nInterrupted by user, shutting down...")
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()