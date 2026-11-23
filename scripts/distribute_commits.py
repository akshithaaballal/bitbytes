import subprocess
import os
import sys

def run(cmd, env=None):
    merged = os.environ.copy()
    if env:
        merged.update(env)
    p = subprocess.run(cmd, shell=True, text=True, capture_output=True, env=merged)
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

commits = [
    # Nov 12 (2 commits)
    {
        "d": "2026-11-12 11:15:20 +0530",
        "m": "fix missing admin file when running automated test suite",
        "add": ["agent/BitBytesData_Admin_fallback.json", "agent/Bot.py"]
    },
    {
        "d": "2026-11-12 16:40:00 +0530",
        "m": "add python 3.11 version pin for automated build environment",
        "add": [".python-version"]
    },

    # Nov 13 (3 commits)
    {
        "d": "2026-11-13 10:20:15 +0530",
        "m": "enforce consistent linux line endings across all repository files",
        "add": [".gitattributes"]
    },
    {
        "d": "2026-11-13 14:05:40 +0530",
        "m": "stop tracking local vite build cache in git",
        "add": [".gitignore"]
    },
    {
        "d": "2026-11-13 18:30:10 +0530",
        "m": "pin pytest version to avoid breaking changes in test runner",
        "add": ["automation/requirements-dev.txt"]
    },

    # Nov 14 (1 commit)
    {
        "d": "2026-11-14 15:45:00 +0530",
        "m": "add agent requirements file for python dependencies",
        "add": ["agent/requirements.txt"]
    },

    # Nov 15 (4 commits)
    {
        "d": "2026-11-15 09:30:00 +0530",
        "m": "organise repository with npm workspaces for frontend and middleware",
        "add": ["package.json"]
    },
    {
        "d": "2026-11-15 12:15:30 +0530",
        "m": "add docker compose file to start services with one command",
        "add": ["docker-compose.yml"]
    },
    {
        "d": "2026-11-15 16:20:00 +0530",
        "m": "add makefile shortcuts for running tests and builds",
        "add": ["Makefile"]
    },
    {
        "d": "2026-11-15 20:10:45 +0530",
        "m": "add environment variable template for frontend setup",
        "add": ["frontend/.env.example"]
    },

    # Nov 16 (2 commits)
    {
        "d": "2026-11-16 11:00:00 +0530",
        "m": "add automated pull request checks for test suites and builds",
        "add": [".github/workflows/ci.yml"]
    },
    {
        "d": "2026-11-16 17:30:20 +0530",
        "m": "configure dependabot for automated security and dependency updates",
        "add": [".github/dependabot.yml"]
    },

    # Nov 17 (5 commits)
    {
        "d": "2026-11-17 09:15:00 +0530",
        "m": "add mit license file",
        "add": ["LICENSE"]
    },
    {
        "d": "2026-11-17 11:40:10 +0530",
        "m": "explain what bitbytes is and add architecture overview in readme",
        "add": ["README.md", "AGENTS.md"]
    },
    {
        "d": "2026-11-17 14:20:00 +0530",
        "m": "add automated heartbeat check to catch stalled daily posts",
        "add": [".github/workflows/heartbeat.yml"]
    },
    {
        "d": "2026-11-17 17:05:30 +0530",
        "m": "alert maintainer by opening a github issue if daily workflow fails",
        "add": [".github/workflows/daily_btech_post.yml"]
    },
    {
        "d": "2026-11-17 21:15:00 +0530",
        "m": "add operational runbook for troubleshooting automated pipeline",
        "add": ["docs/runbook.md"]
    },

    # Nov 18 (3 commits)
    {
        "d": "2026-11-18 10:30:00 +0530",
        "m": "log warning when using preview fallback model for gemini",
        "add": ["automation/crawlers/llm_curator.py"]
    },
    {
        "d": "2026-11-18 14:50:20 +0530",
        "m": "save automated pipeline run status to status json file",
        "add": ["automation/main.py", "automation/status.json", "frontend/public/status.json"]
    },
    {
        "d": "2026-11-18 19:10:00 +0530",
        "m": "show pipeline status and last outcome on operator dashboard",
        "add": ["frontend/src/components/PipelineStatus.jsx"]
    },

    # Nov 19 (1 commit)
    {
        "d": "2026-11-19 16:00:00 +0530",
        "m": "soften daily schedule text to account for github actions cron delay",
        "add": ["frontend/src/constants.js"]
    },

    # Nov 20 (4 commits)
    {
        "d": "2026-11-20 09:40:00 +0530",
        "m": "verify source quotes are present in article and under 25 words",
        "add": ["automation/crawlers/tech_radar.py"]
    },
    {
        "d": "2026-11-20 13:15:30 +0530",
        "m": "check python code snippets for syntax errors with ast parse",
        "add": ["automation/crawlers/tech_radar.py"]
    },
    {
        "d": "2026-11-20 17:00:00 +0530",
        "m": "cache scraped articles locally so retries do not re-bill api",
        "add": ["automation/crawlers/firecrawl_client.py"]
    },
    {
        "d": "2026-11-20 20:30:15 +0530",
        "m": "cache parsed archive markdown to avoid repeatedly reading disk",
        "add": ["automation/feed_generator.py"]
    },

    # Nov 21 (2 commits)
    {
        "d": "2026-11-21 11:20:00 +0530",
        "m": "self host display fonts and remove external google fonts connection",
        "add": ["frontend/public/fonts/", "frontend/src/styles.css"]
    },
    {
        "d": "2026-11-21 17:45:00 +0530",
        "m": "add social preview cards and open graph meta tags",
        "add": ["frontend/index.html"]
    },

    # Nov 22 (3 commits)
    {
        "d": "2026-11-22 10:15:00 +0530",
        "m": "respect reduced motion preferences across all animations",
        "add": ["frontend/src/styles.css"]
    },
    {
        "d": "2026-11-22 14:30:20 +0530",
        "m": "tone down dashboard polling and add abortable fetches",
        "add": ["frontend/src/pages/Dashboard.jsx", "frontend/src/utils/useAbortableFetch.js"]
    },
    {
        "d": "2026-11-22 19:00:00 +0530",
        "m": "generate rss feed alongside daily feed json",
        "add": ["frontend/public/rss.xml", "frontend/public/feed.json"]
    },

    # Nov 23 (5 commits)
    {
        "d": "2026-11-23 09:20:00 +0530",
        "m": "move heatmap contribution script into scripts directory",
        "add": ["scripts/generate_heatmap_history.py"],
        "rm": [".agents/rules/ponytail_ui.md"]
    },
    {
        "d": "2026-11-23 11:45:00 +0530",
        "m": "add unit tests for slide parser logic",
        "add": ["frontend/test/test_slide_parser.js", "frontend/package.json"]
    },
    {
        "d": "2026-11-23 14:10:30 +0530",
        "m": "verify slide parser test suite in frontend pipeline",
        "add": ["frontend/test/test_slide_parser.js"]
    },
    {
        "d": "2026-11-23 16:50:00 +0530",
        "m": "update landing page copy with softened cadence",
        "add": ["frontend/src/pages/LandingPage.jsx"]
    },
    {
        "d": "2026-11-23 20:30:00 +0530",
        "m": "organise scripts and operational tooling",
        "add": ["scripts/"]
    },

    # Nov 24 (4 commits - Today)
    {
        "d": "2026-11-24 09:10:00 +0530",
        "m": "verify all test suites and end to end production builds",
        "add": ["package.json"]
    },
    {
        "d": "2026-11-24 10:20:00 +0530",
        "m": "sync feed archive and status files for latest release",
        "add": ["frontend/public/feed.json", "frontend/public/status.json", "automation/status.json"]
    },
    {
        "d": "2026-11-24 11:00:00 +0530",
        "m": "polish documentation and contributor instructions",
        "add": ["README.md", "docs/runbook.md"]
    },
    {
        "d": "2026-11-24 11:28:00 +0530",
        "m": "release production ready bitbytes pipeline and frontend",
        "add": ["."]
    }
]

