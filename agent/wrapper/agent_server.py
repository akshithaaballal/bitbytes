import sys
import os
import json
import uuid
import time
import threading
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# Add agent root to sys.path so we can import Bot
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
AGENT_DIR = os.path.dirname(CURRENT_DIR)
if AGENT_DIR not in sys.path:
    sys.path.insert(0, AGENT_DIR)

import Bot

HOST = "127.0.0.1"
PORT = 5000

requests = {}

def json_response(handler, status, data):
    body = json.dumps(data).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


class RealCosmitudeAgentHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path == "/health":
            is_connected = bool(Bot.Sessionid)
            return json_response(
                self,
                200,
                {
                    "ok": True,
                    "bridgeConnected": is_connected,
                    "agent": "cosmitude",
                    "forumID": getattr(Bot, "forumID", None)
                },
            )

        if self.path.startswith("/requests/"):
            request_id = self.path.split("/")[-1]
            req = requests.get(request_id)

            if not req:
                return json_response(
                    self,
                    404,
                    {"error": "Request not found"},
                )

            return json_response(self, 200, req)

        return json_response(
            self,
            404,
            {"error": "Not found"},
        )

    def do_POST(self):
        if self.path != "/requests":
            return json_response(
                self,
                404,
                {"error": "Not found"},
            )

        try:
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length)
            data = json.loads(raw.decode("utf-8"))

            request_id = data.get("id") or str(uuid.uuid4())
            flow_type = data.get("type", "BitBytesData_DataProcessing")
            message = data.get("message", "")

            # Send real Bridge to Cosmitude
            bridge_res = Bot.sendUserRequestBridge(flow_type, message)

            if bridge_res.get("success"):
                bridge_id = bridge_res.get("bridgeId")
                flow_used = bridge_res.get("flow")
                requests[request_id] = {
                    "status": "completed",
                    "output": (
                        f"Bridge Sent to Cosmitude!\n"
                        f"• Bridge ID: {bridge_id}\n"
                        f"• Flow: {flow_used}\n"
                        f"• Forum: BitBytesData ({Bot.forumID})\n"
                        f"• Payload: {message}"
                    ),
                    "error": None,
                }
            else:
                requests[request_id] = {
                    "status": "failed",
                    "output": None,
                    "error": bridge_res.get("error", "Failed to send bridge to Cosmitude"),
                }

            return json_response(
                self,
                202,
                {
                    "accepted": True,
                    "id": request_id,
                },
            )

        except Exception as exc:
            return json_response(
                self,
                400,
                {"error": str(exc)},
            )

    def log_message(self, format, *args):
        print("[Cosmitude-Wrapper]", format % args)


def initialize_cosmitude():
    print("[Cosmitude-Wrapper] Initializing Cosmitude Bridge session...")
    try:
        Bot.login()
        if Bot.Sessionid:
            print(f"[Cosmitude-Wrapper] Successfully connected to Cosmitude! Session: {Bot.Sessionid}")
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
    
    # Start background sync thread to listen for forum triggers
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