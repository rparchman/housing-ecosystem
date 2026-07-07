"""
Unified County Data Model Agent
Normalizes parcel fields across counties into a single statewide schema.
"""

import json
from pathlib import Path
from pipeline.models.unified_parcel_model import UnifiedParcelModel
from pipeline.models.county_field_maps import FIELD_MAPS


class CountyNormalizationAgent:
    def __init__(
        self,
        parcel_join_path=Path("pipeline/config/landbank_parcel_join.json"),
        output_path=Path("pipeline/config/unified_county_data.json"),
    ):
        self.parcel_join_path = parcel_join_path
        self.output_path = output_path

    def load(self):
        self.data = json.loads(self.parcel_join_path.read_text())

    def normalize(self):
        unified = {}

        for county, records in self.data["joined"].items():
            unified[county] = []

            field_map = FIELD_MAPS.get(county, {})

            for record in records:
                parcel = record["parcel"]
                unified_record = UnifiedParcelModel.normalize(parcel, field_map)
                unified_record["landbank"] = record
                unified[county].append(unified_record)

        return unified

    def save(self, unified):
        self.output_path.write_text(json.dumps(unified, indent=2), encoding="utf-8")

    def run(self):
        self.load()
        unified = self.normalize()
        self.save(unified)
        return unified