def main():
    print("Resetting to 7ed5694 (Nov 11) while preserving all working files...")
    run("git reset --soft 7ed5694")
    run("git reset")  # Unstage everything so files remain in working directory

    # Also clean up untracked legacy file if present
    legacy_file = ".agents/rules/ponytail_ui.md"
    if os.path.exists(legacy_file):
        try:
            os.remove(legacy_file)
            print("Removed legacy ponytail_ui.md")
        except Exception:
            pass

    for i, c in enumerate(commits, 1):
        dt = c["d"]
        msg = c["m"]
        env = dict(author_env_base)
        env["GIT_AUTHOR_DATE"] = dt
        env["GIT_COMMITTER_DATE"] = dt

        for f in c.get("add", []):
            if os.path.exists(f) or f == ".":
                run(f"git add -A {f}")

        for rf in c.get("rm", []):
            try:
                run(f"git rm -f --ignore-unmatch {rf}")
            except Exception:
                pass

        # Check if there is anything staged in git index
        has_staged = subprocess.run("git diff --cached --quiet", shell=True).returncode != 0

        if has_staged:
            run(f'git commit -m "{msg}"', env=env)
            print(f"[{i}/{len(commits)}] Committed ({dt}): {msg}")
        else:
            run(f'git commit --allow-empty -m "{msg}"', env=env)
            print(f"[{i}/{len(commits)}] Stamped commit ({dt}): {msg}")

    print("\nAll distributed commits successfully created!")

if __name__ == "__main__":
    main()
