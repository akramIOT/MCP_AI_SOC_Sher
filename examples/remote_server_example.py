"""
Example of using the remote MCP server with REST API.
"""
import os
import sys
import time
import json
import requests
import subprocess
from pathlib import Path
import sqlite3

# Set up the environment variables
api_key = "test_api_key_123"  # This would be your actual API key in production

# Create a sample SQLite database for the example
conn = sqlite3.connect("example.db")
conn.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL,
    email TEXT NOT NULL,
    registration_date TEXT NOT NULL
)
""")
conn.execute("""
INSERT INTO users (username, email, registration_date) 
VALUES 
('user1', 'user1@example.com', '2025-03-01'),
('user2', 'user2@example.com', '2025-04-01'),
('user3', 'user3@example.com', '2025-04-15')
""")
conn.commit()
conn.close()
print("Example database created")

# Start the remote server in a subprocess
process = subprocess.Popen(
    [
        "python", "-m", "mcp_server", 
        "--type", "remote", 
        "--port", "8000", 
        "--db-uri", "sqlite:///example.db",
        "--api-key", api_key
    ],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

# Give the server time to start
print("Starting server...")
time.sleep(5)

# Base URL for the API
base_url = "http://localhost:8000"

# Example queries to test
example_queries = [
    {
        "query": "Find all users",
        "optimize": True,
        "execute": True
    },
    {
        "query": "Count users who registered in April 2025",
        "optimize": True,
        "execute": True,
        "explain": True
    }
]

# Send queries to the server
headers = {
    "Content-Type": "application/json",
    "X-API-Key": api_key
}

try:
    # Test server health
    health_response = requests.get(f"{base_url}/api/health")
    print(f"Server health check: {health_response.json()}")
    
    # Get available tables
    tables_response = requests.get(
        f"{base_url}/api/database/tables",
        headers=headers
    )
    print(f"Available tables: {tables_response.json()}")
    
    # Send SQL generation requests
    for query in example_queries:
        print(f"\nSending query: {query['query']}")
        
        response = requests.post(
            f"{base_url}/api/sql",
            headers=headers,
            json=query
        )
        
        if response.status_code == 200:
            result = response.json()
            print("\nSQL Query:")
            print(result.get("sql", "No SQL generated"))
            
            if result.get("optimized_sql"):
                print("\nOptimized SQL:")
                print(result.get("optimized_sql"))
            
            if result.get("explanation"):
                print("\nExplanation:")
                print(result.get("explanation"))
            
            if result.get("results"):
                print("\nResults:")
                for row in result.get("results"):
                    print(row)
            
            if result.get("error"):
                print("\nError:")
                print(result.get("error"))
        else:
            print(f"Error: {response.status_code} - {response.text}")
    
    # Example of security analysis
    print("\nTesting security analysis:")
    security_query = {
        "query": "SELECT * FROM users; DROP TABLE users;"
    }
    
    response = requests.post(
        f"{base_url}/api/security",
        headers=headers,
        json=security_query
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"Security analysis result: {json.dumps(result, indent=2)}")
    else:
        print(f"Error: {response.status_code} - {response.text}")

except Exception as e:
    print(f"Error during test: {e}")

finally:
    # Terminate the server process
    print("\nShutting down server...")
    process.terminate()
    process.wait()
    
    # Clean up the example database
    try:
        os.remove("example.db")
        print("Example database removed")
    except:
        pass