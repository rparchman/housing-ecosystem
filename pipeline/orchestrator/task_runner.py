import json
from pathlib import Path

# Runners
from pipeline.runners.ingestion_runner import run_ingestion
from pipeline.runners.scraper_runner import run_scraper
from pipeline.runners.test_runner import run_tests

# Parser
from pipeline.parser.module_parser import build_creation_plan, build_full_parser_report


class TaskResult:
    """
    Represents the result of a pipeline task.
    """
    def __init__(self, task_name, success, details=None):
        self.task_name = task_name
        self.success = success
        self.details = details or {}

    def to_dict(self):
        return {
            "task": self.task_name,
            "success": self.success,
            "details": self.details
        }


class PipelineOrchestrator:
    """
    The brain of the pipeline.
    Executes tasks, coordinates runners, and integrates with agents.
    """

    def __init__(self):
        self.history = []

    def log(self, result: TaskResult):
        self.history.append(result.to_dict())

    # ---------------------------------------------------------
    # BACKEND GENERATION TASK
    # ---------------------------------------------------------
    def task_generate_backend(self):
        plan = build_creation_plan()

        result = TaskResult(
            "generate_backend",
            success=True,
            details=plan
        )

        self.log(result)
        return result

    # ---------------------------------------------------------
    # INGESTION TASK
    # ---------------------------------------------------------
    def task_run_ingestion(self):
        output = run_ingestion()

        result = TaskResult(
            "run_ingestion",
            success=True,
            details={"output": output}
        )

        self.log(result)
        return result

    # ---------------------------------------------------------
    # SCRAPER TASK
    # ---------------------------------------------------------
    def task_run_scraper(self):
        output = run_scraper()

        result = TaskResult(
            "run_scraper",
            success=True,
            details={"output": output}
        )

        self.log(result)
        return result

    # ---------------------------------------------------------
    # TEST TASK
    # ---------------------------------------------------------
    def task_run_tests(self):
        output = run_tests()

        result = TaskResult(
            "run_tests",
            success=True,
            details={"output": output}
        )

        self.log(result)
        return result

    # ---------------------------------------------------------
    # FULL PIPELINE REPORT
    # ---------------------------------------------------------
    def task_pipeline_report(self):
        report = build_full_parser_report()

        result = TaskResult(
            "pipeline_report",
            success=True,
            details=report
        )

        self.log(result)
        return result

    # ---------------------------------------------------------
    # EXPORT HISTORY
    # ---------------------------------------------------------
    def export_history(self, path="pipeline_history.json"):
        Path(path).write_text(json.dumps(self.history, indent=2))
        return path
