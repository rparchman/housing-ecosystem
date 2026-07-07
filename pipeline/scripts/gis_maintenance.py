"""
GIS Maintenance Scheduler
-------------------------
Runs the GIS Revalidation Agent automatically every week.

This ensures:
    - GIS endpoints stay fresh
    - broken county services are detected
    - new parcel layers are discovered
    - statewide ingestion stays healthy

Run:
    python pipeline/scripts/gis_maintenance.py
"""

from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime
from pipeline.agents.gis_revalidation_agent import GISRevalidationAgent


def run_revalidation():
    print("\n======================================")
    print(f" GIS Revalidation Started @ {datetime.now()}")
    print("======================================\n")

    agent = GISRevalidationAgent()
    validated = agent.run()

    print("\n======================================")
    print(f" GIS Revalidation Completed @ {datetime.now()}")
    print(f" Valid Counties: {len(validated)}")
    print("======================================\n")


def main():
    scheduler = BlockingScheduler()

    # Run every week (Sunday at 3 AM)
    scheduler.add_job(
        run_revalidation,
        trigger="cron",
        day_of_week="sun",
        hour=3,
        minute=0,
        id="weekly_gis_revalidation",
        replace_existing=True
    )

    print("GIS Maintenance Scheduler is running...")
    print("Weekly revalidation scheduled for Sunday @ 3:00 AM.\n")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("Scheduler stopped.")


if __name__ == "__main__":
    main()
