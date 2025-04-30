"""
Database utilities for connecting to different database types.
"""
import os
from typing import Optional, List, Dict, Any, Union
import sqlite3
import pandas as pd
from abc import ABC, abstractmethod
import json
import logging

from langchain_community.utilities import SQLDatabase


logger = logging.getLogger(__name__)


class DatabaseConnection(ABC):
    """Abstract base class for database connections."""
    
    @abstractmethod
    def connect(self) -> Any:
        """Connect to the database."""
        pass
    
    @abstractmethod
    def execute(self, query: str) -> Any:
        """Execute a query."""
        pass
    
    @abstractmethod
    def fetch_all(self, query: str) -> List[Dict[str, Any]]:
        """Fetch all results from a query."""
        pass
    
    @abstractmethod
    def fetch_dataframe(self, query: str) -> pd.DataFrame:
        """Fetch results as a pandas DataFrame."""
        pass
    
    @abstractmethod
    def close(self) -> None:
        """Close the database connection."""
        pass
    
    @abstractmethod
    def get_usable_table_names(self) -> List[str]:
        """Get the names of all usable tables."""
        pass
    
    @abstractmethod
    def get_table_info(self, table_name: str) -> str:
        """Get schema information for a table."""
        pass


class SQLiteConnection(DatabaseConnection):
    """SQLite database connection."""
    
    def __init__(self, db_path: str):
        """Initialize the SQLite connection."""
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.langchain_db = None
    
    def connect(self) -> sqlite3.Connection:
        """Connect to the SQLite database."""
        if self.conn is None:
            try:
                self.conn = sqlite3.connect(self.db_path)
                self.cursor = self.conn.cursor()
                self.langchain_db = SQLDatabase.from_uri(f"sqlite:///{self.db_path}")
                logger.info(f"Connected to SQLite database: {self.db_path}")
            except Exception as e:
                logger.error(f"Error connecting to SQLite database: {e}")
                raise
        return self.conn
    
    def execute(self, query: str) -> Any:
        """Execute a query on the SQLite database."""
        if self.conn is None:
            self.connect()
        try:
            result = self.cursor.execute(query)
            self.conn.commit()
            return result
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            raise
    
    def fetch_all(self, query: str) -> List[Dict[str, Any]]:
        """Fetch all results from a query as a list of dictionaries."""
        try:
            self.execute(query)
            columns = [column[0] for column in self.cursor.description]
            results = [dict(zip(columns, row)) for row in self.cursor.fetchall()]
            return results
        except Exception as e:
            logger.error(f"Error fetching results: {e}")
            raise
    
    def fetch_dataframe(self, query: str) -> pd.DataFrame:
        """Fetch results as a pandas DataFrame."""
        try:
            return pd.read_sql_query(query, self.conn)
        except Exception as e:
            logger.error(f"Error fetching DataFrame: {e}")
            raise
    
    def close(self) -> None:
        """Close the SQLite database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None
            logger.info("Closed SQLite database connection.")
    
    def get_usable_table_names(self) -> List[str]:
        """Get the names of all usable tables."""
        return self.langchain_db.get_usable_table_names()
    
    def get_table_info(self, table_name: str) -> str:
        """Get schema information for a table."""
        return self.langchain_db.get_table_info([table_name])


class SnowflakeConnection(DatabaseConnection):
    """Snowflake database connection."""
    
    def __init__(
        self,
        account: str,
        user: str,
        password: str,
        warehouse: str,
        database: str,
        schema: str,
        role: Optional[str] = None
    ):
        """Initialize the Snowflake connection."""
        self.account = account
        self.user = user
        self.password = password
        self.warehouse = warehouse
        self.database = database
        self.schema = schema
        self.role = role
        self.conn = None
        self.cursor = None
        
        # We'll import snowflake.connector lazily to avoid requiring it for SQLite
        self.snowflake_connector = None
    
    def connect(self) -> Any:
        """Connect to the Snowflake database."""
        if self.conn is None:
            try:
                # Lazily import snowflake.connector
                import snowflake.connector
                self.snowflake_connector = snowflake.connector
                
                # Create connection parameters
                conn_params = {
                    'account': self.account,
                    'user': self.user,
                    'password': self.password,
                    'warehouse': self.warehouse,
                    'database': self.database,
                    'schema': self.schema,
                }
                
                if self.role:
                    conn_params['role'] = self.role
                
                # Connect to Snowflake
                self.conn = snowflake.connector.connect(**conn_params)
                self.cursor = self.conn.cursor()
                logger.info(f"Connected to Snowflake database: {self.database}.{self.schema}")
            except ImportError:
                logger.error("snowflake-connector-python is not installed. Please install it to use Snowflake connections.")
                raise
            except Exception as e:
                logger.error(f"Error connecting to Snowflake database: {e}")
                raise
        return self.conn
    
    def execute(self, query: str) -> Any:
        """Execute a query on the Snowflake database."""
        if self.conn is None:
            self.connect()
        try:
            result = self.cursor.execute(query)
            return result
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            raise
    
    def fetch_all(self, query: str) -> List[Dict[str, Any]]:
        """Fetch all results from a query as a list of dictionaries."""
        try:
            self.execute(query)
            columns = [column[0] for column in self.cursor.description]
            results = [dict(zip(columns, row)) for row in self.cursor.fetchall()]
            return results
        except Exception as e:
            logger.error(f"Error fetching results: {e}")
            raise
    
    def fetch_dataframe(self, query: str) -> pd.DataFrame:
        """Fetch results as a pandas DataFrame."""
        try:
            import pandas as pd
            return pd.read_sql_query(query, self.conn)
        except Exception as e:
            logger.error(f"Error fetching DataFrame: {e}")
            raise
    
    def close(self) -> None:
        """Close the Snowflake database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None
            logger.info("Closed Snowflake database connection.")
    
    def get_usable_table_names(self) -> List[str]:
        """Get the names of all usable tables."""
        query = f"SHOW TABLES IN {self.database}.{self.schema};"
        results = self.fetch_all(query)
        return [row["name"] for row in results]
    
    def get_table_info(self, table_name: str) -> str:
        """Get schema information for a table."""
        query = f"DESCRIBE TABLE {self.database}.{self.schema}.{table_name};"
        results = self.fetch_all(query)
        columns = [f"{row['name']} {row['type']}" for row in results]
        return f"CREATE TABLE {table_name} (\n  " + ",\n  ".join(columns) + "\n);"


def get_database_connection(db_type: str, **kwargs) -> DatabaseConnection:
    """Factory function to get the appropriate database connection."""
    if db_type.lower() == "sqlite":
        return SQLiteConnection(kwargs.get("uri", "database.db").replace("sqlite:///", ""))
    elif db_type.lower() == "snowflake":
        return SnowflakeConnection(
            account=kwargs.get("account"),
            user=kwargs.get("username"),
            password=kwargs.get("password"),
            warehouse=kwargs.get("warehouse"),
            database=kwargs.get("database"),
            schema=kwargs.get("schema"),
            role=kwargs.get("role")
        )
    else:
        raise ValueError(f"Unsupported database type: {db_type}")