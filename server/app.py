from __future__ import annotations

import asyncio
from collections import defaultdict, deque
import hashlib
import hmac
import json
import math
import os
import threading
import time
import urllib.request

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field


TYPESAFE_ENDPOINT = os.environ.get("TYPESAFE_ENDPOINT", "https://api.typesafe.ai/v1/systemone")
JEV_MODEL = os.environ.get("JEV_MODEL", "jev-1.13.0")
TYPE_SAFE_KEY = os.environ.get("TYPESAFE_API_KEY", "").strip()
CLIENT_KEY_HASHES = tuple(
    value.strip().lower()
    for value in os.environ.get("CLIENT_KEY_HASHES", "").split(",")
    if value.strip()
)
RATE_LIMIT = max(1, int(os.environ.get("RATE_LIMIT_PER_MINUTE", "30")))
MODELS = {"gpt-6-astra", "gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna"}
EFFORTS = {"low", "medium", "high", "xhigh", "max"}
REQUESTS: dict[str, deque[float]] = defaultdict(deque)
REQUESTS_LOCK = threading.Lock()


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class RouteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    prompt: str = Field(min_length=1, max_length=6000)
    current_model: str | None = None
    current_effort: str | None = None
    allowed_models: list[str] | None = None
    allowed_efforts: list[str] | None = None


class RouteResponse(BaseModel):
    model: str
    effort: str
    source: str


def authorize(authorization: str | None = Header(default=None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    token = authorization[7:].strip()
    digest = hashlib.sha256(token.encode()).hexdigest()
    if not CLIENT_KEY_HASHES or not any(hmac.compare_digest(digest, expected) for expected in CLIENT_KEY_HASHES):
        raise HTTPException(status_code=401, detail="Invalid Bearer token")
    now = time.monotonic()
    with REQUESTS_LOCK:
        bucket = REQUESTS[digest]
        while bucket and bucket[0] <= now - 60:
            bucket.popleft()
        if len(bucket) >= RATE_LIMIT:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        bucket.append(now)
    return digest


def valid_confidence(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def allowed(values: list[str] | None, known: set[str]) -> set[str]:
    selected = set(values or known) & known
    if not selected:
        raise ValueError("No supported routing choices were supplied")
    return selected


def classify(prompt: str, allowed_models: set[str], allowed_efforts: set[str]) -> RouteResponse:
    if not TYPE_SAFE_KEY:
        raise RuntimeError("TYPESAFE_API_KEY is not configured")
    payload = {
        "model": JEV_MODEL,
        "state": {
            "request": prompt,
            "policy": {
                "low": "One-step, unambiguous, reversible work such as concise answers, formatting, lookups, or tiny mechanical edits.",
                "medium": "Normal coding, research, analysis, or multi-step work with limited uncertainty.",
                "high": "Complex debugging, architecture, broad implementation, difficult synthesis, high uncertainty, or consequential decisions.",
                "gpt-5.6-luna": "Fast lightweight work: short answers, simple lookups, formatting, or tiny mechanical edits.",
                "gpt-5.6-terra": "Focused routine coding: direct implementation, contained debugging, tests, and ordinary repository edits.",
                "gpt-5.6-sol": "Reliable everyday agentic work: multi-step coding, research, analysis, and moderately difficult debugging.",
                "gpt-6-astra": "The hardest work: architecture, broad refactors, difficult synthesis, high uncertainty, or consequential decisions.",
            },
        },
        "questions": {
            "effort": {
                "type": "choice",
                "instructions": "Choose the lowest reasoning effort likely to complete the request correctly.",
                "criteria": {value: f"The {value} policy applies." for value in sorted(allowed_efforts)},
            },
            "model": {
                "type": "choice",
                "instructions": "Choose the least expensive Codex model likely to complete the request correctly. Reserve GPT-6 Astra for genuinely difficult work.",
                "criteria": {value: f"The {value} policy applies." for value in sorted(allowed_models)},
            },
        },
    }
    request = urllib.request.Request(
        TYPESAFE_ENDPOINT,
        data=json.dumps(payload, separators=(",", ":")).encode(),
        headers={"Authorization": f"Bearer {TYPE_SAFE_KEY}", "Content-Type": "application/json"},
    )
    with urllib.request.build_opener(NoRedirect).open(request, timeout=5) as response:
        result = json.load(response)
    effort_answer = result["answers"]["effort"]
    model_answer = result["answers"]["model"]
    effort = effort_answer.get("choice")
    model = model_answer.get("choice")
    effort_confidence = effort_answer.get("confidence")
    model_confidence = model_answer.get("confidence")
    if effort not in allowed_efforts or model not in allowed_models:
        raise ValueError("Jev returned an unsupported route")
    if not valid_confidence(effort_confidence) or not valid_confidence(model_confidence):
        raise ValueError("Jev returned invalid confidence")
    source = "jev"
    if effort == "low" and effort_confidence < 0.65 and "medium" in allowed_efforts:
        effort = "medium"
        source = "jev-uncertain"
    if model == "gpt-5.6-luna" and model_confidence < 0.65 and "gpt-5.6-terra" in allowed_models:
        model = "gpt-5.6-terra"
        source = "jev-uncertain"
    return RouteResponse(model=model, effort=effort, source=source)


app = FastAPI(title="Jev Router SaaS", version="0.1.0", docs_url=None, redoc_url=None)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/route", response_model=RouteResponse)
async def route(body: RouteRequest, _client: str = Depends(authorize)) -> RouteResponse:
    try:
        return await asyncio.to_thread(
            classify, body.prompt, allowed(body.allowed_models, MODELS), allowed(body.allowed_efforts, EFFORTS)
        )
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=502, detail="Routing provider unavailable") from error
