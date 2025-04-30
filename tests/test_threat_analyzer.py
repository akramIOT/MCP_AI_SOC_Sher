"""
Tests for the security threat analyzer.
"""
import unittest
from unittest.mock import patch, MagicMock

from mcp_server.security.threat_analyzer import SQLThreatAnalyzer, ThreatAnalysisResult


class TestSQLThreatAnalyzer(unittest.TestCase):
    """Test the SQL threat analyzer."""
    
    def setUp(self):
        """Set up test environment."""
        self.analyzer = SQLThreatAnalyzer(
            sensitive_tables=["users", "credentials"],
            suspicious_patterns=[
                r"(?i)DELETE\s+FROM",
                r"(?i)DROP\s+TABLE",
                r"(?i)UNION\s+SELECT"
            ]
        )
    
    def test_safe_query(self):
        """Test analysis of a safe query."""
        query = "SELECT id, name FROM products WHERE category = 'electronics';"
        result = self.analyzer._rule_based_analysis(query)
        
        self.assertFalse(result.is_threat)
        self.assertEqual(result.threat_level, "none")
        self.assertEqual(len(result.threat_type), 0)
        self.assertEqual(result.recommended_action, "allow")
    
    def test_query_with_sensitive_table(self):
        """Test analysis of a query accessing sensitive tables."""
        query = "SELECT * FROM users WHERE username = 'admin';"
        result = self.analyzer._rule_based_analysis(query)
        
        self.assertTrue(result.is_threat)
        self.assertIn("Access to sensitive table: users", result.threat_type[0])
        self.assertEqual(result.recommended_action, "allow")  # Low threat level
    
    def test_dangerous_query(self):
        """Test analysis of a dangerous query."""
        query = "DROP TABLE products;"
        result = self.analyzer._rule_based_analysis(query)
        
        self.assertTrue(result.is_threat)
        self.assertEqual(result.threat_level, "high")
        self.assertEqual(result.recommended_action, "block")
    
    def test_medium_threat_query(self):
        """Test analysis of a medium threat query."""
        query = "SELECT * FROM products UNION SELECT * FROM users;"
        result = self.analyzer._rule_based_analysis(query)
        
        self.assertTrue(result.is_threat)
        self.assertEqual(result.threat_level, "medium")
        self.assertEqual(result.recommended_action, "modify")
    
    @patch('mcp_server.security.threat_analyzer.ChatOpenAI')
    def test_llm_based_analysis(self, mock_chat_openai):
        """Test the LLM-based analysis."""
        # Mock the LLM response
        mock_llm = MagicMock()
        mock_content = MagicMock()
        mock_content.content = '{"is_threat": true, "threat_level": "medium", "threat_type": ["SQL Injection"], "explanation": "The query contains potential SQL injection", "recommended_action": "modify"}'
        mock_llm.invoke.return_value = mock_content
        mock_chat_openai.return_value = mock_llm
        
        query = "SELECT * FROM users WHERE username = 'admin' OR 1=1;"
        result = self.analyzer._llm_based_analysis(query)
        
        self.assertTrue(result.is_threat)
        self.assertEqual(result.threat_level, "medium")
        self.assertEqual(result.threat_type, ["SQL Injection"])
        self.assertEqual(result.recommended_action, "modify")
    
    @patch('mcp_server.security.threat_analyzer.ChatOpenAI')
    def test_analyze_query_calls_llm_for_low_threat(self, mock_chat_openai):
        """Test that analyze_query calls LLM for low threats."""
        # Mock rule_based_analysis to return a low threat
        self.analyzer._rule_based_analysis = MagicMock(return_value=ThreatAnalysisResult(
            is_threat=True,
            threat_level="low",
            threat_type=["Access to sensitive table: users"],
            explanation="Detected sensitive table access",
            recommended_action="allow"
        ))
        
        # Mock the LLM response
        mock_llm = MagicMock()
        mock_content = MagicMock()
        mock_content.content = '{"is_threat": true, "threat_level": "medium", "threat_type": ["Data Exfiltration"], "explanation": "The query attempts to access sensitive data", "recommended_action": "modify"}'
        mock_llm.invoke.return_value = mock_content
        mock_chat_openai.return_value = mock_llm
        
        # Call analyze_query
        query = "SELECT * FROM users;"
        result = self.analyzer.analyze_query(query)
        
        # Verify that the LLM was called
        self.assertEqual(result.threat_level, "medium")
        self.assertEqual(result.threat_type, ["Data Exfiltration"])


if __name__ == "__main__":
    unittest.main()