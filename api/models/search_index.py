"""
Statewide Search Index Builder
------------------------------
Builds a high-performance in-memory search index for:

    - parcel_id
    - address
    - owner
    - landbank.program
    - landbank.status

This index powers the /search API for fast lookups.
"""

import json
from pathlib import Path
from collections import defaultdict


class SearchIndex:
    def __init__(self, dataset_path=Path("pipeline/config/statewide_landbank_dataset.json")):
        self.dataset_path = dataset_path
        self.index = defaultdict(list)
        self.loaded = False

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------
    @staticmethod
    def tokenize(text: str):
        """
        Tokenize text into searchable chunks.
        """
        if not text:
            return []

        text = text.upper()
        tokens = text.replace(",", " ").replace(".", " ").split()
        return tokens

    def add_record(self, record):
        """
        Adds a single parcel record to the index.
        """
        parcel_id = record.get("parcel_id")
        address = record.get("address")
        owner = record.get("owner")

        landbank = record.get("landbank") or {}
        program = landbank.get("program")
        status = landbank.get("status")

        fields = [parcel_id, address, owner, program, status]

        for field in fields:
            if not field:
                continue

            for token in self.tokenize(field):
                self.index[token].append(record)

    # ---------------------------------------------------------
    # Build index
    # ---------------------------------------------------------
    def build(self):
        """
        Loads statewide dataset and builds the search index.
        """
        if not self.dataset_path.exists():
            raise FileNotFoundError("Statewide dataset not found")

        data = json.loads(self.dataset_path.read_text())

        for record in data:
            self.add_record(record)

        self.loaded = True
        return self.index

    # ---------------------------------------------------------
    # Search
    # ---------------------------------------------------------
    def search(self, query: str):
        """
        Searches the index using token matching.
        """
        if not self.loaded:
            self.build()

        query = query.upper()
        tokens = self.tokenize(query)

        results = []
        seen = set()

        for token in tokens:
            for record in self.index.get(token, []):
                key = record["parcel_id"]
                if key not in seen:
                    seen.add(key)
                    results.append(record)

        return results
