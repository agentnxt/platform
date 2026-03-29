"""
AgentNext Billing Bridge — ObserveLLM → Billing Metering

Receives trace webhooks from ObserveLLM (Langfuse), extracts usage metrics,
and sends billing events to Billing (Lago) API.

Billable metrics:
  - llm_tokens      : total tokens (input + output) per trace
  - api_calls       : 1 per trace (each workflow execution)
  - workflow_runs   : 1 per unique workflow run
  - agent_runs      : 1 per AgentStudio agent execution
"""

import os
import json
import logging
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.request import Request, urlopen
from urllib.error import URLError

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("billing-bridge")

LAGO_API_URL = os.environ.get("LAGO_API_URL", "http://billing-api:3000")
LAGO_API_KEY = os.environ.get("LAGO_API_KEY", "")

# Tags that mark an AgentStudio agent run
AGENT_TAGS = {"agentstudio", "agent_run", "simstudio"}


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


def process_trace(trace):
    """Extract usage from a Langfuse trace and send billing events."""
    tid  = trace.get("id", "unknown")
    uid  = trace.get("userId", "default")
    wf   = trace.get("name", "unknown")
    tags = set(trace.get("tags") or [])
    observations = trace.get("observations", [])

    tokens = sum(
        (o.get("usage", {}).get("input", 0) or 0)
        + (o.get("usage", {}).get("output", 0) or 0)
        for o in observations
    )

    if tokens > 0:
        send_event(f"{tid}-tok", uid, "llm_tokens", tokens, {"workflow": wf})

    send_event(f"{tid}-api", uid, "api_calls", 1, {"workflow": wf})
    send_event(f"{tid}-wf",  uid, "workflow_runs", 1, {"workflow": wf, "tokens": str(tokens)})

    # AgentStudio-specific agent_run metric
    if tags & AGENT_TAGS or wf.startswith("agent"):
        send_event(f"{tid}-ar", uid, "agent_runs", 1, {"workflow": wf, "tokens": str(tokens)})
        log.info("agent_run billed trace=%s user=%s", tid, uid)


class BridgeHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
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


def main():
    port = int(os.environ.get("BRIDGE_PORT", "8090"))
    log.info("Billing Bridge on :%d  Lago=%s  key_set=%s", port, LAGO_API_URL, bool(LAGO_API_KEY))
    HTTPServer(("0.0.0.0", port), BridgeHandler).serve_forever()


if __name__ == "__main__":
    main()
