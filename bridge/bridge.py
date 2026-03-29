"""
AgentNext Billing Bridge — ObserveLLM (Langfuse) → Lago Metering

Two modes:
  1. Webhook receiver  — accepts POST from Langfuse Cloud webhooks (port BRIDGE_PORT)
  2. Poller            — polls Langfuse OSS API on an interval (OSS has no webhooks)

Both paths feed into process_trace(), which bills Lago for:
  - llm_tokens      : sum of input+output tokens across all observations in the trace
  - api_calls       : 1 per trace
  - workflow_runs   : 1 per trace
  - agent_runs      : 1 per trace tagged agentstudio / agent_run / simstudio,
                      or whose name starts with "agent"
"""

import os
import json
import base64
import logging
import threading
import time
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.request import Request, urlopen
from urllib.error import URLError

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("billing-bridge")

LAGO_API_URL  = os.environ.get("LAGO_API_URL", "http://billing-api:3000")
LAGO_API_KEY  = os.environ.get("LAGO_API_KEY", "")

LANGFUSE_URL        = os.environ.get("LANGFUSE_URL", "http://observellm:3000")
LANGFUSE_PUBLIC_KEY = os.environ.get("LANGFUSE_PUBLIC_KEY", "")
LANGFUSE_SECRET_KEY = os.environ.get("LANGFUSE_SECRET_KEY", "")
POLL_INTERVAL       = int(os.environ.get("POLL_INTERVAL", "30"))   # seconds

# Tags that mark an AgentStudio agent run
AGENT_TAGS = {"agentstudio", "agent_run", "simstudio"}


# ── Lago ─────────────────────────────────────────────────────────────────────

def send_event(tid, sub, code, val, props=None):
    """Send a usage event to Lago."""
    if not LAGO_API_KEY:
        log.warning("LAGO_API_KEY not set — skipping billing event %s", code)
        return
    payload = {
        "event": {
            "transaction_id": tid,
            "external_subscription_id": sub,
            "code": code,
            "timestamp": int(time.time()),
            "properties": {**(props or {}), "value": str(val)},
        }
    }
    try:
        req = Request(
            f"{LAGO_API_URL}/api/v1/events",
            json.dumps(payload).encode(),
            method="POST",
            headers={
                "Authorization": f"Bearer {LAGO_API_KEY}",
                "Content-Type": "application/json",
            },
        )
        urlopen(req, timeout=10)
        log.info("billed %s=%s for sub=%s", code, val, sub)
    except URLError as e:
        log.error("billing failed %s: %s", code, e)


# ── Trace processing ──────────────────────────────────────────────────────────

def process_trace(trace):
    """Extract usage from a Langfuse trace and send billing events to Lago."""
    tid  = trace.get("id", "unknown")
    uid  = trace.get("userId", "default")
    wf   = trace.get("name", "unknown")
    tags = set(trace.get("tags") or [])
    observations = trace.get("observations", [])

    # Token count — sum across all LLM observations in this trace
    tokens = sum(
        (o.get("usage", {}).get("input", 0) or 0)
        + (o.get("usage", {}).get("output", 0) or 0)
        for o in observations
    )

    if tokens > 0:
        send_event(f"{tid}-tok", uid, "llm_tokens", tokens, {"workflow": wf})

    send_event(f"{tid}-api", uid, "api_calls",     1, {"workflow": wf})
    send_event(f"{tid}-wf",  uid, "workflow_runs", 1, {"workflow": wf})

    if tags & AGENT_TAGS or wf.startswith("agent"):
        send_event(f"{tid}-ar", uid, "agent_runs", 1, {"workflow": wf})
        log.info("agent_run billed trace=%s user=%s tokens=%s", tid, uid, tokens)


# ── Langfuse poller ───────────────────────────────────────────────────────────

def _langfuse_auth():
    """Base64 Basic-auth header for Langfuse public/secret key pair."""
    creds = f"{LANGFUSE_PUBLIC_KEY}:{LANGFUSE_SECRET_KEY}"
    return "Basic " + base64.b64encode(creds.encode()).decode()


