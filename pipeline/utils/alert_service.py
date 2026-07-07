"""
AlertService
------------
Unified Slack + Email alerting for statewide GIS maintenance.

Supports:
    - Slack webhook alerts
    - Email alerts via SMTP
    - Simple one-call notify() interface
"""

import smtplib
import ssl
import requests


class AlertService:
    def __init__(
        self,
        slack_webhook: str = None,
        email_sender: str = None,
        email_password: str = None,
        email_recipient: str = None,
        smtp_server: str = "smtp.gmail.com",
        smtp_port: int = 465,
    ):
        self.slack_webhook = slack_webhook
        self.email_sender = email_sender
        self.email_password = email_password
        self.email_recipient = email_recipient
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port

    # ---------------------------------------------------------
    # Slack Alerts
    # ---------------------------------------------------------
    def send_slack(self, message: str):
        if not self.slack_webhook:
            return

        try:
            requests.post(self.slack_webhook, json={"text": message})
        except Exception as e:
            print(f"[AlertService] Slack alert failed: {e}")

    # ---------------------------------------------------------
    # Email Alerts
    # ---------------------------------------------------------
    def send_email(self, subject: str, body: str):
        if not (self.email_sender and self.email_password and self.email_recipient):
            return

        msg = f"Subject: {subject}\n\n{body}"

        try:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=context) as server:
                server.login(self.email_sender, self.email_password)
                server.sendmail(self.email_sender, self.email_recipient, msg)
        except Exception as e:
            print(f"[AlertService] Email alert failed: {e}")

    # ---------------------------------------------------------
    # Unified Alert
    # ---------------------------------------------------------
    def notify(self, title: str, message: str):
        full_message = f"{title}\n\n{message}"

        # Slack
        self.send_slack(full_message)

        # Email
        self.send_email(title, message)

        print(f"[AlertService] Alert sent: {title}")
