"""
Example of using the local MCP server with STDIO interface.
"""
import os
import json
import sys
import subprocess
from pathlib import Path

# Set up the environment variables
os.environ["OPENAI_API_KEY"] = "your_openai_api_key_here"  # Replace with your actual API key
os.environ["MCP_DB_URI"] = "sqlite:///example.db"
os.environ["MCP_SERVER_USE_STDIO"] = "true"

# Create a sample SQLite database for the example
import sqlite3
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

# Start the local server in a subprocess
process = subprocess.Popen(
    ["python", "-m", "mcp_server", "--type", "local", "--stdio"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=1
)

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
for query in example_queries:
    print(f"\nSending query: {query['query']}")
    
    # Encode the query as JSON and send it to the server
    query_json = json.dumps(query)
    process.stdin.write(query_json + "\n")
    process.stdin.flush()
    
    # Read the response from the server
    response = process.stdout.readline()
    
    # Parse and print the response
    try:
        result = json.loads(response)
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
    except json.JSONDecodeError:
        print("Error parsing response:", response)

# Terminate the server process
process.terminate()
process.wait()

# Clean up the example database
try:
    os.remove("example.db")
    print("\nExample database removed")
except:
    pass