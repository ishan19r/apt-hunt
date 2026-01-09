#!/usr/bin/env python3
"""Integration Tests for Apartment Tracker"""
import unittest
import json
import os
import sys
import tempfile
import shutil
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import apartment_tracker as tracker

class TestTrackerIntegration(unittest.TestCase):
    """Integration tests for apartment tracker with file system"""
    
    def setUp(self):
        """Create temp directory for test files"""
        self.test_dir = tempfile.mkdtemp()
        self.original_tracker_file = tracker.TRACKER_FILE
        tracker.TRACKER_FILE = os.path.join(self.test_dir, "test_apartments.json")
    
    def tearDown(self):
        """Clean up temp files"""
        shutil.rmtree(self.test_dir)
        tracker.TRACKER_FILE = self.original_tracker_file
    
    def test_load_empty_tracker(self):
        """Loading non-existent file returns empty structure"""
        data = tracker.load_tracker()
        self.assertEqual(data, {"apartments": []})
    
    def test_save_and_load_tracker(self):
        """Data persists through save/load cycle"""
        test_data = {"apartments": [{"id": 1, "address": "Test St"}]}
        tracker.save_tracker(test_data)
        loaded = tracker.load_tracker()
        self.assertEqual(loaded, test_data)
    
    def test_add_apartment_creates_entry(self):
        """Adding apartment creates proper entry"""
        apt = tracker.add_apartment(
            address="123 Test Ave",
            rent=2600,
            neighborhood="Test Hood",
            url="https://test.com",
            broker="Test Broker",
            notes="Test notes"
        )
        self.assertEqual(apt["address"], "123 Test Ave")
        self.assertEqual(apt["rent"], 2600)
        self.assertEqual(apt["id"], 1)
        self.assertTrue(apt["40x_pass"])
    
    def test_add_multiple_apartments_increments_id(self):
        """Each apartment gets unique incrementing ID"""
        apt1 = tracker.add_apartment("Apt 1", 2600, "Hood", "url1")
        apt2 = tracker.add_apartment("Apt 2", 2700, "Hood", "url2")
        apt3 = tracker.add_apartment("Apt 3", 2800, "Hood", "url3")
        self.assertEqual(apt1["id"], 1)
        self.assertEqual(apt2["id"], 2)
        self.assertEqual(apt3["id"], 3)
    
    def test_40x_pass_calculated_correctly(self):
        """40x rule calculated on add"""
        apt_pass = tracker.add_apartment("Pass", 2600, "Hood", "url")
        apt_fail = tracker.add_apartment("Fail", 3000, "Hood", "url")
        self.assertTrue(apt_pass["40x_pass"])
        self.assertFalse(apt_fail["40x_pass"])
    
    def test_apartments_persist_after_multiple_adds(self):
        """All apartments saved to file"""
        tracker.add_apartment("Apt 1", 2600, "Hood", "url1")
        tracker.add_apartment("Apt 2", 2700, "Hood", "url2")
        data = tracker.load_tracker()
        self.assertEqual(len(data["apartments"]), 2)

class TestResponseGeneration(unittest.TestCase):
    """Integration tests for response message generation"""
    
    def test_inquiry_contains_address(self):
        """Inquiry message contains the address"""
        msg = tracker.generate_inquiry("456 Real St #5A")
        self.assertIn("456 Real St #5A", msg)
    
    def test_inquiry_contains_key_questions(self):
        """Inquiry contains all required questions"""
        msg = tracker.generate_inquiry("Test Address")
        self.assertIn("available", msg.lower())
        self.assertIn("fee", msg.lower())
        self.assertIn("income", msg.lower())
    
    def test_schedule_facetime_response(self):
        """FaceTime response mentions FaceTime"""
        msg = tracker.generate_schedule_response("John", "facetime")
        self.assertIn("FaceTime", msg)
        self.assertIn("John", msg)
    
    def test_schedule_inperson_response(self):
        """In-person response mentions availability"""
        msg = tracker.generate_schedule_response("Jane", "inperson")
        self.assertIn("Jane", msg)
        self.assertIn("5:30pm", msg)
    
    def test_negotiation_contains_target_rent(self):
        """Negotiation message contains target rent"""
        msg = tracker.generate_negotiation("Bob", 2600)
        self.assertIn("$2,600", msg)
        self.assertIn("Bob", msg)

if __name__ == "__main__":
    unittest.main()