def fetch_traces_since(since_iso: str, page: int = 1):
    """Fetch one page of traces from Langfuse created after since_iso."""
    url = (
        f"{LANGFUSE_URL}/api/public/traces"
        f"?fromTimestamp={since_iso}&limit=50&page={page}"
    )
    req = Request(url, headers={"Authorization": _langfuse_auth()})
    resp = urlopen(req, timeout=15)
    return json.loads(resp.read())


def fetch_trace_with_observations(trace_id: str):
    """Fetch a single trace including its observations."""
    url = f"{LANGFUSE_URL}/api/public/traces/{trace_id}"
    req = Request(url, headers={"Authorization": _langfuse_auth()})
    resp = urlopen(req, timeout=15)
    return json.loads(resp.read())


def poll_langfuse():
    """
    Background thread: poll Langfuse for new completed traces and bill them.

    Uses a sliding window: remembers the timestamp of the last successful poll
    and only fetches traces created after that point.
    """
    if not (LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY):
        log.warning("LANGFUSE keys not set — Langfuse polling disabled")
        return

    # Start from now minus one interval to catch any traces created
    # while the bridge was starting up.
    last_ts = time.time() - POLL_INTERVAL
    billed  = set()   # dedup: trace IDs billed in this session

    log.info("Langfuse poller started (interval=%ds url=%s)", POLL_INTERVAL, LANGFUSE_URL)

    while True:
        time.sleep(POLL_INTERVAL)
        try:
            since = datetime.fromtimestamp(last_ts, tz=timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%S.000Z"
            )
            page, total_fetched = 1, 0

            while True:
                data     = fetch_traces_since(since, page)
                traces   = data.get("data", [])
                meta     = data.get("meta", {})
                total_fetched += len(traces)

                for t in traces:
                    tid = t.get("id")
                    if tid in billed:
                        continue
                    # Fetch full trace with observations for token counts
                    try:
                        full = fetch_trace_with_observations(tid)
                        process_trace(full)
                        billed.add(tid)
                    except Exception as e:
                        log.error("failed to fetch trace %s: %s", tid, e)

                # Paginate until exhausted
                if page >= meta.get("totalPages", 1):
                    break
                page += 1

            if total_fetched:
                log.info("poller: processed %d new traces since %s", total_fetched, since)

            last_ts = time.time()

        except Exception as e:
            log.error("Langfuse poll error: %s", e)
            # Don't advance last_ts — retry same window next cycle


# ── Webhook receiver ──────────────────────────────────────────────────────────

class BridgeHandler(BaseHTTPRequestHandler):
    """HTTP handler for Langfuse Cloud webhooks (optional — OSS uses poller)."""

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body   = self.rfile.read(length)
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            self.send_response(400)
            self.end_headers()
            return

        event_type = payload.get("type", payload.get("event", ""))

        if event_type in ("trace.created", "trace.updated", "trace"):
            process_trace(payload.get("data", payload))
        elif event_type == "batch":
            for item in payload.get("batch", []):
                if item.get("type", "") in ("trace.created", "trace.updated"):
                    process_trace(item.get("data", item))

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'{"status":"ok"}')

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'{"status":"healthy","service":"billing-bridge"}')

    def log_message(self, *args):
        pass


# ── Entrypoint ────────────────────────────────────────────────────────────────

def main():
    port = int(os.environ.get("BRIDGE_PORT", "8090"))

    # Start Langfuse poller in background thread
    t = threading.Thread(target=poll_langfuse, daemon=True)
    t.start()

    log.info(
        "Billing Bridge on :%d  Lago=%s  key_set=%s  Langfuse=%s  poll=%ds",
        port, LAGO_API_URL, bool(LAGO_API_KEY), LANGFUSE_URL, POLL_INTERVAL,
    )
    HTTPServer(("0.0.0.0", port), BridgeHandler).serve_forever()


if __name__ == "__main__":
    main()
