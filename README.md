# BitBytes

Frontend (React + Vite) → Middleware (Express) → Cosmitude Agent (Python) → Cosmitude Bridge

The browser only ever talks to the middleware. All agent-specific code lives in
`middleware/src/agentAdapter.js`.

## Status of the Cosmitude Agent integration

The generated agent is a polling client: it has no port and no endpoint. The adapter is written
against a **proposed local wrapper contract** (below), which still has to be built around the agent.
Until then, `/api/health` reports the agent as "not configured" and requests return HTTP 503.

Proposed wrapper contract (our design, not a Cosmitude API):

| Call | Purpose |
|---|---|
| `GET  {AGENT_URL}/health` → `{ "ok": true, "bridgeConnected": true }` | agent + bridge status |
| `POST {AGENT_URL}/requests` with `{ id, type, message }` → 2xx | hand a request to the agent |
| `GET  {AGENT_URL}/requests/{id}` → `{ "status": "pending"\|"completed"\|"failed", "output": ..., "error": "..." }` | poll for the Bridge reply |

Every call sends the header `X-Agent-Key: <AGENT_API_KEY>` when that variable is set.

## 1. Install dependencies

```bash
cd middleware && npm install
cd ../frontend && npm install
```

Requires Node.js 18 or newer.

## 2. Configure the middleware

```bash
cd middleware
cp .env.example .env
# edit .env: set AGENT_URL (and AGENT_API_KEY if the wrapper requires one)
```

The frontend needs no secrets. Optionally set `VITE_API_BASE` in `frontend/.env` to point at a
middleware on another origin; by default the Vite dev server proxies `/api` to `http://localhost:4000`.

## 3. Start the Cosmitude Agent

```bash
pip install requests
python <your-generated-agent-file>.py
```

The generated file runs a login + 10-second sync loop and listens on no port. Start the wrapper
instead once it exists (not built yet).

## 4. Start the middleware

```bash
cd middleware
npm run dev
```

## 5. Start the frontend

```bash
cd frontend
npm run dev
```

Open http://localhost:5173.

## 6. Test

```bash
curl http://localhost:4000/api/health

curl -X POST http://localhost:4000/api/request \
  -H "Content-Type: application/json" \
  -d '{"type":"general","message":"Hello from curl"}'

curl http://localhost:4000/api/requests
```

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| "Cannot reach the BitBytes middleware" | Middleware not running, or not on port 4000. |
| "Cosmitude Agent adapter is not configured yet" (503) | `AGENT_URL` is empty in `middleware/.env`. |
| "Cosmitude Agent is unavailable." (503) | Nothing is listening at `AGENT_URL`, or the URL/port is wrong. |
| "Cosmitude Agent timed out." (504) | Agent is up but slow; raise `AGENT_TIMEOUT_MS`. |
| "Cosmitude Agent returned an error" (502) | Agent answered with a non-2xx status; check the agent's own logs. |
| CORS error in the browser console | Frontend origin is not in `FRONTEND_ORIGIN`. |
| Request stays "Waiting" then fails with "timed out" | Bridge never replied within `REQUEST_TIMEOUT_MS`. |

## Security notes

- Keep `middleware/.env` out of git (already in `.gitignore`).
- The generated agent contains hardcoded credentials. Do not commit it, and move them to environment variables when you build the wrapper.
- The frontend cannot choose the agent URL or path; both are fixed server-side.
