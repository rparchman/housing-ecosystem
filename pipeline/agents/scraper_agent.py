from pipeline.runners.scraper_runner import run_scraper

class ScraperAgent:
    """
    Handles listing scraping workflows.
    Wraps the scraper runner and adds orchestration logic.
    """

    def __init__(self):
        pass

    def scrape(self):
        """
        Executes scraping and returns structured results.
        """
        output = run_scraper()

        return {
            "status": "completed",
            "details": output
        }
