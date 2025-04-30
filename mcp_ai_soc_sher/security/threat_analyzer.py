"""
Security threat analysis for SQL queries.
"""
import re
import json
import logging
from typing import Dict, List, Optional, Any
import os

from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from mcp_ai_soc_sher.common.prompts import SECURITY_THREAT_ANALYSIS_PROMPT


logger = logging.getLogger(__name__)


class ThreatAnalysisResult(BaseModel):
    """Result of a security threat analysis."""
    is_threat: bool = Field(..., description="Whether the query is a security threat")
    threat_level: str = Field(..., description="Threat level (none, low, medium, high)")
    threat_type: List[str] = Field(default_factory=list, description="Types of threats detected")
    explanation: str = Field(..., description="Explanation of the threats detected")
    recommended_action: str = Field(..., description="Recommended action (allow, modify, block)")


class SQLThreatAnalyzer:
    """Analyzer for security threats in SQL queries."""
    
    def __init__(
        self, 
        model: str = "gpt-4", 
        temperature: float = 0.0,
        sensitive_tables: Optional[List[str]] = None,
        suspicious_patterns: Optional[List[str]] = None
    ):
        """Initialize the security threat analyzer."""
        self.model = model
        self.temperature = temperature
        self.sensitive_tables = sensitive_tables or []
        self.suspicious_patterns = suspicious_patterns or []
        
        # Add default suspicious patterns if none provided
        if not self.suspicious_patterns:
            self.suspicious_patterns = [
                r"(?i)DELETE\s+FROM",
                r"(?i)DROP\s+TABLE",
                r"(?i)ALTER\s+TABLE",
                r"(?i)UPDATE\s+.*\s+SET",
                r"(?i)INSERT\s+INTO",
                r"(?i)TRUNCATE\s+TABLE",
                r"(?i)GRANT\s+",
                r"(?i)REVOKE\s+",
                r"(?i)UNION\s+SELECT",
                r"(?i)OR\s+1\s*=\s*1",
                r"(?i);\s*--",
                r"(?i);\s*\/\*",
                r"(?i)SLEEP\s*\(",
                r"(?i)BENCHMARK\s*\(",
                r"(?i)INFORMATION_SCHEMA",
                r"(?i)pg_catalog",
                r"(?i)sys\.",
                r"(?i)xp_cmdshell",
                r"(?i)exec\s*\(",
                r"(?i)INTO\s+OUTFILE",
                r"(?i)INTO\s+DUMPFILE",
            ]
        
        # Initialize LLM
        self.openai_api_key = os.environ.get("OPENAI_API_KEY", "")
        self.llm = ChatOpenAI(
            model=self.model,
            temperature=self.temperature,
            openai_api_key=self.openai_api_key
        )
    
    def analyze_query(self, query: str) -> ThreatAnalysisResult:
        """Analyze a SQL query for security threats."""
        try:
            # Rule-based checks first (fast)
            rule_based_result = self._rule_based_analysis(query)
            if rule_based_result.is_threat and rule_based_result.threat_level in ["medium", "high"]:
                return rule_based_result
            
            # If rule-based analysis doesn't find serious threats, use LLM (more thorough but slower)
            return self._llm_based_analysis(query)
        except Exception as e:
            logger.error(f"Error analyzing SQL query: {e}")
            # Default to safe in case of error
            return ThreatAnalysisResult(
                is_threat=False,
                threat_level="none",
                threat_type=[],
                explanation=f"Error during threat analysis: {e}",
                recommended_action="allow"
            )
    
    def _rule_based_analysis(self, query: str) -> ThreatAnalysisResult:
        """Perform rule-based analysis of the query."""
        detected_patterns = []
        
        # Check for suspicious patterns
        for pattern in self.suspicious_patterns:
            if re.search(pattern, query):
                detected_patterns.append(pattern)
        
        # Check for sensitive tables
        for table in self.sensitive_tables:
            if re.search(rf"\b{re.escape(table)}\b", query, re.IGNORECASE):
                detected_patterns.append(f"Access to sensitive table: {table}")
        
        # Determine threat level based on detected patterns
        if not detected_patterns:
            return ThreatAnalysisResult(
                is_threat=False,
                threat_level="none",
                threat_type=[],
                explanation="No suspicious patterns detected",
                recommended_action="allow"
            )
        
        # Determine threat level and recommendation based on number and type of patterns
        if len(detected_patterns) > 3 or any(
            re.search(pattern, query) for pattern in [
                r"(?i)DROP\s+TABLE",
                r"(?i)DELETE\s+FROM",
                r"(?i)TRUNCATE\s+TABLE",
                r"(?i)INTO\s+OUTFILE",
                r"(?i)INTO\s+DUMPFILE",
                r"(?i)xp_cmdshell",
                r"(?i)exec\s*\("
            ]
        ):
            threat_level = "high"
            recommended_action = "block"
        elif len(detected_patterns) > 1 or any(
            re.search(pattern, query) for pattern in [
                r"(?i)ALTER\s+TABLE",
                r"(?i)UPDATE\s+.*\s+SET",
                r"(?i)INSERT\s+INTO",
                r"(?i)UNION\s+SELECT",
                r"(?i)OR\s+1\s*=\s*1",
                r"(?i)SLEEP\s*\(",
                r"(?i)BENCHMARK\s*\("
            ]
        ):
            threat_level = "medium"
            recommended_action = "modify"
        else:
            threat_level = "low"
            recommended_action = "allow"
        
        return ThreatAnalysisResult(
            is_threat=True,
            threat_level=threat_level,
            threat_type=[f"Suspicious pattern: {pattern}" for pattern in detected_patterns],
            explanation=f"Detected {len(detected_patterns)} suspicious patterns: {', '.join(detected_patterns)}",
            recommended_action=recommended_action
        )
    
    def _llm_based_analysis(self, query: str) -> ThreatAnalysisResult:
        """Perform LLM-based analysis of the query."""
        try:
            prompt = SECURITY_THREAT_ANALYSIS_PROMPT.format(
                query=query,
                sensitive_tables=", ".join(self.sensitive_tables)
            )
            
            response = self.llm.invoke(prompt)
            
            # Parse the JSON response
            try:
                result_dict = json.loads(response.content)
                return ThreatAnalysisResult(**result_dict)
            except Exception as e:
                logger.error(f"Error parsing LLM response as JSON: {e}")
                # Fallback to rule-based result
                return self._rule_based_analysis(query)
        except Exception as e:
            logger.error(f"Error in LLM-based analysis: {e}")
            # Fallback to rule-based result
            return self._rule_based_analysis(query)


class RemoteThreatAnalyzer:
    """Client for a remote threat analysis service."""
    
    def __init__(self, endpoint_url: str, api_key: Optional[str] = None):
        """Initialize the remote threat analyzer."""
        self.endpoint_url = endpoint_url
        self.api_key = api_key
    
    def analyze_query(self, query: str) -> ThreatAnalysisResult:
        """Analyze a SQL query using the remote service."""
        try:
            import requests
            
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            response = requests.post(
                self.endpoint_url,
                headers=headers,
                json={"query": query}
            )
            
            if response.status_code == 200:
                return ThreatAnalysisResult(**response.json())
            else:
                logger.error(f"Error from remote threat analyzer: {response.text}")
                # Fall back to a local analyzer if remote call fails
                local_analyzer = SQLThreatAnalyzer()
                return local_analyzer.analyze_query(query)
        except Exception as e:
            logger.error(f"Error calling remote threat analyzer: {e}")
            # Fall back to a local analyzer if remote call fails
            local_analyzer = SQLThreatAnalyzer()
            return local_analyzer.analyze_query(query)