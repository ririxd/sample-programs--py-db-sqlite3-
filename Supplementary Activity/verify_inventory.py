import sqlite3
from pathlib import Path

from supplementary_auth import InventoryAuthController, compute_status


def main():
    db_path = Path(__file__).resolve().parent / "verification_inventory.db"
    if db_path.exists():
        db_path.unlink()

    controller = InventoryAuthController(str(db_path))
    assert compute_status(0) == "Out of Stock"
    assert compute_status(3) == "Low Stock"
    assert compute_status(7) == "In Stock"

    ok, msg = controller.register_user("admin", "secure123")
    assert ok, msg
    ok, msg = controller.login_user("admin", "secure123")
    assert ok, msg

    ok, msg = controller.add_inventory_item("Router", "Network", 4, 250.0)
    assert ok, msg
    ok, msg = controller.add_inventory_item("Switch", "Network", 2, 120.0)
    assert ok, msg

    with sqlite3.connect(db_path) as conn:
        total = conn.execute("SELECT SUM(quantity * unit_price) FROM hardware").fetchone()[0]
        row_count = conn.execute("SELECT COUNT(*) FROM hardware").fetchone()[0]

    assert total == 1240.0, total
    assert row_count == 2, row_count

    print("TOTAL", total)
    print("ROWS", row_count)
    print("VERIFIED")


if __name__ == "__main__":
    main()
