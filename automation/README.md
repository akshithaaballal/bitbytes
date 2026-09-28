# 🚀 BitBytes Daily Multi-Channel Automation for B.Tech Students

This module automates the generation and distribution of daily bite-sized Computer Science & Engineering concepts across **Telegram** and **GitHub**.

---

## 📁 Project Structure

```
automation/
├── assets/
│   └── fonts/                  # Bundled DejaVu Sans, Bold, and Mono TTF fonts
├── content_bank/               # Rotational curriculum (JSON templates for fallback)
│   ├── day_01_two_pointers.json          (Monday: DSA Bite)
│   ├── day_02_system_design_caching.json (Tuesday: System Design 101)
│   ├── day_03_os_process_vs_thread.json  (Wednesday: Operating Systems)
│   ├── day_04_git_cherry_pick.json       (Thursday: Developer Tools & Git)
│   ├── day_05_tcp_vs_udp.json            (Friday: Computer Networks)
│   ├── day_06_sql_indexes.json           (Saturday: Database Engineering)
│   └── day_07_interview_puzzle.json      (Sunday: Logic & Placement Challenge)
│
├── crawlers/                   # Live web discovery & research engines
│   └── tech_radar.py           # Multi-tiered scraping (Search/HN -> RSS -> arXiv)
│
├── publishers/
│   ├── telegram_publisher.py   # sendPhoto card delivery + HTML Telegram message
│   ├── git_publisher.py        # Generates Markdown files & INDEX.md archive
│   ├── image_generator.py      # Pillow engine generating 1080x1080 PNG social cards
│   └── bridge_reporter.py      # Structured telemetry to Cosmitude Bridge
│
├── main.py                     # Central orchestrator & rotation controller
├── history.json                # Records posted history to prevent duplicates
├── sources.json                # Allowlisted trusted engineering RSS & Atom feeds
├── requirements.txt            # Production Python dependencies
├── requirements-dev.txt        # Development & test dependencies
├── .env.example                # Sample API keys template
└── INDEX.md                    # Generated public knowledge-base table
```

---

## ⚡ Quick Start: Local Testing

### 1. Install Dependencies
```bash
pip install -r automation/requirements.txt -r automation/requirements-dev.txt
```

### 2. Test in Dry-Run Mode (No API keys needed)
Simulates live tiered discovery (with direct HTTP fallback), PNG social card rendering, and Markdown archiving without making live external broadcasts:
```bash
python automation/main.py --dry-run
```

To test a specific day's topic:
```bash
python automation/main.py --dry-run --post day_01
```

To run unit tests:
```bash
pytest automation/tests/
```

Check the generated 1080x1080 PNG social card in `automation/generated_images/`!

---

## 🔑 Setting Up Channels

### Channel 1: Telegram (Recommended — 2 Minutes Setup)
1. Open Telegram and search for `@BotFather`.
2. Send `/newbot`, follow prompts, and copy your `BOT_TOKEN`.
3. Create your public or private channel for students (e.g. `@BitBytesDaily`).
4. Add your bot as an **Administrator** with permission to post messages.
5. In your `.env` or GitHub Secrets:
   ```env
   TELEGRAM_BOT_TOKEN="your_bot_token"
   TELEGRAM_CHANNEL_ID="@BitBytesDaily"
   ```
   When publishing, the pipeline first uploads the 1080x1080 PNG social card via `sendPhoto` with the concept title and track caption, then sends the comprehensive educational breakdown with code and takeaways via `sendMessage`.

### Channel 2: GitHub (Automatic Archive)
- The pipeline automatically writes daily Markdown summaries with front-matter to `automation/archive/` and updates `automation/INDEX.md`.
- In GitHub Actions, it commits the updates back to your repository with `[skip ci]`.

---

## ⏰ Automated Cloud Scheduling (GitHub Actions)

A workflow runs at `.github/workflows/daily_btech_post.yml`:
- Runs in the cloud twice daily at **03:00 UTC and 15:00 UTC**.
- Concurrency control ensures runs never overlap.
- Updates `automation/archive/`, `automation/INDEX.md`, `automation/history.json`, and `frontend/public/feed.json`.
- Uploads generated social card PNGs as workflow artifacts for inspection.
- Required GitHub Actions Secrets:
  - `TELEGRAM_BOT_TOKEN`: Telegram Bot API token from `@BotFather`.
  - `TELEGRAM_CHANNEL_ID`: Channel username (e.g. `@csbites`).
  - `FIRECRAWL_API_KEY`: API key for web discovery (optional; falls back to direct HTTP).
  - `GEMINI_API_KEY`: Google Gemini API key for educational curation.
  - `GEMINI_MODEL`: (Optional) Primary model (default: `gemini-flash-lite-latest`).
