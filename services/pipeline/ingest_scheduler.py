from services.landbank.scraper_county_MI_primary import run_scraper_sample
from services.landbank.normalizer import normalize_batch
from services.shared.db import get_db_session

def main():
    raw = run_scraper_sample()
    normalized = normalize_batch(raw)
    db = get_db_session()
    for rec in normalized:
        pass

if __name__ == "__main__":
    main()
