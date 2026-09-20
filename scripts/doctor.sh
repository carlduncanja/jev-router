#!/bin/zsh
set -euo pipefail

ROUTER_PATH="$HOME/.codex/bin/codex-jev-router-saas"
CONFIG_PATH="$HOME/.codex/jev-router-saas.json"

[[ -x "$ROUTER_PATH" ]] || { print -u2 "Router is not installed."; exit 1; }
python3 -m py_compile "$ROUTER_PATH"
ENDPOINT="$(python3 - "$CONFIG_PATH" <<'PY'
import json, sys
print(json.load(open(sys.argv[1], encoding="utf-8"))["endpoint"])
PY
)"
TOKEN="$(/usr/bin/security find-generic-password -a "$USER" -s jev-router-saas -w)"
RESPONSE="$(curl --fail --silent --show-error --max-time 8 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  --data '{"prompt":"Reply with a concise greeting.","current_model":"gpt-6-astra","current_effort":"medium"}' \
  "$ENDPOINT")"
python3 - "$RESPONSE" <<'PY'
import json, sys
value=json.loads(sys.argv[1])
assert value["model"] in {"gpt-6-astra","gpt-5.6-sol","gpt-5.6-terra","gpt-5.6-luna"}
assert value["effort"] in {"low","medium","high"}
print(f"Routing endpoint passed: {value['model']} / {value['effort']}")
PY
print "CODEX_CLI_PATH=$(launchctl getenv CODEX_CLI_PATH)"
