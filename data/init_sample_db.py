#!/usr/bin/env python
"""
Initialize a sample SQLite database for the Text2SQL MCP Server.
"""
import os
import sqlite3
from pathlib import Path

# Determine the database path
data_dir = Path(__file__).parent
db_path = data_dir / "sample.db"
schema_path = data_dir / "sample_schema.sql"

def init_sample_db():
    """Initialize the sample database."""
    print(f"Initializing sample database at {db_path}...")
    
    # Remove existing database if it exists
    if db_path.exists():
        os.remove(db_path)
    
    # Create a new database and connect to it
    conn = sqlite3.connect(db_path)
    
    # Read and execute the schema SQL
    with open(schema_path, "r") as f:
        schema_sql = f.read()
    
    conn.executescript(schema_sql)
    conn.commit()
    
    # Verify the database was created successfully
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"Created tables: {', '.join(table[0] for table in tables)}")
    
    # Close the connection
    conn.close()
    
    print("Sample database initialized successfully.")
    print(f"To use this database, set MCP_DB_URI=sqlite:///{db_path}")

if __name__ == "__main__":
    init_sample_db()