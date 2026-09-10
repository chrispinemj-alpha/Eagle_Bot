# Eagle Bot Security Baseline

- Never commit secrets, tokens or credentials.
- Use environment variables for provider configuration.
- Deny unknown tools and permissions by default.
- Keep authentication and authorization separate.
- Record consequential actions in an append-only audit system in production.
- Validate all external input at channel boundaries.
- Add rate limiting before exposing public endpoints.
- Add tenant isolation before multi-organization production use.
- Add secure secret storage, TLS, backups and monitoring before production.
- Treat model output as untrusted input when it can influence tools or external actions.

This document describes the baseline, not a claim of production security certification.
