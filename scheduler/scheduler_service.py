"""
Scheduler Service
-----------------
Runs:
    - Weekly GIS Revalidation Agent
    - Monthly GIS Discovery Agent

This container stays alive indefinitely and executes jobs on schedule.
"""

from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime

from pipeline.agents.gis_revalidation_agent import GISRevalidationAgent
from pipeline.agents.gis_discovery_agent import GISDiscoveryAgent
from pipeline.utils.alert_service import AlertService


# Configure alerts
alert = AlertService(
    slack_webhook="https://hooks.slack.com/services/XXX/YYY/ZZZ",
    email_sender="your_email@gmail.com",
    email_password="your_app_password",
    email_recipient="your_email@gmail.com"
)


def weekly_revalidation():
    print("\n=== Weekly GIS Revalidation ===")
    print(f"Started @ {datetime.now()}")

    agent = GISRevalidationAgent(
        slack_webhook=alert.slack_webhook,
        email_sender=alert.email_sender,
        email_password=alert.email_password,
        email_recipient=alert.email_recipient
    )

    validated = agent.run()

    if len(validated) == 0:
        alert.notify(
            "Weekly GIS Revalidation Failure",
            "All counties failed revalidation. Statewide ingestion may be broken."
        )

    print(f"Completed @ {datetime.now()}\n")


def monthly_discovery():
    print("\n=== Monthly GIS Discovery ===")
    print(f"Started @ {datetime.now()}")

    discovery = GISDiscoveryAgent()
    discovered = discovery.run()

    print(f"Discovered {len(discovered)} counties.")

    # Revalidate newly discovered endpoints
    revalidator = GISRevalidationAgent(
        slack_webhook=alert.slack_webhook,
        email_sender=alert.email_sender,
        email_password=alert.email_password,
        email_recipient=alert.email_recipient
    )

    validated = revalidator.run()

    alert.notify(
        "Monthly GIS Discovery Completed",
        f"Discovered {len(discovered)} counties. Validated {len(validated)}."
    )

    print(f"Completed @ {datetime.now()}\n")


def main():
    scheduler = BlockingScheduler()

    # Weekly revalidation — Sunday @ 3 AM
    scheduler.add_job(
        weekly_revalidation,
        trigger="cron",
        day_of_week="sun",
        hour=3,
        minute=0,
        id="weekly_revalidation"
    )

    # Monthly discovery — 1st of month @ 4 AM
    scheduler.add_job(
        monthly_discovery,
        trigger="cron",
        day=1,
        hour=4,
        minute=0,
        id="monthly_discovery"
    )

    print("Scheduler Service Running...")
    print("Weekly @ Sunday 3 AM")
    print("Monthly @ 1st of month 4 AM\n")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("Scheduler stopped.")


if __name__ == "__main__":
    main()
