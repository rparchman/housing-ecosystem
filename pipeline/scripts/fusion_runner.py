"""
Fusion Runner Script
--------------------
Runs the entire statewide housing ecosystem pipeline end-to-end.

This script executes:
    1. Land Bank Inventory Scraper Agent
    2. Parcel-to-Land-Bank Joiner Agent
    3. Unified County Data Model Agent
    4. Statewide Land Bank Aggregator Agent
    5. Fusion Pipeline Agent (full orchestrator)

Usage:
    python pipeline/scripts/fusion_runner.py
"""

import sys
from pathlib import Path

# Import agents
from pipeline.agents.landbank_scraper_agent import LandBankScraperAgent
from pipeline.agents.parcel_join_agent import ParcelJoinAgent
from pipeline.agents.county_normalization_agent import CountyNormalizationAgent
from pipeline.agents.statewide_aggregation_agent import StatewideAggregationAgent
from pipeline.agents.fusion_pipeline_agent import FusionPipelineAgent


def run_stage(title, func):
    print(f"\n=== {title} ===")
    try:
        result = func()
        print(f"{title} completed.")
        return result
    except Exception as e:
        print(f"ERROR during {title}: {e}")
        sys.exit(1)


def main():
    print("\n======================================")
    print("   Michigan Housing Ecosystem Fusion")
    print("======================================\n")

    # Instantiate agents
    scraper = LandBankScraperAgent()
    joiner = ParcelJoinAgent()
    normalizer = CountyNormalizationAgent()
    aggregator = StatewideAggregationAgent()
    fusion = FusionPipelineAgent()

    # Run pipeline stages
    run_stage("Scraping Land Bank Inventory", scraper.run)
    run_stage("Joining Land Bank Inventory to Parcels", joiner.run)
    run_stage("Normalizing County Parcel Data", normalizer.run)
    run_stage("Aggregating Statewide Dataset", aggregator.run)

    print("\n=== Running Full Fusion Pipeline ===")
    final = fusion.run()

    print("\n======================================")
    print(" Fusion Pipeline Complete")
    print(" Output: pipeline/config/statewide_landbank_dataset.json")
    print("======================================\n")

    return final


if __name__ == "__main__":
    main()
