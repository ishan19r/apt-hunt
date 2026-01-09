#!/usr/bin/env python3
"""Unit Tests for Apartment Hunter"""
import unittest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apartment_hunter import check_affordability, calculate_budget, CRITERIA

class TestAffordability(unittest.TestCase):
    """Unit tests for affordability calculations"""
    
    def test_affordability_pass_at_2600(self):
        """$2,600 rent should pass 40x rule with $110k income"""
        self.assertTrue(check_affordability(2600))
    
    def test_affordability_pass_at_2750(self):
        """$2,750 rent should pass 40x rule (exactly $110k needed)"""
        self.assertTrue(check_affordability(2750))
    
    def test_affordability_fail_at_2800(self):
        """$2,800 rent should fail 40x rule (needs $112k)"""
        self.assertFalse(check_affordability(2800))
    
    def test_affordability_fail_at_3200(self):
        """$3,200 rent should fail 40x rule (needs $128k)"""
        self.assertFalse(check_affordability(3200))
    
    def test_affordability_edge_case_zero(self):
        """$0 rent should always pass"""
        self.assertTrue(check_affordability(0))

class TestBudgetCalculation(unittest.TestCase):
    """Unit tests for budget calculations"""
    
    def test_budget_at_2600(self):
        """Budget at $2,600 rent"""
        budget = calculate_budget(2600)
        self.assertEqual(budget["rent"], 2600)
        self.assertEqual(budget["utilities"], 150)
        self.assertEqual(budget["groceries"], 400)
        self.assertEqual(budget["transport"], 132)
        self.assertGreater(budget["dining_out"], 0)
        self.assertGreater(budget["savings"], 0)
    
    def test_budget_at_3200(self):
        """Budget at $3,200 rent leaves less savings"""
        budget_low = calculate_budget(2600)
        budget_high = calculate_budget(3200)
        self.assertGreater(budget_low["savings"], budget_high["savings"])
    
    def test_budget_dining_out_capped_at_500(self):
        """Dining out should be capped at $500"""
        budget = calculate_budget(2600)
        self.assertLessEqual(budget["dining_out"], 500)
    
    def test_budget_savings_never_negative(self):
        """Savings should never be negative"""
        for rent in [2600, 2800, 3000, 3200, 4000]:
            budget = calculate_budget(rent)
            self.assertGreaterEqual(budget["savings"], 0)

class TestCriteria(unittest.TestCase):
    """Unit tests for search criteria"""
    
    def test_criteria_income_set(self):
        """Income should be $110,000"""
        self.assertEqual(CRITERIA["income"], 110000)
    
    def test_criteria_rent_range(self):
        """Rent range should be $2,400 - $3,200"""
        self.assertEqual(CRITERIA["min_rent"], 2400)
        self.assertEqual(CRITERIA["max_rent"], 3200)
    
    def test_criteria_bedrooms(self):
        """Should be searching for 1BR"""
        self.assertEqual(CRITERIA["bedrooms"], 1)
    
    def test_criteria_neighborhoods_not_empty(self):
        """Should have neighborhoods defined"""
        self.assertGreater(len(CRITERIA["neighborhoods"]), 0)

if __name__ == "__main__":
    unittest.main()
