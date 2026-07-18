"""
Automated GIS Revalidation Agent
--------------------------------
Periodically revalidates county GIS endpoints discovered by the GIS Discovery Agent.
"""

import json
import os
from pathlib import Path
from pipeline.utils.arcgis import validate_service, validate_layer, sample_features
from pipeline.utils.alert_service import AlertService
import logging

logger = logging.getLogger(__name__)


class GISRevalidationAgent:
    def __init__(
        self,
        counties_path=Path("pipeline/config/counties.json"),
        validated_path=Path("pipeline/config/counties_validated.json"),
        slack_webhook=None,
        email_sender=None,
        email_password=None,
        email_recipient=None,
    ):
        # read credentials from environment if not provided
        email_sender = email_sender or os.getenv("EMAIL_SENDER")
        email_password = email_password or os.getenv("EMAIL_PASSWORD")
        email_recipient = email_recipient or os.getenv("EMAIL_RECIPIENT")

        self.counties_path = counties_path
        self.validated_path = validated_path

        # Alert system
        self.alert = AlertService(
            slack_webhook=slack_webhook,
            email_sender=email_sender,
            email_password=email_password,
            email_recipient=email_recipient,
        )

    def load(self):
        if not self.counties_path.exists():
            raise FileNotFoundError("counties.json not found")

        self.counties = json.loads(self.counties_path.read_text())
        self.validated = {}

    def revalidate_county(self, name, info):
        gis_url = info.get("gis_url")
        layer_id = info.get("layer_id", 0)

        logger.debug("[GIS Revalidation] %s → %s (layer %s)", name, gis_url, layer_id)

        if not gis_url:
            logger.debug("[%s] Missing GIS URL, skipping.", name)
            return None

        # 1. Service check
        if not validate_service(gis_url):
            logger.debug("[%s] Service unavailable.", name)
            return None

        # 2. Layer check
        layer_meta = validate_layer(gis_url, layer_id)
        if not layer_meta:
            logger.debug("[%s] Parcel layer not found.", name)
            return None

        # 3. Sample features
        sample = sample_features(gis_url, layer_id, limit=5)
        if not sample:
            logger.debug("[%s] No sample features returned.", name)
            return None

        # 4. Field presence
        fields = [f["name"].lower() for f in layer_meta.get("fields", [])]

        required = ["parcel", "parcelid", "sidwell", "pin", "taxid", "address", "situs"]
        has_required = any(r in fields for r in required)

        if not has_required:
            logger.debug("[%s] Missing key parcel/address fields.", name)
            return None

        logger.info("[%s] Revalidation OK.", name)
        return {
            "gis_url": gis_url,
            "layer_id": layer_id,
            "fields": fields,
        }

    def revalidate_all(self):
        self.load()

        for name, info in self.counties.items():
            result = self.revalidate_county(name, info)
            if result:
                self.validated[name] = result

        return self.validated

    def save(self):
        self.validated_path.write_text(json.dumps(self.validated, indent=2), encoding="utf-8")

    def run(self):
        logger.info("=== GIS Revalidation Agent ===")
        validated = self.revalidate_all()
        self.save()

        # Alert if everything failed
        if len(validated) == 0:
            self.alert.notify(
                "GIS Revalidation Failure",
                "All counties failed revalidation. Statewide ingestion may be broken."
            )

        return validated

