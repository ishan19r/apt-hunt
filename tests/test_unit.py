import unittest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import check_40x, calculate_budget, calculate_score, CONFIG

class TestAffordability(unittest.TestCase):
    def test_affordability_pass_at_2600(self):
        self.assertTrue(check_40x(2600))
    def test_affordability_pass_at_2750(self):
        self.assertTrue(check_40x(2750))
    def test_affordability_fail_at_2800(self):
        self.assertFalse(check_40x(2800))
    def test_affordability_fail_at_3200(self):
        self.assertFalse(check_40x(3200))

class TestBudgetCalculation(unittest.TestCase):
    def test_budget_at_2600(self):
        budget = calculate_budget(2600)
        self.assertEqual(budget["rent"], 2600)
        self.assertGreater(budget["dining_out"], 0)
        self.assertGreater(budget["savings"], 0)
    def test_budget_savings_never_negative(self):
        for rent in [2600, 2800, 3000, 3200, 4000]:
            budget = calculate_budget(rent)
            self.assertGreaterEqual(budget["savings"], 0)

class TestScoring(unittest.TestCase):
    def test_score_range(self):
        apt = {"rent": 2600, "no_fee": False}
        score = calculate_score(apt)
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)
    def test_lower_rent_higher_score(self):
        apt_low = {"rent": 2400, "no_fee": False}
        apt_high = {"rent": 3200, "no_fee": False}
        self.assertGreater(calculate_score(apt_low), calculate_score(apt_high))

if __name__ == "__main__":
    unittest.main()
