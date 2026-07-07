def __init__(self):
    self.orchestrator = PipelineOrchestrator()
    self.backend_builder = BackendBuilderAgent()
    self.ingestion_agent = IngestionAgent()
