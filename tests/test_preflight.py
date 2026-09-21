import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"


class PreflightTests(unittest.TestCase):
    def run_fixture(self, name: str) -> dict:
        completed = subprocess.run(
            [sys.executable, str(ROOT / "preflight.py"), str(FIXTURES / name)],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertIn(completed.returncode, (0, 1), completed.stderr)
        return json.loads(completed.stdout)

    def test_clean_file_is_pass(self):
        result = self.run_fixture("clean.musicxml")
        self.assertEqual(result["status"], "pass")
        self.assertEqual([check["status"] for check in result["checks"]], ["pass", "pass", "pass"])

    def test_unclosed_spanner_is_error(self):
        result = self.run_fixture("unclosed-slur.musicxml")
        check = next(item for item in result["checks"] if item["name"] == "paired-spanners")
        self.assertEqual(check["status"], "error")
        self.assertEqual(check["findings"][0]["code"], "paired-spanner-unclosed-start")

    def test_duration_mismatch_is_error(self):
        result = self.run_fixture("duration-mismatch.musicxml")
        check = next(item for item in result["checks"] if item["name"] == "measure-durations")
        self.assertEqual(check["status"], "error")
        self.assertEqual(check["findings"][0]["details"], {"actual": "3", "expected": "4"})

    def test_multiple_voices_are_unknown(self):
        result = self.run_fixture("multiple-voices.musicxml")
        check = next(item for item in result["checks"] if item["name"] == "measure-durations")
        self.assertEqual(check["status"], "unknown")

    def test_missing_jump_target_is_warning(self):
        result = self.run_fixture("missing-segno.musicxml")
        check = next(item for item in result["checks"] if item["name"] == "playback-jumps")
        self.assertEqual(check["status"], "warning")
        self.assertEqual(check["findings"][0]["code"], "playback-jump-target-missing")

    def test_output_is_deterministic(self):
        first = self.run_fixture("clean.musicxml")
        second = self.run_fixture("clean.musicxml")
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
