import os
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from supplementary_auth import InventoryAuthController, compute_status


def test_login_and_registration_flow(tmp_path):
    db_path = tmp_path / "hardware_inventory.db"
    controller = InventoryAuthController(str(db_path))

    ok, message = controller.register_user("admin", "secure123")
    assert ok is True, message

    ok, message = controller.login_user("admin", "secure123")
    assert ok is True, message

    ok, message = controller.login_user("admin", "wrongpass")
    assert ok is False, message


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
