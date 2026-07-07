"""
Parcel-to-Land-Bank Joiner Agent
Matches land bank listings to GIS parcel data using parcel ID, address, or fallback heuristics.
"""

import json
from pathlib import Path
from pipeline.joiners.parcel_matcher import match_by_parcel_id
from pipeline.joiners.address_matcher import match_by_address
from pipeline.joiners.fuzzy_matcher import fuzzy_match


class ParcelJoinAgent:
    def __init__(
        self,
        landbank_path=Path("pipeline/config/landbank_inventory.json"),
        counties_path=Path("pipeline/config/counties_validated.json"),
        output_path=Path("pipeline/config/landbank_parcel_join.json"),
    ):
        self.landbank_path = landbank_path
        self.counties_path = counties_path
        self.output_path = output_path

    def load_data(self):
        self.landbank = json.loads(self.landbank_path.read_text())
        self.counties = json.loads(self.counties_path.read_text())

    def join(self):
        """
        Attempts parcel ID match → address match → fuzzy match.
        """
        joined = {}
        unmatched = {}

        for county, records in self.landbank.items():
            joined[county] = []
            unmatched[county] = []

            gis_info = self.counties.get(county)
            if not gis_info:
                unmatched[county] = records
                continue

            for record in records:
                parcel_id = record.get("parcel_id")
                address = record.get("address")

                match = None

                if parcel_id:
                    match = match_by_parcel_id(parcel_id, gis_info)

                if not match and address:
                    match = match_by_address(address, gis_info)

                if not match:
                    match = fuzzy_match(record, gis_info)

                if match:
                    joined[county].append({**record, "parcel": match})
                else:
                    unmatched[county].append(record)

        return joined, unmatched

    def save(self, joined, unmatched):
        payload = {
            "joined": joined,
            "unmatched": unmatched,
        }
        self.output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def run(self):
        self.load_data()
        joined, unmatched = self.join()
        self.save(joined, unmatched)
        return joined
