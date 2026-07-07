"""
BaseScraper
-----------
Abstract base class for all land bank scrapers.

Each scraper must implement:
    - fetch_raw()
    - parse(raw)
    - normalize(parsed)

The BaseScraper handles:
    - HTTP requests
    - logging
    - error handling
    - output formatting
"""

import json
import requests
from abc import ABC, abstractmethod


class BaseScraper(ABC):
    def __init__(self, county_name: str):
        self.county = county_name.lower().replace(" ", "_")
        self.session = requests.Session()

    # ---------------------------------------------------------
    # HTTP Helpers
    # ---------------------------------------------------------
    def get(self, url, **kwargs):
        """
        Wrapper for GET requests with basic error handling.
        """
        try:
            resp = self.session.get(url, timeout=15, **kwargs)
            resp.raise_for_status()
            return resp
        except Exception as e:
            print(f"[{self.county}] GET failed: {url} → {e}")
            return None

    def get_json(self, url, **kwargs):
        """
        GET request expecting JSON.
        """
        resp = self.get(url, **kwargs)
        if not resp:
            return None

        try:
            return resp.json()
        except Exception as e:
            print(f"[{self.county}] JSON decode failed: {url} → {e}")
            return None

    # ---------------------------------------------------------
    # Abstract Methods (must be implemented by each scraper)
    # ---------------------------------------------------------
    @abstractmethod
    def fetch_raw(self):
        """
        Fetch raw data from the land bank source.
        Returns raw content (HTML, JSON, CSV, etc.)
        """
        pass

    @abstractmethod
    def parse(self, raw):
        """
        Parse raw content into structured Python objects.
        Returns list of dicts.
        """
        pass

    @abstractmethod
    def normalize(self, parsed):
        """
        Normalize parsed records into a unified schema:
            {
                "parcel_id": "...",
                "address": "...",
                "status": "...",
                "program": "...",
                "price": ...,
                "county": "...",
                "source": "wayne_lb",
            }
        """
        pass

    # ---------------------------------------------------------
    # Full pipeline
    # ---------------------------------------------------------
    def run(self):
        """
        Full scraper pipeline:
            raw → parsed → normalized
        """
        print(f"[{self.county}] Starting scraper...")

        raw = self.fetch_raw()
        if raw is None:
            print(f"[{self.county}] No raw data fetched.")
            return []

        parsed = self.parse(raw)
        if parsed is None:
            print(f"[{self.county}] Parsing failed.")
            return []

        normalized = self.normalize(parsed)
        print(f"[{self.county}] Completed. {len(normalized)} records.")

        return normalized
