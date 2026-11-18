import copy
import tempfile
import unittest
from pathlib import Path
from clinical.evaluation_history import load_history, save_snapshot
from scripts.verify_evaluation_ci import generate

class EvaluationHistoryTests(unittest.TestCase):
    def test_empty_history(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(load_history(directory)["count"], 0)

    def test_two_identical_snapshots(self):
        with tempfile.TemporaryDirectory() as directory:
            report = generate()
            save_snapshot(directory, "001", report)
            save_snapshot(directory, "002", report)
            result = load_history(directory)
            self.assertEqual(result["count"], 2)
            self.assertEqual(result["snapshots"][1]["regression_status"], "pass")

    def test_no_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            save_snapshot(directory, "001", generate())
            with self.assertRaises(FileExistsError):
                save_snapshot(directory, "001", generate())

    def test_reject_tampered(self):
        with tempfile.TemporaryDirectory() as directory:
            report = copy.deepcopy(generate())
            report["fixture_count"] = 999
            with self.assertRaises(ValueError):
                save_snapshot(directory, "001", report)

    def test_reject_path_traversal(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                save_snapshot(directory, "../outside", generate())

    def test_reject_corrupted_file(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "001.json").write_text('{"invalid":true}', encoding="utf-8")
            with self.assertRaises(ValueError):
                load_history(directory)

if __name__ == "__main__":
    unittest.main()
