from pipeline.scrapers.base_scraper import BaseScraper

class MonroeLBScraper(BaseScraper):
    def __init__(self):
        super().__init__("monroe")

        # Placeholder HTML listing page
        self.listing_url = "https://monroecountylandbank.com/properties"

    def fetch_raw(self):
        return self.get(self.listing_url)

    def parse(self, raw):
        if not raw:
            return []

        html = raw.text

        # Placeholder HTML parsing
        # You will plug in BeautifulSoup here
        parsed = []

        # Example structure
        # parsed.append({
        #     "parcel_id": "...",
        #     "address": "...",
        #     "status": "...",
        #     "program": "...",
        #     "price": "...",
        # })

        return parsed

    def normalize(self, parsed):
        normalized = []

        for item in parsed:
            normalized.append({
                "parcel_id": item.get("parcel_id"),
                "address": item.get("address"),
                "status": item.get("status"),
                "program": item.get("program"),
                "price": item.get("price"),
                "county": "monroe",
                "source": "monroe_lb",
            })

        return normalized
