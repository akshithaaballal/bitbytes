# 🚀 BitBytes Daily Multi-Channel Automation for B.Tech Students

This module automates the generation and distribution of daily bite-sized Computer Science & Engineering concepts across **Telegram**, **GitHub**, and **Instagram**.

---

## 📁 Project Structure

```
automation/
├── content_bank/           # 7-day rotational curriculum (JSON templates)
│   ├── day_01_two_pointers.json          (Monday: DSA Bite)
│   ├── day_02_system_design_caching.json (Tuesday: System Design 101)
│   ├── day_03_os_process_vs_thread.json  (Wednesday: Operating Systems)
│   ├── day_04_git_cherry_pick.json       (Thursday: Developer Tools & Git)
│   ├── day_05_tcp_vs_udp.json            (Friday: Computer Networks)
│   ├── day_06_sql_indexes.json           (Saturday: Database Engineering)
│   └── day_07_interview_puzzle.json      (Sunday: Logic & Placement Challenge)
│
├── publishers/
│   ├── telegram_publisher.py   # HTML-formatted Telegram messages & code blocks
│   ├── git_publisher.py        # Generates Markdown files & INDEX.md archive
│   ├── image_generator.py      # Pillow engine generating 1080x1080 social cards
│   └── instagram_publisher.py  # Meta Graph API container publisher
│
├── main.py                 # Central orchestrator & rotation controller
├── history.json            # Records posted history to prevent duplicates
├── requirements.txt        # Python dependencies
├── .env.example            # Sample API keys template
└── INDEX.md                # Generated public knowledge-base table
```

---

## ⚡ Quick Start: Local Testing

### 1. Install Dependencies
```bash
pip install -r automation/requirements.txt
```

### 2. Test in Dry-Run Mode (No API keys needed)
Simulates image generation and Markdown archiving without making live network requests:
```bash
python automation/main.py --dry-run
```

To test a specific day's topic:
```bash
python automation/main.py --dry-run --post day_01
```

Check the generated 1080x1080 card in `automation/generated_images/day_01.png` and the generated markdown in `automation/archive/`!

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

### Channel 2: GitHub (Automatic Archive)
- The pipeline automatically writes daily Markdown summaries to `automation/archive/` and updates `automation/INDEX.md`.
- In GitHub Actions, it commits the updates back to your repository with `[skip ci]`.

### Channel 3: Instagram (Optional)
- Requires an Instagram Professional account linked to a Facebook Page.
- Generate an Access Token with `instagram_content_publish` scope from the [Meta Developer Portal](https://developers.facebook.com/).
- Set `INSTAGRAM_ACCESS_TOKEN` and `INSTAGRAM_ACCOUNT_ID`.

---

## ⏰ Automated Cloud Scheduling (GitHub Actions)

A workflow is ready at `.github/workflows/daily_btech_post.yml`:
- Runs completely free in the cloud every day at **08:00 AM IST** (`02:30 UTC`).
- Simply add your `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHANNEL_ID` to your GitHub Repository under **Settings > Secrets and variables > Actions**.
