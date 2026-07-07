import logging

logging.basicConfig(
    filename="logs/ingestion.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def log_ingestion(county, count):
    logging.info(f"Ingested {count} parcels for {county}")
