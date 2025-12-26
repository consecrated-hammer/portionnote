# Security Policy

## Supported Versions

Security updates are applied to the `main` branch.

| Version | Supported |
| ------- | --------- |
| Latest (main) | ✅ Yes |
| < 1.0 | ❌ No |

## Reporting a Vulnerability

**Do not** report security vulnerabilities through public GitHub issues.

### Private Reporting

Send a detailed report to: **consecrated-hammer@outlook.com**

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fixes (if any)

**Response Timeline:**
- Initial response: Within 48 hours
- Status updates: Every 3-5 days
- Resolution: 7-30 days (varies by severity)

## Security Best Practices

### Environment Variables

- **Never commit** `.env` files
- Generate strong `SESSION_SECRET`: `openssl rand -hex 32`
- Rotate secrets periodically
- Use Docker secrets in production

### Database Security

- SQLite database contains session tokens and user data
- Ensure `/data` volume has appropriate permissions
- Backup regularly
- Consider encryption at rest

### Network Security

- **Use HTTPS in production** (Traefik or similar reverse proxy)
- Keep Docker containers updated
- Use firewall rules to restrict access
- Consider VPN for personal use

### Docker Security

- Keep base images updated
- Scan images: `docker scan portionnote`
- Consider running as a non root user for production
- Use Docker secrets for sensitive vars

### Session Management

- Sessions expire after `SESSION_DAYS` (default 14)
- Cookies use `HttpOnly` and `Secure` flags
- Consider shorter lifetime for shared environments

## Known Security Considerations

**CORS:**
- CORS configured for specified origins only
- Update `WEB_ORIGIN`
- Do not use wildcard (`*`) in production

## Security Updates

- Announced through GitHub Releases
- Migration guides provided for breaking changes
- Security reporters credited (with permission)

## Questions?

For security questions (not vulnerabilities), open a GitHub discussion.

Thank you for helping keep PortionNote secure! 🔒
