from pipeline.runners.marketing_runner import run_marketing

class MarketingAgent:
    """
    Generates marketing content based on listings, parcels, and scraped data.
    Wraps the marketing runner and adds orchestration logic.
    """

    def __init__(self):
        pass

    def generate(self):
        """
        Executes marketing content generation and returns structured results.
        """
        output = run_marketing()

        return {
            "status": "completed",
            "details": output
        }
