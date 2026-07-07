"""
Monthly GIS Discovery Refresh Script
------------------------------------
Runs the full GIS Discovery Agent once per month to:

    - find new GIS servers
    - detect changed endpoints
    - detect new parcel layers
    - update counties.json
    - refresh counties_validated.json

This complements the weekly GIS Revalidation Agent.

Run:
    python pipeline/scripts/gis_monthly_refresh.py
"""

from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime
from pipeline.agents.gis_discovery_agent import GISDiscoveryAgent
from pipeline.agents.gis_revalidation_agent import GISRevalidationAgent


def run_monthly_discovery():
    print("\n======================================")
    print(f" Monthly GIS Discovery Started @ {datetime.now()}")
    print("======================================\n")

    # 1. Full discovery (crawl, probe, detect layers)
    discovery = GISDiscoveryAgent()
    discovered = discovery.run()

    print(f"\nDiscovered {len(discovered)} counties with GIS endpoints.")

    # 2. Revalidate newly discovered endpoints
    print("\nRevalidating newly discovered GIS endpoints...")
    revalidator = GISRevalidationAgent()
    validated = revalidator.run()

    print("\n======================================")
    print(f" Monthly GIS Discovery Completed @ {datetime.now()}")
    print(f" Validated Counties: {len(validated)}")
    print("======================================\n")


def main():
    scheduler = BlockingScheduler()

    # Run on the 1st of every month at 4 AM
    scheduler.add_job(
        run_monthly_discovery,
        trigger="cron",
        day=1,
        hour=4,
        minute=0,
        id="monthly_gis_discovery",
        replace_existing=True
    )

    print("Monthly GIS Discovery Scheduler is running...")
    print("Scheduled for the 1st of every month @ 4:00 AM.\n")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("Scheduler stopped.")
        

if __name__ == "__main__":
    main()
