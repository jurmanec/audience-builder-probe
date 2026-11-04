"""Template intent checks. Run: python -m unittest tests.test_templates"""

from __future__ import annotations

import unittest

from builder.templates import run_template


class TemplateTest(unittest.TestCase):
    def test_known_intents_return_draft_audiences(self) -> None:
        expected = {
            "at-risk renewal": 2147,
            "heavy-use upgrade": 440,
            "lapsed video offer": 1052,
        }
        for intent, size in expected.items():
            audience = run_template(intent)
            self.assertIsNotNone(audience)
            assert audience is not None
            self.assertEqual(audience.estimated_size, size)
            self.assertEqual(audience.status, "draft")

    def test_missing_intent_returns_no_audience(self) -> None:
        self.assertIsNone(run_template(None))
        self.assertIsNone(run_template(""))
        self.assertIsNone(run_template("unknown intent"))


if __name__ == "__main__":
    unittest.main()
