from pipeline.agents.supervisor_agent import SupervisorAgent

class MultiAgentOrchestrator:
    """
    High-level orchestrator that coordinates scheduled and on-demand agent workflows.
    """

    def __init__(self):
        self.supervisor = SupervisorAgent()

    def run_nightly_ingestion(self):
        """
        Runs ingestion + scraping + tests nightly.
        """
        result = self.supervisor.run_full_pipeline()
        return {
            "task": "nightly_ingestion",
            "result": result
        }

    def run_weekly_marketing(self):
        """
        Runs marketing generation weekly.
        """
        marketing_result = self.supervisor.marketing_agent.generate()
        return {
            "task": "weekly_marketing",
            "result": marketing_result
        }

    def run_backend_regeneration(self):
        """
        Regenerates backend modules if templates changed.
        """
        backend_result = self.supervisor.backend_builder.generate_backend()
        return {
            "task": "backend_regeneration",
            "result": backend_result
        }

    def run_full_system_check(self):
        """
        Runs ingestion, scraping, tests, marketing — full ecosystem validation.
        """
        result = self.supervisor.run_full_pipeline()
        return {
            "task": "full_system_check",
            "result": result
        }
