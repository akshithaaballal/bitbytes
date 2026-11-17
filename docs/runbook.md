# BitBytes Production Runbook

This runbook documents operational procedures for diagnosing, recovering, and maintaining the BitBytes automated daily publishing pipeline and Cosmitude Bridge integration.

---

## 1. Daily Workflow Architecture

The publishing pipeline is driven by GitHub Actions:
- **Twice-Daily Workflow (`.github/workflows/daily_btech_post.yml`)**:
  - Scheduled at `03:00 UTC` and `15:00 UTC` (~8:30 AM & 8:30 PM IST).
  - Gathers live candidate stories across 3 tiers (Firecrawl/HN, RSS feeds, arXiv).
  - Grounds candidate lessons through LLM curation (Gemini / OpenAI fallback).
  - Enforces the strict grounding gate (quote verification, `ast.parse` syntax checks, token Jaccard title dedup, relevance >= 0.70).
  - Publishes to Telegram channel (`@csbites`), commits the markdown note to `automation/archive/`, regenerates `frontend/public/feed.json` and `frontend/public/rss.xml`, updates `status.json`, and transmits structured telemetry to the Cosmitude Bridge.
- **Heartbeat Monitor (`.github/workflows/heartbeat.yml`)**:
  - Scheduled daily at `04:00 UTC`.
  - Asserts that the latest post in `automation/history.json` is less than 36 hours old.
  - Automatically files an issue labeled `bug`, `automated-alert` if pipeline publishing stalls.

---

## 2. Diagnosing Workflow Failures

### Scenario A: Job Exits with Code 1 at Step 5 ("Run Test Suite")
1. **Admin Schema Check**: The Cosmitude Bot test suite requires `agent/BitBytesData_BitBytesData_Admin.txt` or its bundled fallback `agent/BitBytesData_Admin_fallback.json`. If missing, verify `agent/BitBytesData_Admin_fallback.json` exists in git.
2. **Environment Secrets**: Verify `COSMITUDE_USERNAME`, `COSMITUDE_PASSWORD`, `COSMITUDE_SERVER_ID`, and `COSMITUDE_FORUM_ID` secrets are set in repository settings.
3. **Local Reproduction**:
   ```bash
   $env:COSMITUDE_USERNAME='d'; $env:COSMITUDE_PASSWORD='d'; $env:COSMITUDE_SERVER_ID='d'; $env:COSMITUDE_FORUM_ID='d'; python -m pytest automation/tests -q
   ```

### Scenario B: AI Grounding Rejections
If the workflow logs show all candidate leads were rejected:
- **Quote Verification**: The LLM hallucinated quotes or exceeded the 25-word verbatim ceiling.
- **Syntax Check**: The generated Python snippet failed `ast.parse`.
- **Relevance Score**: The returned relevance score was below `0.70`.
- **Automatic Evergreen Fallback**: The pipeline will automatically fall back to `automation/content_bank/` and publish the longest-unposted evergreen lesson.

### Scenario C: Heartbeat Alert (Stall > 36h)
1. Navigate to repository **Actions** tab.
2. Check the most recent `daily_btech_post.yml` run log for git push rebase collisions or API rate limit responses.
3. Trigger a manual dispatch:
   - Go to Actions -> Twice-Daily B.Tech Engineering Post Automation -> **Run workflow**.

---

## 3. Cosmitude Bridge Telemetry Inspection

The bridge reporter (`automation/publishers/bridge_reporter.py`) records 4 lifecycle flows:
1. `DataProcessing`: Lead harvesting statistics and tier distribution.
2. `ProcessingStages`: Scraping engine, LLM model used, and grounding validation results.
3. `CompletionTracking`: Telegram message link, Git commit SHA, and archive file path.
4. `FailureManagement`: Skipped reason, fallback reason, or exception traceback.

All telemetry messages respect the 30-second execution budget and handle transient connection failures gracefully.

---

## 4. Manual Operations Checklist

- **Trigger dry-run**:
  ```bash
  python automation/main.py --dry-run
  ```
- **Trigger single evergreen post**:
  ```bash
  python automation/main.py --evergreen --post day_01
  ```
- **Force feed and RSS regeneration**:
  ```bash
  python -c "from feed_generator import generate_feed_json; generate_feed_json()"
  ```
