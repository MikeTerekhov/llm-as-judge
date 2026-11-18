import copy
import json
import tempfile
import unittest
from pathlib import Path
from clinical.release_manifest import build_manifest
from clinical.release_registry import add_manifest, list_manifests
from scripts.verify_evaluation_ci import generate

SHA = "a"*40

class ReleaseRegistryTests(unittest.TestCase):
    def manifest(self):
        return build_manifest(generate(), None, commit_sha=SHA)

    def test_add_and_list(self):
        with tempfile.TemporaryDirectory() as root:
            add_manifest(root, "release_001", self.manifest())
            result = list_manifests(root)
            self.assertEqual(result["count"], 1)
            self.assertEqual(result["releases"][0]["decision"], "pending")

    def test_duplicate_cannot_overwrite(self):
        with tempfile.TemporaryDirectory() as root:
            add_manifest(root, "release_001", self.manifest())
            with self.assertRaises(FileExistsError):
                add_manifest(root, "release_001", self.manifest())

    def test_filter_decision(self):
        with tempfile.TemporaryDirectory() as root:
            add_manifest(root, "release_001", self.manifest())
            self.assertEqual(list_manifests(root, decision="approved")["count"], 0)

    def test_filter_commit(self):
        with tempfile.TemporaryDirectory() as root:
            add_manifest(root, "release_001", self.manifest())
            self.assertEqual(list_manifests(root, commit_sha=SHA)["count"], 1)
            self.assertEqual(list_manifests(root, commit_sha="b"*40)["count"], 0)

    def test_reject_invalid_id(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(ValueError):
                add_manifest(root, "../outside", self.manifest())

    def test_reject_tampered_manifest(self):
        with tempfile.TemporaryDirectory() as root:
            manifest = copy.deepcopy(self.manifest())
            manifest["commit_sha"] = "b"*40
            with self.assertRaises(ValueError):
                add_manifest(root, "bad", manifest)

    def test_corrupt_registry_blocks_listing(self):
        with tempfile.TemporaryDirectory() as root:
            Path(root, "bad.json").write_text('{"invalid":true}', encoding="utf-8")
            with self.assertRaises(ValueError):
                list_manifests(root)

if __name__ == "__main__":
    unittest.main()
