from __future__ import annotations

import json
import subprocess
import sys
import unittest


class MainXaiAcceptanceTest(unittest.TestCase):
    def run_ai(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-m", "ai", *args],
            capture_output=True,
            text=True,
            timeout=20,
        )

    def test_main_legacy_mode_prints_expected_json_shape(self) -> None:
        completed = self.run_ai()

        self.assertEqual(completed.returncode, 0)
        data = json.loads(completed.stdout.strip())

        self.assertEqual(set(data.keys()), {"source", "item_count"})

    def test_main_xai_mode_includes_schema_and_explanations(self) -> None:
        completed = self.run_ai("--xai", "--top-k", "2")

        self.assertEqual(completed.returncode, 0)
        data = json.loads(completed.stdout.strip())

        self.assertIn("schema_version", data)
        self.assertIn("explanations", data)
        self.assertIsInstance(data["explanations"], list)

    def test_main_rejects_negative_top_k_with_argparse_error(self) -> None:
        completed = self.run_ai("--top-k", "-1")

        self.assertEqual(completed.returncode, 2)
        self.assertTrue("--top-k" in completed.stderr or "must be > 0" in completed.stderr)


if __name__ == "__main__":
    unittest.main()
