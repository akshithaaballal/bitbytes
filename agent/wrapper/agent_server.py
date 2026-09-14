import sys
import os
import json
import uuid
import time
import hmac
import threading
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# Add agent root to sys.path so we can import Bot
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
AGENT_DIR = os.path.dirname(CURRENT_DIR)
PROJECT_ROOT = os.path.dirname(AGENT_DIR)
AUTOMATION_DIR = os.path.join(PROJECT_ROOT, "automation")

if AGENT_DIR not in sys.path:
    sys.path.insert(0, AGENT_DIR)
if AUTOMATION_DIR not in sys.path:
    sys.path.insert(0, AUTOMATION_DIR)

import Bot

try:
    import main as automation_main
except Exception as e:
    print(f"[Cosmitude-Wrapper] Warning importing automation: {e}")
    automation_main = None

HOST = os.getenv("AGENT_HOST", "127.0.0.1")
PORT = int(os.getenv("AGENT_PORT", 5001))
AGENT_API_KEY = os.getenv("AGENT_API_KEY", "")

# In-memory storage bounded to max 200 items
MAX_STORE_ITEMS = 200
MAX_BODY_BYTES = 64 * 1024  # 64 KB
requests_store = {}
broadcast_jobs = {}
broadcast_lock = threading.Lock()
store_lock = threading.Lock()


def trim_dict(d: dict, max_size: int = MAX_STORE_ITEMS):
    if len(d) > max_size:
        keys_to_remove = list(d.keys())[:-max_size]
        for k in keys_to_remove:
            d.pop(k, None)


def json_response(handler, status, data):
    try:
        body = json.dumps(data).encode("utf-8")
        handler.send_response(status)
        handler.send_header("Content-Type", "application/json")
        handler.send_header("Content-Length", str(len(body)))
        handler.end_headers()
        handler.wfile.write(body)
    except (BrokenPipeError, ConnectionResetError):
        pass


def verify_agent_key(handler) -> bool:
    """Verifies X-Agent-Key header using constant-time comparison."""
    if not AGENT_API_KEY:
        # If no key set in env, reject for security
        return False
    provided = handler.headers.get("X-Agent-Key", "")
    return hmac.compare_digest(provided.encode("utf-8"), AGENT_API_KEY.encode("utf-8"))


class RealCosmitudeAgentHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        # Health check is open
        if self.path == "/health":
            is_connected = bool(Bot.Sessionid)
            return json_response(
                self,
                200,
                {
                    "ok": True,
                    "bridgeConnected": is_connected,
                    "agent": "cosmitude"
                },
            )

        # All other routes require X-Agent-Key
        if not verify_agent_key(self):
            return json_response(self, 401, {"error": "Unauthorized: Invalid or missing X-Agent-Key"})

        if self.path == "/broadcast/next":
            if not automation_main:
                return json_response(self, 500, {"error": "Automation engine not loaded"})
            try:
                next_post = automation_main.get_next_post_summary()
                return json_response(self, 200, {"ok": True, "next": next_post})
            except Exception as err:
                return json_response(self, 500, {"error": str(err)})

        if self.path == "/broadcast/history":
            if not automation_main:
                return json_response(self, 500, {"error": "Automation engine not loaded"})
            try:
                base_dir = os.path.dirname(os.path.abspath(automation_main.__file__))
                history_path = os.path.join(base_dir, "history.json")
                history = automation_main.load_history(history_path)
                return json_response(self, 200, {"ok": True, "history": list(reversed(history))})
            except Exception as err:
                return json_response(self, 500, {"error": str(err)})

        # Status check for broadcast job: GET /broadcast/status/<jobId>
        if self.path.startswith("/broadcast/status/"):
            job_id = self.path.split("/broadcast/status/")[-1].strip()
            try:
                uuid.UUID(job_id)
            except (ValueError, AttributeError):
                return json_response(self, 400, {"error": "Invalid job ID: must be a valid UUID"})

            with store_lock:
                job = broadcast_jobs.get(job_id)
                if not job:
                    return json_response(self, 404, {"error": "Job not found"})
                return json_response(self, 200, {
                    "jobId": job_id,
                    "stage": job.get("stage", "crawling"),
                    "result": job.get("result"),
                    "error": job.get("error")
                })

        if self.path.startswith("/requests/"):
            request_id = self.path.split("/")[-1]
            with store_lock:
                req = requests_store.get(request_id)
            if not req:
                return json_response(self, 404, {"error": "Request not found"})
            return json_response(self, 200, req)

        return json_response(self, 404, {"error": "Not found"})

    def do_POST(self):
        # All POST routes require X-Agent-Key
        if not verify_agent_key(self):
            return json_response(self, 401, {"error": "Unauthorized: Invalid or missing X-Agent-Key"})

        # Enforce 64 KB limit on POST request Content-Length
        try:
            content_length = int(self.headers.get("Content-Length", 0))
        except (ValueError, TypeError):
            content_length = 0

        if content_length > MAX_BODY_BYTES:
            return json_response(self, 413, {"error": "Payload Too Large: Content-Length exceeds 64KB"})

        if self.path == "/broadcast":
            if not automation_main:
                return json_response(self, 500, {"error": "Automation engine not loaded"})

            dry_run = False
            if content_length > 0:
                try:
                    raw = self.rfile.read(content_length)
                    data = json.loads(raw.decode("utf-8"))
                    dry_run = bool(data.get("dry_run", False))
                except Exception:
                    pass

            # Concurrency check under threading.Lock
            acquired = broadcast_lock.acquire(blocking=False)
            if not acquired:
                return json_response(self, 409, {"error": "A broadcast job is currently active"})

            job_id = str(uuid.uuid4())
            with store_lock:
                broadcast_jobs[job_id] = {
                    "stage": "crawling",
                    "result": None,
                    "error": None,
                    "created_at": time.time()
                }
                trim_dict(broadcast_jobs, MAX_STORE_ITEMS)

            def run_job(jid, is_dry):
                try:
                    def progress_cb(stg):
                        with store_lock:
                            if jid in broadcast_jobs:
                                broadcast_jobs[jid]["stage"] = stg

                    res = automation_main.run_pipeline(dry_run=is_dry, progress_callback=progress_cb)
                    with store_lock:
                        if jid in broadcast_jobs:
                            if res.get("skipped"):
                                broadcast_jobs[jid]["stage"] = "skipped"
                                broadcast_jobs[jid]["result"] = res
                            elif res.get("success"):
                                broadcast_jobs[jid]["stage"] = "done"
                                broadcast_jobs[jid]["result"] = res
                            else:
                                broadcast_jobs[jid]["stage"] = "failed"
                                broadcast_jobs[jid]["error"] = res.get("error", "Broadcast failed")
                except Exception as exc:
                    with store_lock:
                        if jid in broadcast_jobs:
                            broadcast_jobs[jid]["stage"] = "failed"
                            broadcast_jobs[jid]["error"] = str(exc)
                finally:
                    broadcast_lock.release()

            thread_started = False
            try:
                worker = threading.Thread(target=run_job, args=(job_id, dry_run), daemon=True)
                worker.start()
                thread_started = True
            finally:
                if not thread_started:
                    broadcast_lock.release()

            return json_response(self, 202, {"jobId": job_id, "status": "crawling"})

        if self.path != "/requests":
            return json_response(self, 404, {"error": "Not found"})

        try:
            raw = self.rfile.read(content_length) if content_length > 0 else b"{}"
            data = json.loads(raw.decode("utf-8"))

            request_id = data.get("id") or str(uuid.uuid4())
            flow_type = data.get("type", "BitBytesData_DataProcessing")
            message = data.get("message", "")

            # Send real Bridge to Cosmitude
            bridge_res = Bot.sendUserRequestBridge(flow_type, message)

            with store_lock:
                if bridge_res.get("success"):
                    bridge_id = bridge_res.get("bridgeId")
                    flow_used = bridge_res.get("flow")
                    requests_store[request_id] = {
                        "status": "completed",
                        "output": (
                            f"Bridge Sent to Cosmitude!\n"
                            f"• Bridge ID: {bridge_id}\n"
                            f"• Flow: {flow_used}\n"
                            f"• Forum: BitBytesData\n"
                            f"• Payload: {message}"
                        ),
                        "error": None,
                    }
                else:
                    requests_store[request_id] = {
                        "status": "failed",
                        "output": None,
                        "error": bridge_res.get("error", "Failed to send bridge to Cosmitude"),
                    }
                trim_dict(requests_store, MAX_STORE_ITEMS)

            return json_response(
                self,
                202,
                {
                    "accepted": True,
                    "id": request_id,
                },
            )

        except Exception as exc:
            return json_response(self, 400, {"error": str(exc)})

    def log_message(self, format, *args):
        # Minimal logging without session ID
        print("[Cosmitude-Wrapper]", format % args)


def initialize_cosmitude():
    print("[Cosmitude-Wrapper] Initializing Cosmitude Bridge session...")
    try:
        Bot.login()
        if Bot.Sessionid:
            # Stopped logging session ID for security
            print("[Cosmitude-Wrapper] Successfully connected to Cosmitude.")
        else:
            print("[Cosmitude-Wrapper] Warning: Session ID empty after login.")
    except Exception as exc:
        print(f"[Cosmitude-Wrapper] Login error: {exc}")


def sync_loop():
    print("[Cosmitude-Wrapper] Starting background forum sync listener...")
    while True:
        try:
            if Bot.Sessionid:
                Bot.clienntSync()
        except Exception as e:
            print(f"[Cosmitude-Wrapper] Background sync error: {e}")
        time.sleep(10)


if __name__ == "__main__":
    initialize_cosmitude()

    sync_thread = threading.Thread(target=sync_loop, daemon=True)
    sync_thread.start()

    print(f"Cosmitude Real Agent Wrapper running on http://{HOST}:{PORT}")

    server = ThreadingHTTPServer(
        (HOST, PORT),
        RealCosmitudeAgentHandler,
    )

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nAgent server stopped.")
        server.server_close()
