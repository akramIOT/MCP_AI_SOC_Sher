"""
Text2SQL Agent implementation for the MCP Server.
"""
import os
import json
from typing import Dict, List, Optional, Any, Tuple
import logging
from pydantic import BaseModel, Field

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from langchain_core.prompts import FewShotPromptTemplate, SystemMessagePromptTemplate
from langchain_core.example_selectors import SemanticSimilarityExampleSelector
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.agents.agent_toolkits import create_sql_agent
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.tools import BaseTool, tool
from langchain_community.agent_toolkits import create_retriever_tool

from .prompts import SQL_SYSTEM_PREFIX, SQL_GENERATION_PROMPT, SQL_OPTIMIZATION_PROMPT
from .db_utils import DatabaseConnection


logger = logging.getLogger(__name__)


class QueryRequest(BaseModel):
    """Request model for SQL query generation."""
    query: str = Field(..., description="Natural language query")
    optimize: bool = Field(False, description="Whether to optimize the generated SQL")
    execute: bool = Field(False, description="Whether to execute the generated SQL")
    explain: bool = Field(False, description="Whether to explain the generated SQL")
    dialect: str = Field("SQLite", description="SQL dialect to use")
    top_k: int = Field(10, description="Maximum number of results to return")


class QueryResponse(BaseModel):
    """Response model for SQL query generation."""
    sql: str = Field(..., description="Generated SQL query")
    optimized_sql: Optional[str] = Field(None, description="Optimized SQL query")
    results: Optional[List[Dict[str, Any]]] = Field(None, description="Query results")
    explanation: Optional[str] = Field(None, description="Explanation of the SQL query")
    error: Optional[str] = Field(None, description="Error message if query generation failed")


