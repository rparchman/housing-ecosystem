from pipeline.runners.public_scraper_runner import run_public_scraper

class PublicScraperAgent:
    """
    Scrapes only legal public data sources:
    - County Land Bank
    - County Treasurer
    - City Open Data
    - Census / HUD
    - Public JSON APIs
    """

    def __init__(self):
        pass

    def scrape(self):
        output = run_public_scraper()

        return {
            "status": "completed",
            "details": output
        }
