"""
Automated GIS Revalidation Agent
--------------------------------
Periodically revalidates county GIS endpoints discovered by the GIS Discovery Agent.

Checks:
    - service availability
    - parcel layer existence
    - field presence (parcel ID, address, owner, etc.)
    - sample feature retrieval

Updates:
    - pipeline/config/counties_validated.json

Includes:
    - Slack + Email alerting for failures
"""

import json
from pathlib import Path
from pipeline.utils.arcgis import validate_service, validate_layer, sample_features
from pipeline.utils.alert_service import AlertService


class GISRevalidationAgent:
    def __init__(
        self,
        counties_path=Path("pipeline/config/counties.json"),
        validated_path=Path("pipeline/config/counties_validated.json"),
        slack_webhook=None,
        email_sender=rickie_parchman@yahoo.com,
        email_password=Deeznuff#2,
        email_recipient=rickie_parchman@yahoo.com,
    ):
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

        print(f"[GIS Revalidation] {name} → {gis_url} (layer {layer_id})")

        if not gis_url:
            print(f"[{name}] Missing GIS URL, skipping.")
            return None

        # 1. Service check
        if not validate_service(gis_url):
            print(f"[{name}] Service unavailable.")
            return None

        # 2. Layer check
        layer_meta = validate_layer(gis_url, layer_id)
        if not layer_meta:
            print(f"[{name}] Parcel layer not found.")
            return None

        # 3. Sample features
        sample = sample_features(gis_url, layer_id, limit=5)
        if not sample:
            print(f"[{name}] No sample features returned.")
            return None

        # 4. Field presence
        fields = [f["name"].lower() for f in layer_meta.get("fields", [])]

        required = ["parcel", "parcelid", "sidwell", "pin", "taxid", "address", "situs"]
        has_required = any(r in fields for r in required)

        if not has_required:
            print(f"[{name}] Missing key parcel/address fields.")
            return None

        print(f"[{name}] Revalidation OK.")
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
        print("\n=== GIS Revalidation Agent ===")
        validated = self.revalidate_all()
        self.save()

        # Alert if everything failed
        if len(validated) == 0:
            self.alert.notify(
                "GIS Revalidation Failure",
                "All counties failed revalidation. Statewide ingestion may be broken."
            )

        return validated

