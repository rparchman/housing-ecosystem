from pipeline.runners.opportunity_runner import run_opportunity_scoring

class OpportunityAgent:
    """
    Scores parcels and neighborhoods using legal public data sources.
    """

    def __init__(self):
        pass

    def score(self):
        output = run_opportunity_scoring()

        return {
            "status": "completed",
            "details": output
        }
