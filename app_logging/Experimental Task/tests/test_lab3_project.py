import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from controllers.auth_controller import AuthController
from controllers.tracker_controller import TrackerController
from database import init_db


class Lab3ProjectTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmpdir.name, "test_lab_tracker.db")
        init_db(self.db_path)
        self.auth = AuthController(self.db_path)
        self.tracker = TrackerController(self.db_path)

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_registration_hashes_password_and_allows_login(self):
        success, message = self.auth.register_user("Alice", "secret123")
        self.assertTrue(success)
        self.assertIn("registered", message.lower())

        success, message = self.auth.login_user("Alice", "secret123")
        self.assertTrue(success)
        self.assertIn("successful", message.lower())

        success, message = self.auth.login_user("Alice", "wrong")
        self.assertFalse(success)

    def test_tracker_validation_rejects_bad_input(self):
        success, message = self.tracker.add_experiment("A", "123", "Pending")
        self.assertFalse(success)
        self.assertIn("title", message.lower())

        success, message = self.tracker.add_experiment("Alpha", "1234", "Pending")
        self.assertTrue(success)
        self.assertIn("success", message.lower())


if __name__ == "__main__":
    unittest.main()
