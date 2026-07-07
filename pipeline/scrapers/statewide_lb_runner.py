from pipeline.scrapers.wayne_lb import WayneLBScraper
from pipeline.scrapers.detroit_lb import DetroitLBScraper
from pipeline.scrapers.genesee_lb import GeneseeLBScraper
from pipeline.scrapers.monroe_lb import MonroeLBScraper
from pipeline.scrapers.washtenaw_lb import WashtenawLBScraper


def run_all_scrapers():
    scrapers = [
        WayneLBScraper(),
        DetroitLBScraper(),
        GeneseeLBScraper(),
        MonroeLBScraper(),
        WashtenawLBScraper(),
    ]

    results = {}

    for scraper in scrapers:
        results[scraper.county] = scraper.run()

    return results
