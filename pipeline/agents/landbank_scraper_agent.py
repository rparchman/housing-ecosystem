"""
Land Bank Inventory Scraper Agent
Collects inventory from all Michigan land banks and normalizes it.
"""

from pathlib import Path
import json
from pipeline.scrapers.base_scraper import BaseScraper
from pipeline.scrapers.statewide_lb_runner import run_all_scrapers


class LandBankScraperAgent:
    def __init__(self, output_path: Path = Path("pipeline/config/landbank_inventory.json")):
        self.output_path = output_path
        self.inventory = {}

    def scrape_all(self):
        """
        Runs all land bank scrapers and merges their normalized output.
        """
        results = run_all_scrapers()
        merged = {}

        for county, records in results.items():
            merged[county] = records

        self.inventory = merged
        return merged

    def save(self):
        """
        Writes the statewide land bank inventory to disk.
        """
        self.output_path.write_text(json.dumps(self.inventory, indent=2), encoding="utf-8")

    def run(self):
        """
        Full pipeline: scrape → merge → save.
        """
        self.scrape_all()
        self.save()
        return self.inventory
