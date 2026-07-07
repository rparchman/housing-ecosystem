from pipeline.scrapers.base_scraper import BaseScraper

class WashtenawLBScraper(BaseScraper):
    def __init__(self):
        super().__init__("washtenaw")

        # Placeholder CSV or HTML listing
        self.listing_url = "https://washtenawlandbank.org/listings"

    def fetch_raw(self):
        return self.get(self.listing_url)

    def parse(self, raw):
        if not raw:
            return []

        text = raw.text

        parsed = []

        # Placeholder CSV/HTML parsing
        # You will plug in BeautifulSoup or csv.reader here

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
                "county": "washtenaw",
                "source": "washtenaw_lb",
            })

        return normalized
