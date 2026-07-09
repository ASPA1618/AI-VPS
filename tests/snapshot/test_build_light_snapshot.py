from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[2] / "ops" / "snapshot" / "build_light_snapshot.py"
SPEC = importlib.util.spec_from_file_location("build_light_snapshot", MODULE_PATH)
assert SPEC and SPEC.loader
snapshot = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(snapshot)


class RemoteNormalisationTests(unittest.TestCase):
    def test_ssh_remote_becomes_repository_slug(self) -> None:
        self.assertEqual(
            snapshot.normalise_remote("git@github.com:ASPA1618/AI-VPS.git"),
            "ASPA1618/AI-VPS",
        )

    def test_https_remote_becomes_repository_slug(self) -> None:
        self.assertEqual(
            snapshot.normalise_remote("https://github.com/ASPA1618/AI-VPS.git"),
            "ASPA1618/AI-VPS",
        )

    def test_invalid_remote_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            snapshot.normalise_remote("file:///home/user/private/repo")


class AllowlistTests(unittest.TestCase):
    def test_known_aggregate_keys_are_accepted(self) -> None:
        value = snapshot.allowlist(
            "business_aggregates",
            {"customer_count": 330, "vehicle_count": 1979},
        )
        self.assertEqual(value["customer_count"], 330)

    def test_unknown_aggregate_key_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            snapshot.allowlist("business_aggregates", {"customer_rows": []})


class PrivacyValidationTests(unittest.TestCase):
    def test_safe_snapshot_fragment_is_accepted(self) -> None:
        snapshot.validate(
            {
                "repo": {"repository": "ASPA1618/AI-VPS", "commit": "a" * 40},
                "business_aggregates": {"customer_count": 330},
            }
        )

    def test_email_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            snapshot.validate({"note": "contact@example.com"})

    def test_vin_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            snapshot.validate({"note": "WVWZZZ1JZXW000001"})

    def test_phone_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            snapshot.validate({"note": "+380 67 123 45 67"})

    def test_secret_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            snapshot.validate({"note": "ghp_123456789012345678901234567890"})

    def test_forbidden_key_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            snapshot.validate({"customer_email": "redacted"})


class FileWriteTests(unittest.TestCase):
    def test_unchanged_content_is_not_rewritten(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "current.json"
            self.assertTrue(snapshot.write_if_changed(path, b"{}\n"))
            self.assertFalse(snapshot.write_if_changed(path, b"{}\n"))
            self.assertTrue(snapshot.write_if_changed(path, b'{"v":1}\n'))


if __name__ == "__main__":
    unittest.main()
