import unittest
import os
import importlib
import sys

import gemini_helper

# @unittest.skipUnless(os.getenv("RUN_GEMINI_TEST"), "Set RUN_GEMINI_TEST=1 to enable")
class GeminiRealCallTestCase(unittest.TestCase):
    def setUp(self):
        os.environ.setdefault("GEMINI_MODEL", "gemini-1.5-flash")
        # Remove the fake module injected by other tests if present
        sys.modules.pop('google.generativeai', None)
        importlib.reload(gemini_helper)

    def test_parse_transactions_real(self):
        text = "Bought 1 share of AAPL at $100 on 2020-01-01"
        txs = gemini_helper.parse_transactions(text)
        self.assertIsInstance(txs, list)
        self.assertGreater(len(txs), 0)

if __name__ == "__main__":
    unittest.main()
