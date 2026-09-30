"""Run the successor's behavioural suite. No external services are required."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
if __name__ == '__main__':
    suite = unittest.defaultTestLoader.discover(str(ROOT / 'successor'), pattern='test_*.py')
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.testsRun < 100:
        print('Required behavioural case floor was not met.', file=sys.stderr)
        sys.exit(1)
    sys.exit(not result.wasSuccessful())
