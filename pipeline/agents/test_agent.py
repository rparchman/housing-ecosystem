from pipeline.runners.test_runner import run_tests

class TestAgent:
    """
    Handles backend and pipeline test execution.
    Wraps the test runner and adds orchestration logic.
    """

    def __init__(self):
        pass

    def test(self):
        """
        Executes tests and returns structured results.
        """
        output = run_tests()

        return {
            "status": "completed",
            "details": output
        }
