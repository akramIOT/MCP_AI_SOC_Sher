"""
Local MCP Server implementation with STDIO and SSE support.
"""
import os
import sys
import json
import time
import logging
import threading
import argparse
from typing import Dict, List, Optional, Any, Callable, Iterator, Union
import asyncio
from concurrent.futures import ThreadPoolExecutor
import signal
from pydantic import BaseModel, Field

from fastapi import FastAPI, Depends, HTTPException, Request, Response, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from sse_starlette.sse import EventSourceResponse

from ..common.config import load_config, MCPConfig
from ..common.db_utils import get_database_connection, DatabaseConnection
from ..common.agent import Text2SQLAgent, QueryRequest, QueryResponse
from ..security.threat_analyzer import SQLThreatAnalyzer, RemoteThreatAnalyzer, ThreatAnalysisResult


logger = logging.getLogger(__name__)


class SQLRequest(BaseModel):
    """Request model for SQL query generation."""
    query: str = Field(..., description="Natural language query")
    optimize: bool = Field(False, description="Whether to optimize the generated SQL")
    execute: bool = Field(False, description="Whether to execute the generated SQL")
    explain: bool = Field(False, description="Whether to explain the generated SQL")
    stream: bool = Field(False, description="Whether to stream the response")
    security_check: bool = Field(True, description="Whether to perform security checks")
    dialect: str = Field("SQLite", description="SQL dialect to use")
    top_k: int = Field(10, description="Maximum number of results to return")


class SQLResponse(BaseModel):
    """Response model for SQL query generation."""
    sql: str = Field(..., description="Generated SQL query")
    optimized_sql: Optional[str] = Field(None, description="Optimized SQL query")
    results: Optional[List[Dict[str, Any]]] = Field(None, description="Query results")
    explanation: Optional[str] = Field(None, description="Explanation of the SQL query")
    security: Optional[ThreatAnalysisResult] = Field(None, description="Security analysis result")
    error: Optional[str] = Field(None, description="Error message if query generation failed")


