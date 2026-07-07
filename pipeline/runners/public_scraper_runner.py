from pipeline.scraper.landbank_scraper import scrape_landbank
from pipeline.scraper.treasurer_scraper import scrape_treasurer
from pipeline.scraper.city_opendata_scraper import scrape_city_data
from pipeline.scraper.census_scraper import scrape_census
from pipeline.scraper.hud_scraper import scrape_hud
from pipeline.scraper.walkscore_scraper import scrape_walkscore
from pipeline.scraper.school_scraper import scrape_school_data
from pipeline.scraper.redfin_json import fetch_redfin_listings

def run_public_scraper():
    """
    Runs all legal public scraping sources.
    """

    return {
        "landbank": scrape_landbank(),
        "treasurer": scrape_treasurer(),
        "city": scrape_city_data(),
        "census": scrape_census(),
        "hud": scrape_hud(),
        "walkscore": scrape_walkscore(),
        "schools": scrape_school_data(),
        "redfin_public": fetch_redfin_listings("detroit")
    }
