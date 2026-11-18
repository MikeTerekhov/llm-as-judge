import json
import tempfile
import unittest
from pathlib import Path
from clinical.audit_integrity import locked_append, checkpoint, verify_checkpoint

SHA = "a"*64

class AuditIntegrityTests(unittest.TestCase):
    def event(self, path, **kwargs):
        return locked_append(path, event_type="manifest_registered",
                             release_id="r1", artifact_sha256=SHA, **kwargs)

    def test_checkpoint_and_future_append(self):
        with tempfile.TemporaryDirectory() as root:
            log, cp = Path(root)/"audit.jsonl", Path(root)/"anchor.json"
            self.event(log)
            checkpoint(log, cp)
            self.event(log, checkpoint_path=cp)
            result = verify_checkpoint(log, cp)
            self.assertEqual(result["checkpoint_sequence"], 1)
            self.assertEqual(result["current_sequence"], 2)

    def test_checkpoint_cannot_overwrite(self):
        with tempfile.TemporaryDirectory() as root:
            log, cp = Path(root)/"audit.jsonl", Path(root)/"anchor.json"
            checkpoint(log, cp)
            with self.assertRaises(FileExistsError):
                checkpoint(log, cp)

    def test_truncation_detected(self):
        with tempfile.TemporaryDirectory() as root:
            log, cp = Path(root)/"audit.jsonl", Path(root)/"anchor.json"
            self.event(log)
            checkpoint(log, cp)
            log.write_text("")
            with self.assertRaises(ValueError):
                verify_checkpoint(log, cp)

    def test_rewritten_history_detected(self):
        with tempfile.TemporaryDirectory() as root:
            log, cp = Path(root)/"audit.jsonl", Path(root)/"anchor.json"
            self.event(log)
            checkpoint(log, cp)
            log.write_text("")
            self.event(log, recorded_at="2026-01-01T00:00:00+00:00")
            with self.assertRaises(ValueError):
                verify_checkpoint(log, cp)

    def test_tampered_checkpoint_detected(self):
        with tempfile.TemporaryDirectory() as root:
            log, cp = Path(root)/"audit.jsonl", Path(root)/"anchor.json"
            checkpoint(log, cp)
            data = json.loads(cp.read_text())
            data["sequence"] = 1
            cp.write_text(json.dumps(data))
            with self.assertRaises(ValueError):
                verify_checkpoint(log, cp)

    def test_locked_append_fails_on_truncated_history(self):
        with tempfile.TemporaryDirectory() as root:
            log, cp = Path(root)/"audit.jsonl", Path(root)/"anchor.json"
            self.event(log)
            checkpoint(log, cp)
            log.write_text("")
            with self.assertRaises(ValueError):
                self.event(log, checkpoint_path=cp)

    def test_empty_checkpoint(self):
        with tempfile.TemporaryDirectory() as root:
            log, cp = Path(root)/"audit.jsonl", Path(root)/"anchor.json"
            checkpoint(log, cp)
            self.assertEqual(verify_checkpoint(log, cp)["current_sequence"], 0)

if __name__ == "__main__":
    unittest.main()
