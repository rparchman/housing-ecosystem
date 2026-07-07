"""
Fusion Pipeline Agent
Runs the entire statewide ecosystem pipeline end-to-end.
"""

from pipeline.agents.landbank_scraper_agent import LandBankScraperAgent
from pipeline.agents.parcel_join_agent import ParcelJoinAgent
from pipeline.agents.county_normalization_agent import CountyNormalizationAgent
from pipeline.agents.statewide_aggregation_agent import StatewideAggregationAgent


class FusionPipelineAgent:
    def __init__(self):
        self.scraper = LandBankScraperAgent()
        self.joiner = ParcelJoinAgent()
        self.normalizer = CountyNormalizationAgent()
        self.aggregator = StatewideAggregationAgent()

    def run(self):
        print("Scraping land bank inventory...")
        self.scraper.run()

        print("Joining land bank inventory to parcels...")
        self.joiner.run()

        print("Normalizing county parcel data...")
        self.normalizer.run()

        print("Aggregating statewide dataset...")
        final = self.aggregator.run()

        print("Fusion pipeline complete.")
        return final
