"""
AgentNext Billing Bridge — ObserveLLM → Billing Metering

Receives trace webhooks from ObserveLLM (Langfuse), extracts usage metrics,
and sends billing events to Billing (Lago) API.

Meters three billable metrics:
  - llm_tokens: total tokens (input + output) per trace
  - api_calls: 1 per trace (each workflow execution)
  - workflow_runs: 1 per unique workflow run
"""

import os
import json
import logging
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.request import Request, urlopen
from urllib.error import URLError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)
log = logging.getLogger("billing-bridge")

LAGO_API_URL = os.environ.get("LAGO_API_URL", "http://billing-api:3000")
LAGO_API_KEY = os.environ.get("LAGO_API_KEY", "")


def send_event(tid, sub, code, val, props=None):
    """Send a usage event to Billing (Lago) API."""
    if not LAGO_API_KEY:
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
        log.info("sent %s=%s for %s", code, val, sub)
    except URLError as e:
        log.error("failed %s: %s", code, e)


def process_trace(trace):
    """Extract usage from a trace and send billing events."""
    tid = trace.get("id", "unknown")
    uid = trace.get("userId", "default")
    wf = trace.get("name", "unknown")
    observations = trace.get("observations", [])

    tokens = sum(
        (o.get("usage", {}).get("input", 0) or 0)
        + (o.get("usage", {}).get("output", 0) or 0)
        for o in observations
    )

    if tokens > 0:
        send_event(f"{tid}-tok", uid, "llm_tokens", tokens, {"workflow": wf})
    send_event(f"{tid}-api", uid, "api_calls", 1, {"workflow": wf})
    send_event(
        f"{tid}-wf", uid, "workflow_runs", 1,
        {"workflow": wf, "tokens": str(tokens)}
    )


class BridgeHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
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
        self.wfile.write(b'{"status":"healthy"}')

    def log_message(self, *args):
        pass


def main():
    port = int(os.environ.get("BRIDGE_PORT", "8090"))
    log.info("AgentNext Billing Bridge on port %d", port)
    log.info("Billing API: %s", LAGO_API_URL)
    HTTPServer(("0.0.0.0", port), BridgeHandler).serve_forever()


if __name__ == "__main__":
    main()
