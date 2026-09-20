#!/bin/zsh
set -euo pipefail

PLUGIN_ROOT="${0:A:h:h}"
ENDPOINT="${1:-}"
INSTALL_DIR="$HOME/.codex/bin"
ROUTER_PATH="$INSTALL_DIR/codex-jev-router-saas"
CONTROL_PATH="$INSTALL_DIR/jev-router-control"
CONFIG_PATH="$HOME/.codex/jev-router-saas.json"
PLIST_PATH="$HOME/Library/LaunchAgents/com.jevrouter.codex.plist"

if [[ "$(uname -s)" != "Darwin" ]]; then
  print -u2 "This installer currently supports macOS only."
  exit 1
fi

if [[ ! -x /Applications/ChatGPT.app/Contents/Resources/codex ]]; then
  print -u2 "Codex Desktop was not found in /Applications/ChatGPT.app."
  exit 1
fi

if [[ -z "$ENDPOINT" ]]; then
  read "ENDPOINT?HTTPS routing endpoint (for example https://router.example.com/v1/route): "
fi
if [[ "$ENDPOINT" != https://* && "$ENDPOINT" != http://127.0.0.1:* && "$ENDPOINT" != http://localhost:* ]]; then
  print -u2 "The routing endpoint must use HTTPS."
  exit 1
fi

read -s "CLIENT_TOKEN?Customer SaaS token: "
print
if [[ -z "$CLIENT_TOKEN" ]]; then
  print -u2 "A customer SaaS token is required."
  exit 1
fi

mkdir -p "$INSTALL_DIR" "$HOME/.codex/log" "$HOME/Library/LaunchAgents"
install -m 700 "$PLUGIN_ROOT/client/codex-jev-router" "$ROUTER_PATH"
install -m 700 "$PLUGIN_ROOT/control-panel/jev-router-control" "$CONTROL_PATH"
/usr/bin/security add-generic-password -U -a "$USER" -s jev-router-saas -w "$CLIENT_TOKEN" >/dev/null

python3 - "$CONFIG_PATH" "$ENDPOINT" <<'PY'
import json, os, sys
path, endpoint = sys.argv[1:]
with open(path, "w", encoding="utf-8") as handle:
    json.dump({"endpoint": endpoint}, handle, separators=(",", ":"))
    handle.write("\n")
os.chmod(path, 0o600)
PY

cat > "$PLIST_PATH" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.jevrouter.codex</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/launchctl</string>
    <string>setenv</string>
    <string>CODEX_CLI_PATH</string>
    <string>$ROUTER_PATH</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
</dict>
</plist>
EOF
chmod 600 "$PLIST_PATH"

launchctl bootout "gui/$(id -u)" "$PLIST_PATH" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST_PATH"
launchctl setenv CODEX_CLI_PATH "$ROUTER_PATH"

print "Installed Jev Router SaaS. Run ~/.codex/bin/jev-router-control to choose allowed models and efforts."
print "Fully quit Codex with Command-Q and reopen it."
