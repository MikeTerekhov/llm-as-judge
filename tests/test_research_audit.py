import json
import tempfile
import unittest
from pathlib import Path
from clinical.research_audit import append_audit, read_audit, audit_summary

DIGEST = "a"*64

class AuditTests(unittest.TestCase):
    def test_empty_log(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(read_audit(Path(directory)/"events.jsonl"), ())

    def test_chained_events(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"events.jsonl"
            first = append_audit(path, event_type="manifest_registered", release_id="r1",
                                 artifact_sha256=DIGEST)
            second = append_audit(path, event_type="evaluation_changed", release_id="r1",
                                  artifact_sha256=DIGEST)
            self.assertEqual(second["previous_sha256"], first["event_sha256"])
            self.assertEqual(len(read_audit(path)), 2)

    def test_detect_tampering(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"events.jsonl"
            append_audit(path, event_type="manifest_registered", release_id="r1",
                         artifact_sha256=DIGEST)
            path.write_text(path.read_text().replace('"r1"', '"r2"'))
            with self.assertRaises(ValueError):
                read_audit(path)

    def test_detect_deleted_middle_event(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"events.jsonl"
            for _ in range(3):
                append_audit(path, event_type="evaluation_changed", release_id="r1",
                             artifact_sha256=DIGEST)
            lines = path.read_text().splitlines()
            path.write_text(lines[0]+"\n"+lines[2]+"\n")
            with self.assertRaises(ValueError):
                read_audit(path)

    def test_invalid_event_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                append_audit(Path(directory)/"events.jsonl", event_type="deploy",
                             release_id="r1", artifact_sha256=DIGEST)

    def test_invalid_digest_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                append_audit(Path(directory)/"events.jsonl", event_type="manifest_registered",
                             release_id="r1", artifact_sha256="bad")

    def test_filter(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"events.jsonl"
            for release in ("r1", "r2"):
                append_audit(path, event_type="manifest_registered", release_id=release,
                             artifact_sha256=DIGEST)
            summary = audit_summary(path, release_id="r1")
            self.assertEqual(summary["total_events"], 2)
            self.assertEqual(summary["matched_events"], 1)

if __name__ == "__main__":
    unittest.main()
