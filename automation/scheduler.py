"""
Hourly Local Scheduler for BitBytes Post Automation.
Runs the pipeline every hour automatically when executed locally.
"""

import time
from datetime import datetime
from main import run_pipeline

INTERVAL_MINUTES = 60

def start_hourly_scheduler():
    print(f"\n=======================================================")
    print(f"⏰ BitBytes Hourly Local Scheduler Started")
    print(f"Interval: Every {INTERVAL_MINUTES} minutes")
    print(f"=======================================================\n")
    
    # Run once immediately on start
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Triggering hourly run...")
    try:
        run_pipeline()
    except Exception as exc:
        print(f"Error during run: {exc}")
        
    while True:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Sleeping for {INTERVAL_MINUTES} minutes until next hourly post...")
        time.sleep(INTERVAL_MINUTES * 60)
        
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Triggering next hourly post...")
        try:
            run_pipeline()
        except Exception as exc:
            print(f"Error during run: {exc}")

if __name__ == "__main__":
    start_hourly_scheduler()