class LocalMCPServer:
    """Local MCP Server implementation."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the local MCP server."""
        # Load configuration
        self.config = load_config(config_path)
        
        # Set up logging
        logging.basicConfig(
            level=logging.DEBUG if self.config.server.debug else logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Set up OpenAI API key
        if self.config.openai_api_key:
            os.environ["OPENAI_API_KEY"] = self.config.openai_api_key
        
        # Initialize database connection
        self.db_connection = get_database_connection(
            self.config.database.type,
            **self.config.database.dict()
        )
        
        # Initialize agent
        self.agent = Text2SQLAgent(
            db_connection=self.db_connection,
            model=self.config.agent.model,
            temperature=self.config.agent.temperature,
            use_examples=self.config.agent.use_examples,
            examples_count=self.config.agent.examples_count
        )
        
        # Initialize security threat analyzer
        if self.config.security.enable_threat_analysis:
            if self.config.security.remote_security_endpoint:
                self.threat_analyzer = RemoteThreatAnalyzer(
                    endpoint_url=self.config.security.remote_security_endpoint
                )
            else:
                self.threat_analyzer = SQLThreatAnalyzer(
                    model=self.config.security.threat_analysis_model,
                    sensitive_tables=self.config.security.sensitive_tables,
                    suspicious_patterns=self.config.security.suspicious_patterns
                )
        else:
            self.threat_analyzer = None
        
        # Initialize FastAPI app if using SSE
        self.app = None
        if self.config.server.use_sse:
            self.app = self._create_fastapi_app()
        
        # Thread pool for background tasks
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Keep track of the server state
        self.is_running = False
        self.stdio_thread = None
    
    def _create_fastapi_app(self) -> FastAPI:
        """Create a FastAPI app for the server."""
        app = FastAPI(title="Text2SQL MCP Server")
        
        # Add CORS middleware if enabled
        if self.config.server.allow_cors:
            app.add_middleware(
                CORSMiddleware,
                allow_origins=self.config.server.cors_origins,
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )
        
        # Add routes
        app.post("/api/sql", response_model=SQLResponse)(self.handle_sql_request)
        app.post("/api/sql/stream")(self.stream_sql_response)
        app.get("/api/health")(self.health_check)
        
        return app
    
    async def health_check(self):
        """Health check endpoint."""
        try:
            # Test database connection
            self.db_connection.execute("SELECT 1;")
            
            return {"status": "healthy", "database": "connected"}
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}
    
    async def handle_sql_request(self, request: SQLRequest) -> SQLResponse:
        """Handle a SQL request."""
        try:
            # Check security if enabled
            if request.security_check and self.threat_analyzer:
                # Generate SQL first
                query_request = QueryRequest(
                    query=request.query,
                    optimize=False,
                    execute=False,
                    explain=False,
                    dialect=request.dialect,
                    top_k=request.top_k
                )
                query_response = self.agent.generate_sql(query_request)
                
                # Analyze security
                security_result = self.threat_analyzer.analyze_query(query_response.sql)
                
                # If it's a high threat, block the request
                if security_result.is_threat and security_result.recommended_action == "block":
                    return SQLResponse(
                        sql=query_response.sql,
                        security=security_result,
                        error="Query blocked due to security concerns"
                    )
            else:
                security_result = None
            
            # Process the request
            query_request = QueryRequest(
                query=request.query,
                optimize=request.optimize,
                execute=request.execute,
                explain=request.explain,
                dialect=request.dialect,
                top_k=request.top_k
            )
            query_response = self.agent.generate_sql(query_request)
            
            # Create response
            return SQLResponse(
                sql=query_response.sql,
                optimized_sql=query_response.optimized_sql,
                results=query_response.results,
                explanation=query_response.explanation,
                security=security_result,
                error=query_response.error
            )
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            return SQLResponse(
                sql="",
                error=str(e)
            )
    
    async def stream_sql_response(self, request: SQLRequest) -> EventSourceResponse:
        """Stream a SQL response."""
        async def event_generator():
            try:
                # Generate SQL
                query_request = QueryRequest(
                    query=request.query,
                    optimize=request.optimize,
                    execute=request.execute,
                    explain=request.explain,
                    dialect=request.dialect,
                    top_k=request.top_k
                )
                
                # Stream SQL generation
                yield {
                    "event": "start",
                    "data": json.dumps({"message": "Starting SQL generation"})
                }
                
                # Check security if enabled
                if request.security_check and self.threat_analyzer:
                    # Generate SQL first (non-streaming)
                    query_response = self.agent.generate_sql(QueryRequest(
                        query=request.query,
                        optimize=False,
                        execute=False,
                        explain=False,
                        dialect=request.dialect,
                        top_k=request.top_k
                    ))
                    
                    # Stream the generated SQL
                    yield {
                        "event": "sql",
                        "data": json.dumps({"sql": query_response.sql})
                    }
                    
                    # Analyze security
                    security_result = self.threat_analyzer.analyze_query(query_response.sql)
                    
                    # Stream security analysis
                    yield {
                        "event": "security",
                        "data": json.dumps(security_result.dict())
                    }
                    
                    # If it's a high threat, stop processing
                    if security_result.is_threat and security_result.recommended_action == "block":
                        yield {
                            "event": "error",
                            "data": json.dumps({"message": "Query blocked due to security concerns"})
                        }
                        return
                
                # Normal processing
                query_response = self.agent.generate_sql(query_request)
                
                # Stream results
                if not request.security_check:
                    yield {
                        "event": "sql",
                        "data": json.dumps({"sql": query_response.sql})
                    }
                
                if query_response.optimized_sql:
                    yield {
                        "event": "optimized_sql",
                        "data": json.dumps({"optimized_sql": query_response.optimized_sql})
                    }
                
                if query_response.explanation:
                    yield {
                        "event": "explanation",
                        "data": json.dumps({"explanation": query_response.explanation})
                    }
                
                if query_response.results:
                    # Stream results in chunks if large
                    if len(query_response.results) > 100:
                        for i in range(0, len(query_response.results), 100):
                            chunk = query_response.results[i:i+100]
                            yield {
                                "event": "results_chunk",
                                "data": json.dumps({"results": chunk, "chunk": i // 100})
                            }
                    else:
                        yield {
                            "event": "results",
                            "data": json.dumps({"results": query_response.results})
                        }
                
                if query_response.error:
                    yield {
                        "event": "error",
                        "data": json.dumps({"message": query_response.error})
                    }
                
                # Completion event
                yield {
                    "event": "complete",
                    "data": json.dumps({"message": "Processing complete"})
                }
            except Exception as e:
                logger.error(f"Error in event generator: {e}")
                yield {
                    "event": "error",
                    "data": json.dumps({"message": str(e)})
                }
        
        return EventSourceResponse(event_generator())
    
    def _process_stdio_request(self, request_str: str) -> str:
        """Process a request from STDIO."""
        try:
            # Parse the request
            request_dict = json.loads(request_str)
            request = SQLRequest(**request_dict)
            
            # Handle the request
            response = asyncio.run(self.handle_sql_request(request))
            
            # Return the response
            return json.dumps(response.dict())
        except json.JSONDecodeError:
            error_response = SQLResponse(
                sql="",
                error="Invalid JSON in request"
            )
            return json.dumps(error_response.dict())
        except Exception as e:
            logger.error(f"Error processing STDIO request: {e}")
            error_response = SQLResponse(
                sql="",
                error=str(e)
            )
            return json.dumps(error_response.dict())
    
    def _stdio_worker(self):
        """Worker thread for STDIO interface."""
        while self.is_running:
            try:
                # Read input from STDIN
                request_str = sys.stdin.readline().strip()
                
                if not request_str:
                    # Empty input, wait and continue
                    time.sleep(0.1)
                    continue
                
                # Process the request
                response_str = self._process_stdio_request(request_str)
                
                # Write response to STDOUT
                sys.stdout.write(response_str + "\n")
                sys.stdout.flush()
            except Exception as e:
                logger.error(f"Error in STDIO worker: {e}")
                # Wait a bit before trying again
                time.sleep(0.1)
    
    def start(self):
        """Start the server."""
        self.is_running = True
        
        # Start STDIO interface if enabled
        if self.config.server.use_stdio:
            self.stdio_thread = threading.Thread(target=self._stdio_worker)
            self.stdio_thread.daemon = True
            self.stdio_thread.start()
            logger.info("STDIO interface started")
        
        # Start SSE server if enabled
        if self.config.server.use_sse and self.app:
            import uvicorn
            logger.info(f"Starting SSE server on {self.config.server.host}:{self.config.server.port}")
            uvicorn.run(
                self.app,
                host=self.config.server.host,
                port=self.config.server.port,
                log_level="debug" if self.config.server.debug else "info"
            )
    
    def stop(self):
        """Stop the server."""
        self.is_running = False
        
        # Wait for STDIO thread to finish
        if self.stdio_thread and self.stdio_thread.is_alive():
            self.stdio_thread.join(timeout=5.0)
        
        # Close database connection
        if self.db_connection:
            self.db_connection.close()
        
        # Shutdown executor
        self.executor.shutdown(wait=False)
        
        logger.info("Server stopped")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Text2SQL MCP Server")
    parser.add_argument("--config", type=str, help="Path to configuration file")
    parser.add_argument("--host", type=str, help="Server host address")
    parser.add_argument("--port", type=int, help="Server port")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--stdio", action="store_true", help="Enable STDIO interface")
    parser.add_argument("--sse", action="store_true", help="Enable SSE interface")
    parser.add_argument("--db-uri", type=str, help="Database URI")
    parser.add_argument("--db-type", type=str, help="Database type")
    parser.add_argument("--openai-api-key", type=str, help="OpenAI API key")
    parser.add_argument("--security", action="store_true", help="Enable security threat analysis")
    return parser.parse_args()


def main():
    """Main entry point for the server."""
    args = parse_args()
    
    # Set environment variables from args
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
    if args.db_uri:
        os.environ["MCP_DB_URI"] = args.db_uri
    if args.db_type:
        os.environ["MCP_DB_TYPE"] = args.db_type
    if args.openai_api_key:
        os.environ["OPENAI_API_KEY"] = args.openai_api_key
    if args.security:
        os.environ["MCP_SECURITY_ENABLE_THREAT_ANALYSIS"] = "true"
    
    # Create and start the server
    server = LocalMCPServer(config_path=args.config)
    
    # Handle termination signals
    def signal_handler(sig, frame):
        print("Shutting down server...")
        server.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start the server
    try:
        server.start()
    except KeyboardInterrupt:
        print("Interrupted by user, shutting down...")
    finally:
        server.stop()


if __name__ == "__main__":
    main()