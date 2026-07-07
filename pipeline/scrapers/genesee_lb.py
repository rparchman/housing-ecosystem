from pipeline.scrapers.base_scraper import BaseScraper

class GeneseeLBScraper(BaseScraper):
    def __init__(self):
        super().__init__("genesee")

        # Placeholder API endpoint
        self.api_url = "https://www.thelandbank.org/api/properties"

    def fetch_raw(self):
        return self.get_json(self.api_url)

    def parse(self, raw):
        if not raw:
            return []

        return raw.get("results", [])

    def normalize(self, parsed):
        normalized = []

        for item in parsed:
            normalized.append({
                "parcel_id": item.get("sidwell"),
                "address": item.get("address"),
                "status": item.get("status"),
                "program": item.get("program"),
                "price": item.get("price"),
                "county": "genesee",
                "source": "genesee_lb",
            })

        return normalized
