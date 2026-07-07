from pipeline.scrapers.base_scraper import BaseScraper

class WayneLBScraper(BaseScraper):
    def __init__(self):
        super().__init__("wayne")

        # WordPress JSON endpoint (placeholder)
        self.api_url = "https://waynecountylandbank.com/wp-json/wp/v2/properties"

    def fetch_raw(self):
        return self.get_json(self.api_url)

    def parse(self, raw):
        if not raw:
            return []

        parsed = []
        for item in raw:
            parsed.append({
                "title": item.get("title", {}).get("rendered"),
                "content": item.get("content", {}).get("rendered"),
                "meta": item.get("meta", {}),
            })
        return parsed

    def normalize(self, parsed):
        normalized = []

        for item in parsed:
            meta = item.get("meta", {})

            normalized.append({
                "parcel_id": meta.get("parcel_id"),
                "address": meta.get("address"),
                "status": meta.get("status"),
                "program": meta.get("program"),
                "price": meta.get("price"),
                "county": "wayne",
                "source": "wayne_lb",
            })

        return normalized
