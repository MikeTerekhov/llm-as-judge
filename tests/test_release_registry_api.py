import os
import tempfile
import unittest
from unittest.mock import patch
from fastapi import HTTPException
from api.release_registry import release_registry

class RegistryApiTests(unittest.TestCase):
    def test_disabled(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(HTTPException) as ctx:
                release_registry()
        self.assertEqual(ctx.exception.status_code, 404)

    def test_empty_registry(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(os.environ, {
                "AI_REGIMEN_ENABLE_RELEASE_REGISTRY_API": "true",
                "AI_REGIMEN_RELEASE_REGISTRY_DIR": directory}, clear=True):
                self.assertEqual(release_registry()["count"], 0)

    def test_invalid_filter(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(os.environ, {
                "AI_REGIMEN_ENABLE_RELEASE_REGISTRY_API": "true",
                "AI_REGIMEN_RELEASE_REGISTRY_DIR": directory}, clear=True):
                with self.assertRaises(HTTPException) as ctx:
                    release_registry(decision="unknown")
        self.assertEqual(ctx.exception.status_code, 422)

if __name__ == "__main__":
    unittest.main()
