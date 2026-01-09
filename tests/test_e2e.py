#!/usr/bin/env python3
"""End-to-End Tests for Apartment Hunting Workflow"""
import unittest
import json
import os
import sys
import tempfile
import shutil
import subprocess
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import apartment_tracker as tracker
from apartment_hunter import check_affordability, calculate_budget, generate_inquiry

class TestFullWorkflowE2E(unittest.TestCase):
    """End-to-end tests simulating real user workflows"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.original_tracker_file = tracker.TRACKER_FILE
        tracker.TRACKER_FILE = os.path.join(self.test_dir, "test_apartments.json")
    
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.test_dir)
        tracker.TRACKER_FILE = self.original_tracker_file
    
    def test_complete_apartment_search_workflow(self):
        """
        E2E: Full workflow from finding apartment to sending inquiry
        
        Simulates: User finds listing -> checks affordability -> 
        adds to tracker -> generates inquiry
        """
        # Step 1: User finds a listing on StreetEasy
        listing = {
            "address": "344 East 110th Street #6D",
            "rent": 2650,
            "neighborhood": "East Harlem",
            "url": "https://streeteasy.com/rental/test",
            "broker": "Cole Someck"
        }
        
        # Step 2: Check if it passes 40x rule
        is_affordable = check_affordability(listing["rent"])
        self.assertTrue(is_affordable, "Apartment should be affordable")
        
        # Step 3: Calculate budget impact
        budget = calculate_budget(listing["rent"])
        self.assertGreater(budget["dining_out"], 400, "Should have dining budget")
        self.assertGreater(budget["savings"], 500, "Should have savings")
        
        # Step 4: Add to tracker
        apt = tracker.add_apartment(
            address=listing["address"],
            rent=listing["rent"],
            neighborhood=listing["neighborhood"],
            url=listing["url"],
            broker=listing["broker"],
            notes="Private terrace, flexible lease"
        )
        self.assertEqual(apt["status"], "interested")
        self.assertTrue(apt["40x_pass"])
        
        # Step 5: Generate inquiry message
        inquiry = tracker.generate_inquiry(listing["address"])
        self.assertIn(listing["address"], inquiry)
        self.assertIn("Ishan", inquiry)
        
        # Step 6: Verify apartment is persisted
        data = tracker.load_tracker()
        self.assertEqual(len(data["apartments"]), 1)
        self.assertEqual(data["apartments"][0]["address"], listing["address"])
    
    def test_multiple_apartments_comparison_workflow(self):
        """
        E2E: Compare multiple apartments and pick best option
        
        Simulates: User adds 3 apartments -> compares budgets -> 
        identifies best option
        """
        apartments = [
            {"address": "Apt A - East Harlem", "rent": 2600},
            {"address": "Apt B - UES", "rent": 2800},
            {"address": "Apt C - Yorkville", "rent": 3200},
        ]
        
        results = []
        for apt in apartments:
            affordable = check_affordability(apt["rent"])
            budget = calculate_budget(apt["rent"])
            tracker.add_apartment(apt["address"], apt["rent"], "Manhattan", "url")
            results.append({
                "address": apt["address"],
                "rent": apt["rent"],
                "affordable": affordable,
                "savings": budget["savings"],
                "dining": budget["dining_out"]
            })
        
        # Verify all added
        data = tracker.load_tracker()
        self.assertEqual(len(data["apartments"]), 3)
        
        # Find best option (affordable + highest savings)
        affordable_options = [r for r in results if r["affordable"]]
        self.assertEqual(len(affordable_options), 1, "Only $2,600 should pass 40x")
        
        best = max(affordable_options, key=lambda x: x["savings"])
        self.assertEqual(best["rent"], 2600)
    
    def test_negotiation_workflow(self):
        """
        E2E: Full negotiation workflow
        
        Simulates: View apartment -> like it -> send negotiation
        """
        # Add apartment
        apt = tracker.add_apartment(
            address="3rd Floor Unit",
            rent=2700,
            neighborhood="East Harlem",
            url="https://streeteasy.com/rental/3265122",
            broker="Doron Sher",
            notes="Negotiable"
        )
        
        # Generate negotiation for $2,600
        target_rent = 2600
        msg = tracker.generate_negotiation("Doron Sher", target_rent)
        
        self.assertIn("Doron Sher", msg)
        self.assertIn("$2,600", msg)
        self.assertIn("ready to sign", msg.lower())
        
        # Verify savings difference
        budget_original = calculate_budget(2700)
        budget_negotiated = calculate_budget(2600)
        monthly_savings = budget_negotiated["savings"] - budget_original["savings"]
        self.assertEqual(monthly_savings, 100, "Should save $100/mo by negotiating")
    
    def test_scripts_run_without_errors(self):
        """E2E: Both scripts execute without errors"""
        # Test apartment_hunter.py
        result = subprocess.run(
            [sys.executable, "apartment_hunter.py"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        self.assertEqual(result.returncode, 0, f"apartment_hunter.py failed: {result.stderr}")
        self.assertIn("APARTMENT HUNTER", result.stdout)
        
        # Test apartment_tracker.py
        result = subprocess.run(
            [sys.executable, "apartment_tracker.py"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        self.assertEqual(result.returncode, 0, f"apartment_tracker.py failed: {result.stderr}")

class TestDataIntegrityE2E(unittest.TestCase):
    """E2E tests for data integrity across operations"""
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.original_tracker_file = tracker.TRACKER_FILE
        tracker.TRACKER_FILE = os.path.join(self.test_dir, "test_apartments.json")
    
    def tearDown(self):
        shutil.rmtree(self.test_dir)
        tracker.TRACKER_FILE = self.original_tracker_file
    
    def test_json_file_valid_after_operations(self):
        """JSON file remains valid after multiple operations"""
        for i in range(10):
            tracker.add_apartment(f"Apt {i}", 2600 + (i * 50), "Hood", f"url{i}")
        
        # Verify JSON is valid
        with open(tracker.TRACKER_FILE, 'r') as f:
            data = json.load(f)
        
        self.assertEqual(len(data["apartments"]), 10)
        
        # Verify all required fields present
        for apt in data["apartments"]:
            self.assertIn("id", apt)
            self.assertIn("address", apt)
            self.assertIn("rent", apt)
            self.assertIn("40x_pass", apt)
            self.assertIn("status", apt)

if __name__ == "__main__":
    unittest.main()
