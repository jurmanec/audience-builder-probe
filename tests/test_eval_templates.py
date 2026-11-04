"""Gold-set run of the template path. Run: python -m unittest tests.test_eval_templates"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from eval.templates import evaluate_gold
from builder.template_runner import main


class EvalTemplatesTest(unittest.TestCase):
    def test_gold_objectives_write_an_audience_only_for_known_intents(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            failures = evaluate_gold(Path(directory))
        self.assertEqual(failures, [])

    def test_command_writes_nothing_for_an_unknown_intent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "audience.json"
            code = main(["unknown intent", "--out", str(destination)])
            self.assertEqual(code, 2)
            self.assertFalse(destination.exists())
            self.assertEqual(list(Path(directory).iterdir()), [])


if __name__ == "__main__":
    unittest.main()
