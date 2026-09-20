---
name: jev-router
description: Configure, diagnose, or explain Jev Router SaaS model and reasoning-effort selection for Codex Desktop.
---

# Jev Router SaaS

Use the package README and local diagnostic script to help the user install or troubleshoot the router.

- Never ask for or display the TypeSafe provider key. It belongs only on the SaaS server.
- Customer tokens are individual, revocable credentials and belong in macOS Keychain under service `jev-router-saas`.
- The client sends at most 6,000 redacted prompt characters to the configured HTTPS endpoint.
- Run `${PLUGIN_ROOT}/scripts/doctor.sh` for a read-only health check.
- Explain that the Codex composer picker can retain its manually selected value; the per-turn commentary item reports the effective routed model and effort.
- Supported overrides are `[astra]`, `[sol]`, `[terra]`, `[luna]`, `[high]`, `[medium]`, `[low]`, and `[no-jev]`.
