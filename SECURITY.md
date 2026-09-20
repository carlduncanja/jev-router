# Security

## Credentials

- Store `TYPESAFE_API_KEY` only in the hosting provider's secret manager.
- Issue a unique random customer token for each account and store only its SHA-256 hash server-side.
- The macOS client stores its customer token in Keychain under service `jev-router-saas`.
- Rotate provider and customer credentials after suspected exposure.

## Prompt data

The client sends at most 6,000 characters from the current user prompt. It removes common API-key, bearer-token, password, secret, and private-key patterns before transmission. Redaction reduces accidental disclosure but cannot guarantee that all sensitive data is removed.

Do not log HTTP bodies, authorization headers, or prompt text. Record only tenant ID, timestamp, latency, selected route, status code, and metering totals. Define a short retention period and a deletion process.

## Deployment

- Require HTTPS and reject redirects.
- Put the API behind a managed gateway or WAF with per-customer rate and spend limits.
- Keep the container and Python dependencies patched.
- Run the container as an unprivileged user.
- Verify Codex Desktop compatibility before every client release.
- Sign and notarize public macOS packages.

Report vulnerabilities privately to the operator's published security contact.
