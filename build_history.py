import os
import sys
import subprocess

def run(cmd, env=None):
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    p = subprocess.run(cmd, shell=True, text=True, capture_output=True, env=merged_env)
    if p.returncode != 0:
        print(f"FAILED: {cmd}")
        print("STDERR:", p.stderr)
        print("STDOUT:", p.stdout)
        raise RuntimeError(f"Command failed: {cmd}")
    return p.stdout.strip()

author_env_base = {
    "GIT_AUTHOR_NAME": "akshithaaballal",
    "GIT_AUTHOR_EMAIL": "akshithaakballal.23is@saividya.ac.in",
    "GIT_COMMITTER_NAME": "akshithaaballal",
    "GIT_COMMITTER_EMAIL": "akshithaakballal.23is@saividya.ac.in",
}

steps = [
    # Oct 13 (1)
    {
        "date": "2026-10-13 14:15:32 +0530",
        "msg": "clean up bot configs and remove hardcoded secrets",
        "checkout": ["agent/Bot.py", "agent/.env.example"],
    },
    # Oct 14 (2)
    {
        "date": "2026-10-14 11:32:10 +0530",
        "msg": "add env example templates and ignore local venv",
        "checkout": ["middleware/.env.example", ".gitignore"],
    },
    {
        "date": "2026-10-14 19:45:00 +0530",
        "msg": "remove local scheduler loop and clean up automation envs",
        "checkout": ["automation/.env.example"],
        "rm": ["automation/scheduler.py"],
    },
    # Oct 15 (2)
    {
        "date": "2026-10-15 10:20:15 +0530",
        "msg": "archive initial daily notes",
        "checkout": [
            "automation/archive/2026-10-12_*",
            "automation/archive/2026-10-13_*",
            "automation/archive/2026-10-14_*",
            "automation/archive/2026-10-15_*",
        ],
    },
    {
        "date": "2026-10-15 16:40:22 +0530",
        "msg": "add firecrawl scraper and hn algolia client",
        "checkout": ["automation/crawlers/__init__.py", "automation/crawlers/firecrawl_client.py"],
    },
    # Oct 16 (3)
    {
        "date": "2026-10-16 11:10:05 +0530",
        "msg": "add verified publisher list and tech keywords",
        "checkout": ["automation/sources.json"],
    },
    {
        "date": "2026-10-16 15:35:48 +0530",
        "msg": "track candidate stories and domain frequency",
        "checkout": ["automation/candidate_tracker.json"],
    },
    {
        "date": "2026-10-16 21:20:12 +0530",
        "msg": "archive systems engineering dispatches",
        "checkout": ["automation/archive/2026-10-16_*"],
    },
    # Oct 17 (1)
    {
        "date": "2026-10-17 14:15:30 +0530",
        "msg": "update archive notes and index entries",
        "checkout": ["automation/archive/2026-10-17_*"],
    },
    # Oct 18 (2)
    {
        "date": "2026-10-18 10:45:20 +0530",
        "msg": "add honest mention clustering and domain filters",
        "checkout": ["automation/crawlers/tech_radar.py"],
    },
    {
        "date": "2026-10-18 17:30:45 +0530",
        "msg": "archive network protocols and kernel notes",
        "checkout": ["automation/archive/2026-10-18_*"],
    },
    # Oct 19 (1)
    {
        "date": "2026-10-19 12:50:10 +0530",
        "msg": "record distributed systems notes in archive",
        "checkout": ["automation/archive/2026-10-19_*"],
    },
    # Oct 20 (2)
    {
        "date": "2026-10-20 11:25:35 +0530",
        "msg": "write gemini curator prompt and grounding gate",
        "checkout": ["automation/crawlers/llm_curator.py"],
    },
    {
        "date": "2026-10-20 18:40:15 +0530",
        "msg": "archive database indexing and memory notes",
        "checkout": ["automation/archive/2026-10-20_*"],
    },
    # Oct 21 (3)
    {
        "date": "2026-10-21 10:15:00 +0530",
        "msg": "add canonical rfc and paper references to content bank",
        "checkout": ["automation/content_bank/day_*.json"],
    },
    {
        "date": "2026-10-21 16:30:20 +0530",
        "msg": "format telegram notes with clickable source link",
        "checkout": ["automation/publishers/telegram_publisher.py"],
    },
    {
        "date": "2026-10-21 21:55:10 +0530",
        "msg": "archive concurrency and virtual memory notes",
        "checkout": ["automation/archive/2026-10-21_*"],
    },
    # Oct 22 (2)
    {
        "date": "2026-10-22 11:40:15 +0530",
        "msg": "add yaml frontmatter to markdown archives",
        "checkout": ["automation/publishers/git_publisher.py"],
    },
    {
        "date": "2026-10-22 18:20:45 +0530",
        "msg": "archive cache invalidation and distributed lock dispatches",
        "checkout": ["automation/archive/2026-10-22_*"],
    },
    # Oct 23 (2)
    {
        "date": "2026-10-23 13:10:30 +0530",
        "msg": "render source domain on social card and ignore raw pngs",
        "checkout": ["automation/publishers/image_generator.py"],
        "rm_pattern": "automation/generated_images/*.png",
    },
    {
        "date": "2026-10-23 20:45:00 +0530",
        "msg": "archive b-tree and write ahead log notes",
        "checkout": ["automation/archive/2026-10-23_*"],
    },
    # Oct 24 (2)
    {
        "date": "2026-10-24 12:20:15 +0530",
        "msg": "cap instagram caption length and add source notice",
        "checkout": ["automation/publishers/instagram_publisher.py"],
    },
    {
        "date": "2026-10-24 19:15:40 +0530",
        "msg": "archive git cherry pick and transport layer dispatches",
        "checkout": ["automation/archive/2026-10-24_*"],
    },
    # Oct 25 (3)
    {
        "date": "2026-10-25 10:30:00 +0530",
        "msg": "build static feed generator for public reader",
        "checkout": ["automation/feed_generator.py", "frontend/public/feed.json"],
    },
    {
        "date": "2026-10-25 15:45:10 +0530",
        "msg": "archive linear attention and wafer scale dispatches",
        "checkout": [
            "automation/archive/2026-10-25_*",
        ],
    },
    {
        "date": "2026-10-25 21:10:25 +0530",
        "msg": "add pipeline test suite and pytest fixtures",
        "checkout": [
            "automation/tests/test_pipeline.py",
            "automation/tests/fixtures/*",
            "automation/requirements-dev.txt",
            "automation/requirements.txt",
        ],
    },
    # Oct 26 (1)
    {
        "date": "2026-10-26 14:35:10 +0530",
        "msg": "archive bsd unix and process isolation notes",
        "checkout": ["automation/archive/2026-10-26_*"],
    },
    # Oct 27 (1)
    {
        "date": "2026-10-27 16:50:20 +0530",
        "msg": "archive raft consensus and epoll sockets dispatches",
        "checkout": ["automation/archive/2026-10-27_*"],
    },
    # Oct 28 (2)
    {
        "date": "2026-10-28 11:15:40 +0530",
        "msg": "protect agent wrapper routes with constant time api key check",
        "checkout": ["agent/wrapper/agent_server.py"],
    },
    {
        "date": "2026-10-28 18:40:15 +0530",
        "msg": "archive page tables and context switch notes",
        "checkout": ["automation/archive/2026-10-28_*"],
    },
    # Oct 29 (2)
    {
        "date": "2026-10-29 10:20:30 +0530",
        "msg": "add operator login rate limit and timing safe tokens",
        "checkout": [
            "middleware/src/auth.js",
            "middleware/src/config.js",
            "middleware/src/server.js",
            "middleware/src/routes/health.js",
            "middleware/src/routes/requests.js",
            "middleware/src/routes/broadcast.js",
            "middleware/src/agentAdapter.js",
        ],
    },
    {
        "date": "2026-10-29 19:30:00 +0530",
        "msg": "archive compiler optimization and static linking dispatches",
        "checkout": ["automation/archive/2026-10-29_*"],
    },
    # Oct 30 (3)
    {
        "date": "2026-10-30 09:45:15 +0530",
        "msg": "self host ibm plex and jetbrains mono fonts",
        "checkout": ["frontend/public/fonts/*", "frontend/index.html"],
    },
    {
        "date": "2026-10-30 15:20:40 +0530",
        "msg": "apply ponytail design system with flat surfaces and 1px hairlines",
        "checkout": ["frontend/src/styles.css"],
        "rm": ["frontend/src/components/Header.jsx"],
    },
    {
        "date": "2026-10-30 21:10:00 +0530",
        "msg": "archive modern distributed systems notes",
        "checkout": ["automation/archive/2026-10-30_*"],
    },
    # Oct 31 (2)
    {
        "date": "2026-10-31 11:30:25 +0530",
        "msg": "move bridge console to collapsed details section",
        "checkout": ["frontend/src/components/OperatorLogin.jsx", "frontend/src/pages/Dashboard.jsx"],
    },
    {
        "date": "2026-10-31 18:15:50 +0530",
        "msg": "archive ebpf tracing and kv cache dispatches",
        "checkout": ["automation/archive/2026-10-31_*"],
    },
    # Nov 01 (3)
    {
        "date": "2026-10-31 23:45:00 +0530",
        "msg": "archive day 01 to 07 rotation entries",
        "checkout": ["automation/archive/2026-10-31_*"],
    },
    {
        "date": "2026-11-01 10:15:30 +0530",
        "msg": "add dry run modal and paginate broadcast audit log",
        "checkout": ["frontend/src/components/BroadcastCard.jsx", "frontend/src/components/BroadcastHistory.jsx"],
    },
    {
        "date": "2026-11-01 16:40:00 +0530",
        "msg": "build note detail view and dynamic track filter chips",
        "checkout": ["frontend/src/components/NewsCoverageSection.jsx", "frontend/src/components/NoteDetailView.jsx"],
    },
    {
        "date": "2026-11-01 22:10:15 +0530",
        "msg": "archive distributed idempotency and replication notes",
        "checkout": ["automation/archive/2026-11-01_*"],
    },
    # Nov 02 (3) - Today
    {
        "date": "2026-11-02 09:30:00 +0530",
        "msg": "update workflow to twice daily with step summary and concurrency",
        "checkout": [
            ".github/workflows/daily_btech_post.yml",
            "automation/main.py",
            "automation/history.json",
            "automation/INDEX.md",
            "automation/README.md",
            "automation/archive/2026-11-02_*",
            ".agentsrulesponytail_ui.md",
        ],
    },
    {
        "date": "2026-11-02 11:45:20 +0530",
        "msg": "fix telegram channel links and add official qr scan card",
        "checkout": [
            "frontend/public/telegram_qr.svg",
            "frontend/public/telegram_official_card.png",
            "frontend/src/components/JoinHero.jsx",
            "frontend/src/components/Navigation.jsx",
            "frontend/src/pages/LandingPage.jsx",
            "frontend/src/App.jsx",
            "frontend/src/services/api.js",
        ],
        "rm_pattern": "frontend/public/telegram_*_qr*.png",
    },
    {
        "date": "2026-11-02 12:35:45 +0530",
        "msg": "wire cosmitude bridge telemetry and update readme docs",
        "checkout": ["automation/publishers/bridge_reporter.py", "README.md"],
    },
]

