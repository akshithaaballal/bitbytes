# BitBytes

> Daily technical concepts from production systems for B.Tech CS & AI students.
> Dispatched twice daily (03:00 & 15:00 UTC) across Telegram, Git archive, and static web feed.

```
Frontend (React + Vite) ──> Public Feed (/feed.json)
         │
         ▼ (Operator Portal only)
Middleware (Express) ──> Agent Wrapper (Python) ──> Cosmitude Bridge / Automation Pipeline
```

The public site is a zero-layout-shift static web reader that consumes `frontend/public/feed.json`. It requires no running backend or secrets to serve readers. The Operator Console connects through the Express middleware and Python agent wrapper.

---

## System Architecture

1. **Automation Pipeline (`automation/`)**:
   - **Cadence:** Dispatched twice daily (03:00 and 15:00 UTC) via GitHub Actions (`.github/workflows/daily_btech_post.yml`).
   - **Discovery:** Firecrawl Search and Hacker News (Algolia single-request front page) in Tier 1, followed by trusted engineering RSS/Atom feeds in Tier 2, and arXiv in Tier 3.
   - **Source Filter:** Whitelisted engineering publications in `automation/sources.json` matched via word-boundary regex and domain matching (`host == d or host.endswith("." + d)`).
   - **Honest Mention Clustering:** Clusters candidate stories by normalized token Jaccard similarity ($\ge 0.5$). `source_count` measures distinct registrable domains over the trailing 7 days. Topics graduate to publication only after independent cross-domain validation.
   - **Grounded LLM Curator:** Uses Gemini (`gemini-flash-lite-latest` with `gemini-3-flash-preview` fallback) to distill teachable systems engineering concepts strictly grounded in fetched articles ($800+$ clean characters, up to 12,000 characters analyzed).
   - **Multi-channel Publishing:** Broadcasts high-resolution 1080x1080 PNG social cards via `sendPhoto` and complete educational lessons via `sendMessage` to Telegram ([@csbites](https://t.me/csbites)), commits YAML front-matter Markdown to `automation/archive/`, and generates `frontend/public/feed.json`.
   - **Evergreen Fallback:** If live discovery exhausts all tiers, rotates through `automation/content_bank/day_*.json` choosing the post posted longest ago or never, complete with canonical engineering references (e.g. RFC 9293).

2. **Cosmitude Bridge Telemetry & Research Reports (`automation/publishers/bridge_reporter.py`)**:
   - **Structured Reports:** Whenever the pipeline runs (whether published, skipped, or failed), a complete structured report is dispatched to Cosmitude Bridge (`BitBytesData_DataProcessing` flow).
   - **Telemetry Fields:** Each report includes the execution timestamp, topic title, curation engine, original source URL, cross-domain source count, publication statuses across Telegram and Git, skipped reason, and lesson summary.
   - **Durable Local Queue:** If Cosmitude Bridge is offline or credentials are missing, reports are persisted to `automation/bridge_queue.json` (gitignored) and automatically flushed when bridge connectivity is restored.

3. **Agent Wrapper (`agent/wrapper/agent_server.py`)**:
   - Hardened HTTP server exposing `/health`, `/requests`, and `/broadcast`. Runs on `AGENT_HOST` (`127.0.0.1`) and `AGENT_PORT` (`5001`).
   - Protects non-health routes with constant-time `hmac.compare_digest` checking against `X-Agent-Key`.
   - Rejects request payloads larger than 64 KB with HTTP 413.
   - Concurrency control: `POST /broadcast` acquires a `threading.Lock` and returns HTTP `202 Accepted` with a UUID `jobId`, or `409 Conflict` if a job is active. Thread creation errors safely release the lock.
   - Asynchronous job telemetry: Polled via `GET /broadcast/status/<jobId>` with UUID format validation.
   - Thread-safe storage: In-memory job and request stores guarded by `threading.Lock`.

4. **Middleware (`middleware/`)**:
   - Express API gateway with security headers (`X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`, `Cache-Control: no-store` on `/api/*`).
   - Fail-fast validation: Server exits immediately (`process.exit(1)`) if `OPERATOR_PASSCODE` or `OPERATOR_TOKEN_SECRET` is missing.
   - Reverse proxy support: Configurable via `TRUST_PROXY` env var (default disabled).
   - Operator login (`POST /api/operator/login`): rate-limited to 5 attempts per minute per IP (with automatic periodic memory pruning), constant-time `crypto.timingSafeEqual` passcode verification, and signs 8-hour HMAC tokens.
   - Protected routes guarded by `requireOperator` middleware.

5. **Frontend (`frontend/`)**:
   - Built with React and Vite following strict Ponytail minimalism (flat surfaces, 1px hairline borders, single accent color, no gradients or glows, self-hosted IBM Plex Sans and JetBrains Mono Latin woff2 fonts, zero external font requests).
   - Asymmetric layout: Dominant latest dispatch card and compact archive rows.
   - Note detail view at `#p/<id>` with one-click code copy, source provenance chip, and breadcrumb navigation.
   - Single `<main>` on every page, full `:focus-visible` states, and `prefers-reduced-motion` compliance.

---

## Environment Variables

### 1. Automation Pipeline (`automation/.env`)
| Variable | Description | Default / Example |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | Bot token from @BotFather | Required for live broadcast |
| `TELEGRAM_CHANNEL_ID` | Telegram channel username or ID | `@csbites` |
| `GEMINI_API_KEY` | Google Gemini API key | Required for LLM curation |
| `GEMINI_MODEL` | Primary Gemini model identifier | `gemini-flash-lite-latest` |
| `GEMINI_MODEL_FALLBACK` | Fallback Gemini model identifier | `gemini-3-flash-preview` |
| `FIRECRAWL_API_KEY` | Firecrawl scraping API key | Optional (falls back to direct HTTP) |
| `USE_AI_RADAR` | Enable autonomous live web research | `true` |
| `GENERATE_IMAGE` | Render 1080x1080 PNG social card | `true` (production default) |
| `SIMULATE_MODE` | Dry-run mode for local testing | `false` |

### 2. Agent Wrapper (`agent/.env`)
| Variable | Description | Default / Example |
|---|---|---|
| `AGENT_HOST` | Host address to bind | `127.0.0.1` |
| `AGENT_PORT` | Port for agent server | `5001` |
| `AGENT_API_KEY` | Secret key required in `X-Agent-Key` header | Set strong random secret |
| `TELEGRAM_CHANNEL` | Public channel name for Cosmitude bridge log | `@csbites` |
| `COSMITUDE_API_BASE` | Cosmitude API Base URL | `https://ca.cosmitude.com` |
| `COSMITUDE_MAC_ADDRESS` | Bridge device identifier | `Bridge-Web` |
| `COSMITUDE_USERNAME` | Cosmitude Bot UUID | Required for Cosmitude Bridge |
| `COSMITUDE_PASSWORD` | Cosmitude Bot Password | Required for Cosmitude Bridge |
| `COSMITUDE_SERVER_ID` | Cosmitude LLServer ID | Required for Cosmitude Bridge |
| `COSMITUDE_FORUM_ID` | Cosmitude Forum ID | Required for Cosmitude Bridge |

### 3. Middleware (`middleware/.env`)
| Variable | Description | Default / Example |
|---|---|---|
| `PORT` | Middleware HTTP port | `4000` |
| `AGENT_URL` | Upstream Agent URL | `http://127.0.0.1:5001` |
| `AGENT_API_KEY` | Must match `AGENT_API_KEY` in `agent/.env` | Shared secret |
| `OPERATOR_PASSCODE` | Passcode for operator console login | Required (no fallback) |
| `OPERATOR_TOKEN_SECRET` | Secret key used to sign HMAC tokens (8h) | Required (no fallback) |
| `TRUST_PROXY` | Enable reverse proxy IP resolution | `false` |
| `FRONTEND_ORIGIN` | Allowed CORS origins (comma-separated) | `http://localhost:5173` |

### 4. Frontend (`frontend/.env`)
| Variable | Description | Default / Example |
|---|---|---|
| `VITE_API_BASE` | Base URL for middleware API requests | `""` (proxied by Vite) |

---

## Local Development Quickstart

### 1. Install Dependencies
```bash
# Frontend
cd frontend && npm install

# Middleware
cd ../middleware && npm install

# Automation
cd ../automation && pip install -r requirements.txt -r requirements-dev.txt

# Agent
cd ../agent && pip install requests python-dotenv
```

### 2. Run Automation & Middleware Tests
```bash
# Automation tests
pytest automation/tests/

# Middleware auth tests
npm --prefix middleware test
```

### 3. Dry-Run the Pipeline Locally
```bash
python automation/main.py --dry-run
```

### 4. Start Local Services
- **Terminal 1 (Agent Wrapper):**
  ```bash
  cd agent/wrapper && python agent_server.py
  ```
- **Terminal 2 (Middleware):**
  ```bash
  cd middleware && npm run dev
  ```
- **Terminal 3 (Frontend):**
  ```bash
  cd frontend && npm run dev
  ```

Open [http://localhost:5173](http://localhost:5173) in your browser.

<!-- note 86 -->

<!-- note 87 -->

<!-- note 88 -->

<!-- note 89 -->

<!-- note 90 -->

<!-- note 91 -->

<!-- note 92 -->

<!-- note 93 -->

<!-- note 94 -->

<!-- note 95 -->

<!-- note 96 -->

<!-- note 97 -->

<!-- note 98 -->

<!-- note 99 -->

<!-- note 100 -->

<!-- note 101 -->

<!-- note 102 -->

<!-- note 103 -->

<!-- note 104 -->

<!-- note 109 -->

<!-- note 110 -->

<!-- note 111 -->

<!-- note 112 -->

<!-- note 113 -->

<!-- note 114 -->

<!-- note 115 -->

<!-- note 116 -->

<!-- note 117 -->

<!-- note 118 -->

<!-- note 119 -->

<!-- note 120 -->

<!-- note 121 -->

<!-- note 122 -->

<!-- note 123 -->

<!-- note 124 -->

<!-- note 125 -->

<!-- note 126 -->

<!-- note 127 -->

<!-- note 128 -->

<!-- note 129 -->

<!-- note 130 -->

<!-- note 131 -->

<!-- note 132 -->

<!-- note 133 -->

<!-- note 134 -->

<!-- note 135 -->

<!-- note 136 -->

<!-- note 137 -->

<!-- note 138 -->

<!-- note 139 -->

<!-- note 140 -->

<!-- note 141 -->

<!-- note 142 -->

<!-- note 143 -->

<!-- note 144 -->

<!-- note 145 -->

<!-- note 146 -->

<!-- note 147 -->

<!-- note 148 -->

<!-- note 154 -->

<!-- note 155 -->

<!-- note 156 -->

<!-- note 157 -->

<!-- note 158 -->

<!-- note 159 -->

<!-- note 160 -->

<!-- note 161 -->

<!-- note 162 -->

<!-- note 163 -->

<!-- note 164 -->

<!-- note 165 -->

<!-- note 166 -->

<!-- note 167 -->

<!-- note 168 -->

<!-- note 169 -->

<!-- note 170 -->

<!-- note 171 -->

<!-- note 172 -->

<!-- note 173 -->

<!-- note 174 -->

<!-- note 175 -->
