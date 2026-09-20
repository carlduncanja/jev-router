#!/bin/zsh
set -euo pipefail

PLIST_PATH="$HOME/Library/LaunchAgents/com.jevrouter.codex.plist"
ROUTER_PATH="$HOME/.codex/bin/codex-jev-router-saas"
CONTROL_PATH="$HOME/.codex/bin/jev-router-control"

launchctl bootout "gui/$(id -u)" "$PLIST_PATH" 2>/dev/null || true
if [[ "$(launchctl getenv CODEX_CLI_PATH 2>/dev/null || true)" == "$ROUTER_PATH" ]]; then
  launchctl unsetenv CODEX_CLI_PATH
fi
rm -f "$PLIST_PATH" "$ROUTER_PATH" "$CONTROL_PATH" "$HOME/.codex/jev-router-saas.json"
/usr/bin/security delete-generic-password -a "$USER" -s jev-router-saas >/dev/null 2>&1 || true
print "Removed Jev Router SaaS. Fully quit Codex with Command-Q and reopen it."
