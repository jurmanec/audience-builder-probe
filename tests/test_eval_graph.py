"""Gold-set run of the graph path. Run: python -m unittest tests.test_eval_graph"""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from eval.graph import evaluate_graph
from builder.graph_runner import main


class EvalGraphTest(unittest.TestCase):
    def test_scripted_graph_cases_write_files_only_after_success(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            failures = evaluate_graph(Path(directory))
        self.assertEqual(failures, [])

    def test_command_writes_nothing_when_the_api_key_is_missing(self) -> None:
        with patch.dict(os.environ, {"XAI_API_KEY": ""}), tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "audience.json"
            code = main(
                [
                    "Month-to-month households with at least a year of tenure and recent support contact.",
                    "--out",
                    str(destination),
                ]
            )
            self.assertEqual(code, 2)
            self.assertFalse(destination.exists())
            self.assertEqual(list(Path(directory).iterdir()), [])


if __name__ == "__main__":
    unittest.main()
