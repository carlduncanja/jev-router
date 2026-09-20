# Jev Router SaaS

Jev Router SaaS keeps one TypeSafe API key on your server and gives every customer a separate, revocable client token. The Codex Desktop client sends at most 6,000 redacted prompt characters to your service. Your service asks Jev to select both:

- Model: GPT-6 Astra, GPT-5.6 Sol, GPT-5.6 Terra, or GPT-5.6 Luna
- Reasoning effort: Low, Medium, High, XHigh, or Max (subject to the selected model's support)

The local router writes those choices into both `turn/start` and the active collaboration-mode settings. It never distributes the TypeSafe key.

## Architecture

```text
Codex Desktop
  -> local router (redaction, overrides, fallback)
  -> your HTTPS /v1/route endpoint (customer Bearer token)
  -> TypeSafe Jev (your server-side TypeSafe key)
  -> { model, effort }
  -> Codex App Server
```

Your server sees the redacted prompt text because it must classify it. Do not log request bodies. Publish a privacy policy that states what is sent, retained, and shared with TypeSafe.

## Deploy the API

Build the included container on a platform such as Fly.io, Railway, Render, Google Cloud Run, or AWS App Runner.

```sh
cd server
docker build -t jev-router-saas .
docker run --rm -p 8080:8080 \
  -e TYPESAFE_API_KEY='your-typesafe-key' \
  -e CLIENT_KEY_HASHES='sha256-of-customer-token' \
  jev-router-saas
```

Generate one customer token and its server-side hash:

```sh
python3 scripts/generate_client_key.py
```

Give the customer the token once. Add only its SHA-256 hash to `CLIENT_KEY_HASHES`. For a real paid service, store token hashes and subscription state in a database or API gateway instead of the environment variable.

The public endpoint must use HTTPS. Check it with:

```sh
curl https://router.example.com/healthz
```

## Install the macOS client

From the package root:

```sh
./scripts/install.sh https://router.example.com/v1/route
```

The installer asks for the customer's SaaS token using hidden input, stores it in macOS Keychain, installs the router under `~/.codex/bin`, and registers a per-user LaunchAgent. Fully quit and reopen Codex afterward.

Run diagnostics:

```sh
./scripts/doctor.sh
```

## Customer control panel

Run this after installation:

```sh
~/.codex/bin/jev-router-control
```

It opens a local-only page where customers choose the models and reasoning efforts Jev may use. Save applies the choices to future turns; **Restart Codex** quits and reopens Codex after the customer clicks it.

Remove it:

```sh
./scripts/uninstall.sh
```

## Prompt overrides

- `[astra]`, `[sol]`, `[terra]`, or `[luna]`
- `[max]`, `[xhigh]`, `[high]`, `[medium]`, or `[low]`
- Combine them, for example `[astra] [high]`.
- `[no-jev]` keeps the current Codex model and effort.

If the SaaS request fails, the client keeps the current model when available and falls back to GPT-6 Astra with Medium reasoning otherwise.

## Production checklist

- Confirm your TypeSafe order permits this customer application. TypeSafe's current Master Customer Agreement allows API integration into customer applications for end users, while prohibiting offering TypeSafe as a standalone service. Get written confirmation that your routing product and expected volume fit your order.
- Rotate the TypeSafe key that was previously pasted into a chat before deployment.
- Give every customer a unique client token.
- Enforce per-customer rate and spend limits at the gateway or database layer.
- Sign and notarize the macOS installer before distributing it broadly.
- Pin and test supported Codex Desktop versions because the client wraps the App Server transport.
- Publish privacy, acceptable-use, deletion, and subprocessors policies.
- Add billing webhooks that disable or rotate customer tokens when subscriptions change.
- Monitor counts, latency, model choice, and errors without logging prompt text.

## Packaging boundary

The included Codex plugin provides discovery and setup guidance. A plugin hook cannot currently change the model or reasoning effort on `turn/start`, so the local router remains required.