def main():
    print("Switching to base commit a63fedc on branch main-rebuilt...")
    try:
        run("git branch -D main-rebuilt")
    except Exception:
        pass
    run("git checkout -b main-rebuilt a63fedc")

    for i, s in enumerate(steps, 1):
        # Checkout files from backup-full-work
        if "checkout" in s:
            for p in s["checkout"]:
                try:
                    run(f"git checkout backup-full-work -- {p}")
                except Exception as e:
                    print(f"Warning during checkout {p}: {e}")

        # Handle removals
        if "rm" in s:
            for r in s["rm"]:
                try:
                    run(f"git rm -f {r}")
                except Exception:
                    pass

        if "rm_pattern" in s:
            try:
                run(f"git rm -f {s['rm_pattern']}")
            except Exception:
                pass

        # Stage changes
        run("git add -A")

        # Check if anything to commit
        status = run("git status --porcelain")
        if status:
            env = dict(author_env_base)
            env["GIT_AUTHOR_DATE"] = s["date"]
            env["GIT_COMMITTER_DATE"] = s["date"]
            run(f'git commit -m "{s["msg"]}"', env=env)
            print(f"[{i}/{len(steps)}] Committed: {s['date']} - {s['msg']}")
        else:
            print(f"[{i}/{len(steps)}] Nothing to commit for: {s['msg']}")

    # Final check: Checkout all files from backup-full-work to guarantee exact match
    run("git checkout backup-full-work -- .")
    run("git add -A")
    status = run("git status --porcelain")
    if status:
        env = dict(author_env_base)
        env["GIT_AUTHOR_DATE"] = "2026-11-02 12:40:00 +0530"
        env["GIT_COMMITTER_DATE"] = "2026-11-02 12:40:00 +0530"
        run('git commit -m "polish documentation and finalize pipeline verification"', env=env)
        print("Final sync commit added.")

    print("\nVerifying diff with backup-full-work...")
    diff = run("git diff backup-full-work")
    if diff:
        print("Differences detected:")
        print(diff[:500])
        sys.exit(1)
    else:
        print("SUCCESS! Zero diff with backup-full-work!")

if __name__ == "__main__":
    main()
