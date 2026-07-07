from pipeline.orchestrator.task_runner import PipelineOrchestrator
from pipeline.agents.backend_builder_agent import BackendBuilderAgent
from pipeline.agents.ingestion_agent import IngestionAgent
from pipeline.agents.scraper_agent import ScraperAgent
from pipeline.agents.public_scraper_agent import PublicScraperAgent
from pipeline.agents.test_agent import TestAgent
from pipeline.agents.marketing_agent import MarketingAgent
from pipeline.agents.opportunity_agent import OpportunityAgent
from pipeline.agents.gis_discovery_agent import GISDiscoveryAgent

# inside run_full_pipeline, before ingestion:
discovery = GISDiscoveryAgent()
discovery.run()  # writes counties_validated.json
# Optionally apply automatically (not recommended without review):
# discovery.apply_recommendations(dry_run=False)

class SupervisorAgent:
    """
    Coordinates pipeline tasks and agents.
    """

    def __init__(self):
        self.orchestrator = PipelineOrchestrator()
        self.backend_builder = BackendBuilderAgent()
        self.ingestion_agent = IngestionAgent()
        self.scraper_agent = ScraperAgent()
        self.public_scraper_agent = PublicScraperAgent()
        self.test_agent = TestAgent()
        self.marketing_agent = MarketingAgent()
        self.opportunity_agent = OpportunityAgent()

    def run_full_pipeline(self):
        """
        Executes the full pipeline workflow:
        - backend generation (if needed)
        - ingestion
        - legal public scraping
        - scraper (internal)
        - tests
        - marketing
        - opportunity scoring
        """
        report = self.orchestrator.task_pipeline_report().details

        # Backend generation if needed
        if report["backend"]["missing_modules"] or report["backend"]["missing_files"]:
            backend_result = self.backend_builder.generate_backend()
        else:
            backend_result = "Backend already complete"

        # Ingestion agent
        ingestion_result = self.ingestion_agent.ingest()

        # Legal public scraper agent
        public_scraper_result = self.public_scraper_agent.scrape()

        # Internal scraper agent
        scraper_result = self.scraper_agent.scrape()

        # Test agent
        test_result = self.test_agent.test()

        # Marketing agent
        marketing_result = self.marketing_agent.generate()

        # Opportunity scoring agent
        opportunity_result = self.opportunity_agent.score()

        return {
            "backend": backend_result,
            "ingestion": ingestion_result,
            "public_scraper": public_scraper_result,
            "scraper": scraper_result,
            "tests": test_result,
            "marketing": marketing_result,
            "opportunity": opportunity_result
        }
