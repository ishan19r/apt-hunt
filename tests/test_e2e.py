import unittest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import check_40x, calculate_budget, calculate_score, generate_inquiry, CONFIG

class TestFullWorkflow(unittest.TestCase):
    def test_complete_workflow(self):
        listing = {"address": "344 East 110th Street #6D", "rent": 2650, "no_fee": True}
        is_affordable = check_40x(listing["rent"])
        self.assertTrue(is_affordable)
        budget = calculate_budget(listing["rent"])
        self.assertGreater(budget["dining_out"], 400)
        score = calculate_score(listing)
        self.assertGreater(score, 50)
        inquiry = generate_inquiry(listing)
        self.assertIn(listing["address"], inquiry)
        self.assertIn(CONFIG["profile"]["name"], inquiry)

if __name__ == "__main__":
    unittest.main()
