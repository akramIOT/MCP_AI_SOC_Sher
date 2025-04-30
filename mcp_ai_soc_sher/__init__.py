"""
MCP AI SOC Sher - An AI-powered SOC Text2SQL framework.

This package provides a comprehensive framework for converting natural language to SQL queries 
with integrated security threat analysis and monitoring capabilities.

Usage:
    from mcp_ai_soc_sher.local import LocalMCPServer
    from mcp_ai_soc_sher.remote import RemoteMCPServer
    
    # Start a local server with STDIO interface
    local_server = LocalMCPServer()
    local_server.start()
    
    # Start a remote server with REST API
    remote_server = RemoteMCPServer()
    remote_server.start()
"""

__version__ = "0.1.0"
__author__ = "Akram Sheriff"