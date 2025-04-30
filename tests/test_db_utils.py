"""
Tests for the database utilities.
"""
import os
import tempfile
import unittest
import sqlite3
from pathlib import Path

from mcp_server.common.db_utils import SQLiteConnection, get_database_connection


class TestSQLiteConnection(unittest.TestCase):
    """Test SQLite database connection."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a temporary database file
        self.db_fd, self.db_path = tempfile.mkstemp()
        
        # Create a test table and data
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)")
        cursor.execute("INSERT INTO test (name) VALUES ('test1')")
        cursor.execute("INSERT INTO test (name) VALUES ('test2')")
        conn.commit()
        conn.close()
        
        # Create the SQLiteConnection instance
        self.db_connection = SQLiteConnection(self.db_path)
    
    def tearDown(self):
        """Clean up test environment."""
        self.db_connection.close()
        os.close(self.db_fd)
        os.unlink(self.db_path)
    
    def test_connect(self):
        """Test connection to SQLite database."""
        conn = self.db_connection.connect()
        self.assertIsNotNone(conn)
        self.assertIsInstance(conn, sqlite3.Connection)
    
    def test_execute(self):
        """Test query execution."""
        result = self.db_connection.execute("SELECT * FROM test")
        self.assertIsNotNone(result)
    
    def test_fetch_all(self):
        """Test fetching all results."""
        results = self.db_connection.fetch_all("SELECT * FROM test")
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["name"], "test1")
        self.assertEqual(results[1]["name"], "test2")
    
    def test_fetch_dataframe(self):
        """Test fetching results as DataFrame."""
        df = self.db_connection.fetch_dataframe("SELECT * FROM test")
        self.assertEqual(len(df), 2)
        self.assertEqual(df["name"][0], "test1")
        self.assertEqual(df["name"][1], "test2")
    
    def test_get_usable_table_names(self):
        """Test getting table names."""
        tables = self.db_connection.get_usable_table_names()
        self.assertIn("test", tables)
    
    def test_get_table_info(self):
        """Test getting table schema."""
        info = self.db_connection.get_table_info("test")
        self.assertIn("CREATE TABLE", info)
        self.assertIn("id", info)
        self.assertIn("name", info)


class TestGetDatabaseConnection(unittest.TestCase):
    """Test the database connection factory function."""
    
    def test_get_sqlite_connection(self):
        """Test getting a SQLite connection."""
        db_connection = get_database_connection("sqlite", uri="test.db")
        self.assertIsInstance(db_connection, SQLiteConnection)
        self.assertEqual(db_connection.db_path, "test.db")
    
    def test_invalid_db_type(self):
        """Test with an invalid database type."""
        with self.assertRaises(ValueError):
            get_database_connection("invalid_db_type")


if __name__ == "__main__":
    unittest.main()