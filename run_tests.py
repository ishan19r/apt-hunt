#!/usr/bin/env python3
import unittest
import sys

def run_all_tests():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.discover('tests', pattern='test_*.py'))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    print("\n" + "="*60)
    print(f"Tests: {result.testsRun} | Failures: {len(result.failures)} | Errors: {len(result.errors)}")
    print("="*60)
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    sys.exit(run_all_tests())
