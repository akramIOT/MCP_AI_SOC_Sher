# Security Considerations

This guide covers security considerations for the Text2SQL MCP Server.

## API Key Security

- **OpenAI API Key**: Store your OpenAI API key in the `.env` file or as an environment variable, never hardcode it in your source code.
- **Server API Key**: For the remote server, always set a strong API key to authenticate requests.

## SQL Injection Prevention

The Text2SQL MCP Server includes built-in security threat analysis to detect and prevent SQL injection attacks:

1. **Rule-Based Analysis**: Fast pattern matching for common SQL injection patterns.
2. **LLM-Based Analysis**: More thorough analysis using a language model.

### Enabling Security Threat Analysis

Enable security threat analysis in your configuration:

```
MCP_SECURITY_ENABLE_THREAT_ANALYSIS=true
```

### Security Levels

The security analyzer classifies threats into different levels:

- **None**: No security threats detected.
- **Low**: Minor issues that may not be harmful.
- **Medium**: Potential security concerns that should be reviewed.
- **High**: Serious security threats that should be blocked.

### Recommended Actions

Based on the threat level, the system recommends one of the following actions:

- **Allow**: Allow the query to be executed.
- **Modify**: The query should be modified before execution.
- **Block**: The query should be blocked completely.

### Sensitive Tables

You can define sensitive tables that require special attention:

```
MCP_SECURITY_SENSITIVE_TABLES=users,credentials,payments,accounts
```

### Suspicious Patterns

You can define custom suspicious patterns to check for:

```
MCP_SECURITY_SUSPICIOUS_PATTERNS="(?i)DELETE\\s+FROM,(?i)DROP\\s+TABLE"
```

## Remote Security Analysis

For increased security, you can use a separate server for security threat analysis:

```
MCP_SECURITY_REMOTE_ENDPOINT=https://security-analysis-server.example.com/api/analyze
```

## Network Security

- The server binds to `0.0.0.0` by default, which makes it accessible from any network interface.
- For production, consider using a reverse proxy with TLS/SSL.
- Use firewall rules to restrict access to the server.

## Database Security

- Use a dedicated database user with limited permissions.
- For Snowflake, use a role with appropriate permissions.
- Store database credentials securely in environment variables.

## Authentication

- The remote server uses API key authentication.
- All endpoints (except `/api/health`) require authentication.
- Use a strong, random API key for production.

## CORS Configuration

By default, CORS is enabled for all origins (`*`). For production, restrict it to your trusted domains:

```
MCP_SERVER_ALLOW_CORS=true
MCP_SERVER_CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

## Best Practices

1. **Regular Updates**: Keep the server and its dependencies up to date.
2. **Monitoring**: Monitor server logs for suspicious activity.
3. **Rate Limiting**: Implement rate limiting to prevent abuse.
4. **Input Validation**: Validate all input before processing.
5. **Output Sanitization**: Ensure output doesn't contain sensitive information.