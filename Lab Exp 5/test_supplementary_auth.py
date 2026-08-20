import os
import sqlite3
import sys
from pathlib import Path

import auth_controller

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from Main import InventoryAuthController, compute_status

# Authorization and authentication tests for the Inventory Management System


def test_login_and_registration_flow(tmp_path):
    db_path = tmp_path / "hardware_inventory.db"
    controller = InventoryAuthController(str(db_path))

    ok, message = controller.register_user("admin", "Secure123!", "admin@example.com")
    assert ok is True, message

    ok, message = controller.login_user("admin", "Secure123!")
    assert ok is True, message

    ok, message = controller.login_user("admin", "Wrongpass1!")
    assert ok is False, message


def test_duplicate_email_is_rejected(tmp_path):
    db_path = tmp_path / "hardware_inventory.db"
    controller = InventoryAuthController(str(db_path))

    ok, message = controller.register_user("admin", "Secure123!", "admin@example.com")
    assert ok is True, message

    ok, message = controller.register_user("anotheruser", "Secure123!", "admin@example.com")
    assert ok is False, message
    assert "Email already registered, please use a different email." in message


def test_login_lockout_after_three_failed_attempts(tmp_path):
    db_path = tmp_path / "hardware_inventory.db"
    controller = InventoryAuthController(str(db_path))

    controller.register_user("admin", "Secure123!", "admin@example.com")

    for attempt in ["Wrongpass1!", "Wrongpass2!", "Wrongpass3!"]:
        ok, message = controller.login_user("admin", attempt)
        assert ok is False, message

    ok, message = controller.login_user("admin", "Secure123!")
    assert ok is False, message
    assert "30 seconds" in message

    ok, message = controller.login_user("admin", "Secure123!")
    assert ok is False, message
    assert "30 seconds" in message


def test_lockout_expires_and_resets_attempts(tmp_path, monkeypatch):
    db_path = tmp_path / "hardware_inventory.db"
    controller = InventoryAuthController(str(db_path))
    controller.register_user("admin", "Secure123!", "admin@example.com")

    fake_now = 1_700_000_000.0
    monkeypatch.setattr(auth_controller.time, "time", lambda: fake_now)

    for attempt in ["Wrongpass1!", "Wrongpass2!", "Wrongpass3!"]:
        ok, message = controller.login_user("admin", attempt)
        assert ok is False, message

    ok, message = controller.login_user("admin", "Secure123!")
    assert ok is False, message
    assert "30 seconds" in message

    monkeypatch.setattr(auth_controller.time, "time", lambda: fake_now + 31)
    ok, message = controller.login_user("admin", "Secure123!")
    assert ok is True, message


def test_status_calculation_and_inventory_total(tmp_path):
    db_path = tmp_path / "hardware_inventory.db"
    controller = InventoryAuthController(str(db_path))
    controller.ensure_database()

    assert compute_status(0) == "Out of Stock"
    assert compute_status(3) == "Low Stock"
    assert compute_status(7) == "In Stock"

    controller.add_inventory_item("Router", "Network", 4, 250.0)
    controller.add_inventory_item("Switch", "Network", 2, 120.0)

    with sqlite3.connect(db_path) as conn:
        total = conn.execute("SELECT SUM(quantity * unit_price) FROM hardware").fetchone()[0]

    assert total == 1240.0