class Text2SQLAgent:
    """Agent for converting natural language to SQL queries."""
    
    def __init__(
        self,
        db_connection: DatabaseConnection,
        model: str = "gpt-4",
        temperature: float = 0.0,
        use_examples: bool = True,
        examples_count: int = 5,
        examples: Optional[List[Dict[str, str]]] = None,
    ):
        """Initialize the Text2SQL agent."""
        self.db_connection = db_connection
        self.model = model
        self.temperature = temperature
        self.use_examples = use_examples
        self.examples_count = examples_count
        self.examples = examples or []
        
        # Set up OpenAI API key from environment
        self.openai_api_key = os.environ.get("OPENAI_API_KEY", "")
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model=self.model,
            temperature=self.temperature,
            openai_api_key=self.openai_api_key
        )
        
        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(openai_api_key=self.openai_api_key)
        
        # Connect to database
        self.db_connection.connect()
        
        # Build agent
        self.agent = self._build_agent()
    
    def _build_agent(self) -> AgentExecutor:
        """Build the Text2SQL agent."""
        # Get table info for context
        table_names = self.db_connection.get_usable_table_names()
        table_info = []
        for table in table_names:
            table_info.append(self.db_connection.get_table_info(table))
        table_info_str = "\n\n".join(table_info)
        
        # Build prompt
        if self.use_examples and self.examples:
            example_selector = SemanticSimilarityExampleSelector.from_examples(
                self.examples,
                self.embeddings,
                FAISS,
                k=self.examples_count,
                input_keys=["input"],
            )
            few_shot_prompt = FewShotPromptTemplate(
                example_selector=example_selector,
                example_prompt=PromptTemplate.from_template(
                    "User input: {input}\nSQL query: {query}"
                ),
                input_variables=["input", "dialect", "top_k", "table_info"],
                prefix=SQL_SYSTEM_PREFIX,
                suffix="",
            )
            full_prompt = ChatPromptTemplate.from_messages(
                [
                    SystemMessagePromptTemplate(prompt=few_shot_prompt),
                    ("human", "{input}"),
                    MessagesPlaceholder("agent_scratchpad"),
                ]
            )
            
            agent = create_sql_agent(
                llm=self.llm,
                db=self.db_connection.langchain_db,
                prompt=full_prompt,
                agent_type="openai-tools",
                verbose=True
            )
        else:
            # Create a simpler prompt without examples
            system_template = SQL_SYSTEM_PREFIX.format(
                dialect="SQLite",  # This will be overridden at runtime
                top_k=10,  # This will be overridden at runtime
                table_info=table_info_str
            )
            prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", system_template),
                    ("human", "{input}"),
                    MessagesPlaceholder("agent_scratchpad"),
                ]
            )
            
            agent = create_sql_agent(
                llm=self.llm,
                db=self.db_connection.langchain_db,
                prompt=prompt,
                agent_type="openai-tools",
                verbose=True
            )
        
        return agent
    
    def generate_sql(self, request: QueryRequest) -> QueryResponse:
        """Generate a SQL query from natural language."""
        try:
            # Create agent input
            agent_input = {
                "input": request.query,
                "dialect": request.dialect,
                "top_k": request.top_k,
                "table_info": self._get_table_info_str()
            }
            
            # Run agent
            result = self.agent.invoke(agent_input)
            sql_query = self._extract_sql_query(result)
            
            response = QueryResponse(sql=sql_query)
            
            # Optimize SQL if requested
            if request.optimize and sql_query:
                response.optimized_sql = self._optimize_sql(sql_query, request.dialect)
            
            # Execute SQL if requested
            if request.execute and (response.optimized_sql or sql_query):
                query_to_execute = response.optimized_sql or sql_query
                response.results = self._execute_sql(query_to_execute)
            
            # Explain SQL if requested
            if request.explain and sql_query:
                response.explanation = self._explain_sql(sql_query)
            
            return response
        except Exception as e:
            logger.error(f"Error generating SQL: {e}")
            return QueryResponse(
                sql="",
                error=str(e)
            )
    
    def _get_table_info_str(self) -> str:
        """Get table information as a string."""
        table_names = self.db_connection.get_usable_table_names()
        table_info = []
        for table in table_names:
            table_info.append(self.db_connection.get_table_info(table))
        return "\n\n".join(table_info)
    
    def _extract_sql_query(self, agent_result: Dict[str, Any]) -> str:
        """Extract the SQL query from the agent result."""
        if "output" in agent_result:
            # Try to find the SQL query in the output
            output = agent_result["output"]
            if "```sql" in output:
                # Extract code from markdown
                sql_blocks = output.split("```sql")
                if len(sql_blocks) > 1:
                    sql_query = sql_blocks[1].split("```")[0].strip()
                    return sql_query
            
            # Try to find SQL query with simple pattern matching
            lines = output.split("\n")
            for i, line in enumerate(lines):
                if "SELECT" in line or "WITH" in line or "CREATE" in line:
                    # Found the start of a SQL query, try to extract it
                    sql_lines = []
                    j = i
                    while j < len(lines) and ";" not in lines[j]:
                        sql_lines.append(lines[j])
                        j += 1
                    if j < len(lines):
                        sql_lines.append(lines[j])  # Add the line with the semicolon
                    if sql_lines:
                        return "\n".join(sql_lines).strip()
        
        # If we can't find a SQL query, return an empty string
        return ""
    
    def _optimize_sql(self, sql_query: str, dialect: str) -> str:
        """Optimize a SQL query."""
        try:
            prompt = SQL_OPTIMIZATION_PROMPT.format(
                query=sql_query,
                dialect=dialect
            )
            response = self.llm.invoke(prompt)
            return response.content
        except Exception as e:
            logger.error(f"Error optimizing SQL: {e}")
            return sql_query
    
    def _execute_sql(self, sql_query: str) -> List[Dict[str, Any]]:
        """Execute a SQL query."""
        try:
            return self.db_connection.fetch_all(sql_query)
        except Exception as e:
            logger.error(f"Error executing SQL: {e}")
            return []
    
    def _explain_sql(self, sql_query: str) -> str:
        """Explain a SQL query."""
        try:
            prompt = f"Explain the following SQL query in simple terms:\n\n{sql_query}"
            response = self.llm.invoke(prompt)
            return response.content
        except Exception as e:
            logger.error(f"Error explaining SQL: {e}")
            return ""


# Additional tools for the agent
class AgentTools:
    """Tools for the Text2SQL agent."""
    
    @staticmethod
    @tool
    def generate_sql_query(requirement: str, dialect: str = "SQLite") -> str:
        """Generate a SQL query from natural language."""
        try:
            llm = ChatOpenAI(model="gpt-4", temperature=0.0)
            prompt = SQL_GENERATION_PROMPT.format(
                requirement=requirement,
                dialect=dialect
            )
            response = llm.invoke(prompt)
            return response.content
        except Exception as e:
            logger.error(f"Error generating SQL query: {e}")
            return ""
    
    @staticmethod
    @tool
    def improve_sql_query(query: str, dialect: str = "SQLite") -> str:
        """Improve and optimize the given SQL query."""
        try:
            llm = ChatOpenAI(model="gpt-4", temperature=0.0)
            prompt = SQL_OPTIMIZATION_PROMPT.format(
                query=query,
                dialect=dialect
            )
            response = llm.invoke(prompt)
            return response.content
        except Exception as e:
            logger.error(f"Error improving SQL query: {e}")
            return ""
    
    @staticmethod
    @tool
    def execute_sql_query(query: str, connection: Any) -> List[Dict[str, Any]]:
        """Execute a SQL query and return the results."""
        try:
            if hasattr(connection, "fetch_all"):
                return connection.fetch_all(query)
            else:
                # Fallback for sqlite3.Connection objects
                cursor = connection.cursor()
                cursor.execute(query)
                columns = [column[0] for column in cursor.description]
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]
                cursor.close()
                return results
        except Exception as e:
            logger.error(f"Error executing SQL query: {e}")
            return []