from pipeline.runners.ingestion_runner import run_ingestion

class IngestionAgent:
    """
    Handles ingestion workflows.
    Wraps the ingestion runner and adds orchestration logic.
    """

    def __init__(self):
        pass

    def ingest(self):
        """
        Executes ingestion and returns structured results.
        """
        output = run_ingestion()

        return {
            "status": "completed",
            "details": output
        }
