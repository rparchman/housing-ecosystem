"""
Statewide Land Bank Aggregator Agent
Merges normalized county datasets into a single statewide dataset.
"""

import json
from pathlib import Path


class StatewideAggregationAgent:
    def __init__(
        self,
        unified_path=Path("pipeline/config/unified_county_data.json"),
        output_path=Path("pipeline/config/statewide_landbank_dataset.json"),
    ):
        self.unified_path = unified_path
        self.output_path = output_path

    def load(self):
        self.unified = json.loads(self.unified_path.read_text())

    def aggregate(self):
        statewide = []

        for county, records in self.unified.items():
            for record in records:
                statewide.append(record)

        return statewide

    def save(self, statewide):
        self.output_path.write_text(json.dumps(statewide, indent=2), encoding="utf-8")

    def run(self):
        self.load()
        statewide = self.aggregate()
        self.save(statewide)
        return statewide
