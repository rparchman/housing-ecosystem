def normalize_record(raw):
    return {
        "listing_id": raw.get("source_id"),
        "address": raw.get("address"),
        "meta": {"raw_html": raw.get("raw")},
        "va_tag": False
    }

def normalize_batch(raw_list):
    return [normalize_record(r) for r in raw_list]
