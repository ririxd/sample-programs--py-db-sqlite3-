from pathlib import Path
import sqlite3
from typing import Dict, List, Optional

DB_FILE = Path(__file__).resolve().parent / "hardware_inventory.db"


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_FILE)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS hardware (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL,
            category TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            status TEXT NOT NULL
        )
        """
    )
    cursor.execute("PRAGMA table_info(hardware)")
    columns = [row[1] for row in cursor.fetchall()]
    if "status" not in columns and "Pstatus" in columns:
        cursor.execute("ALTER TABLE hardware RENAME COLUMN Pstatus TO status")
    connection.commit()
    connection.close()


def create_user(username: str, password_hash: str) -> None:
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, password_hash),
        )
        connection.commit()


def find_user_by_username(username: str) -> Optional[Dict[str, str]]:
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT user_id, username, password_hash FROM users WHERE username = ?",
            (username,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return dict(row)


def user_exists(username: str) -> bool:
    return find_user_by_username(username) is not None


def hardware_exists(item_name: str) -> bool:
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT COUNT(1) FROM hardware WHERE LOWER(item_name) = ?",
            (item_name.strip().lower(),),
        )
        return cursor.fetchone()[0] > 0


def add_hardware(item_name: str, category: str, quantity: int, unit_price: float, status: str) -> None:
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO hardware (item_name, category, quantity, unit_price, status) VALUES (?, ?, ?, ?, ?)",
            (item_name, category, quantity, unit_price, status),
        )
        connection.commit()


def get_all_hardware() -> List[Dict[str, str]]:
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT item_id, item_name, category, quantity, unit_price, status FROM hardware ORDER BY item_id"
        )
        return [dict(row) for row in cursor.fetchall()]


def get_hardware_by_id(item_id: int) -> Optional[Dict[str, str]]:
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT item_id, item_name, category, quantity, unit_price, status FROM hardware WHERE item_id = ?",
            (item_id,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def update_hardware(item_id: int, quantity: int, unit_price: float, status: str) -> None:
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE hardware SET quantity = ?, unit_price = ?, status = ? WHERE item_id = ?",
            (quantity, unit_price, status, item_id),
        )
        connection.commit()


def delete_hardware(item_id: int) -> None:
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM hardware WHERE item_id = ?", (item_id,))
        connection.commit()
