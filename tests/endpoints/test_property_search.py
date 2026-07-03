import unittest
from api.endpoints.property_search.controller import PropertySearchController

class TestPropertySearch(unittest.TestCase):
    def setUp(self):
        self.controller = PropertySearchController()

    def test_basic(self):
        params = {"q": "Main", "page": 1, "limit": 25, "status": None, "sort": None, "direction": None, "min_price": None, "max_price": None, "county": None}
        resp = self.controller.handle(params)
        self.assertEqual(resp["status"], 200)
        self.assertEqual(resp["page"], 1)
        self.assertEqual(resp["limit"], 25)
        # total should be at least 1 because mock contains "123 Main St"
        self.assertGreaterEqual(resp["total"], 1)
        self.assertGreaterEqual(resp["total_pages"], 1)
        self.assertIsInstance(resp["results"], list)

    def test_pagination_page2(self):
        # use q that matches many rows (or no q to use all rows)
        params = {"q": None, "page": 2, "limit": 2, "status": None, "sort": None, "direction": None, "min_price": None, "max_price": None, "county": None}
        resp = self.controller.handle(params)
        self.assertEqual(resp["status"], 200)
        self.assertEqual(resp["page"], 2)
        self.assertEqual(resp["limit"], 2)
        # total should equal number of mock rows (7 in current mock)
        self.assertEqual(resp["total"], 7)
        # total_pages should be ceil(7/2) == 4
        self.assertEqual(resp["total_pages"], 4)
        # page 2 should contain the expected ids (prop-003 and prop-004 in current mock)
        ids = [r["id"] for r in resp["results"]]
        self.assertIn("prop-003", ids)
        self.assertIn("prop-004", ids)

if __name__ == "__main__":
    unittest.main()
