import unittest
import json
import os
import sys
import tempfile
import shutil
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import app

class TestTrackerIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.original_tracker = app.TRACKER_FILE
        app.TRACKER_FILE = os.path.join(self.test_dir, "test.json")
    def tearDown(self):
        shutil.rmtree(self.test_dir)
        app.TRACKER_FILE = self.original_tracker
    def test_load_empty_tracker(self):
        data = app.load_tracker()
        self.assertEqual(data["apartments"], [])
    def test_save_and_load(self):
        test_data = {"apartments": [{"id": "1", "address": "Test"}], "inquiries_sent": [], "last_scrape": None}
        app.save_tracker(test_data)
        loaded = app.load_tracker()
        self.assertEqual(loaded["apartments"][0]["address"], "Test")

if __name__ == "__main__":
    unittest.main()
