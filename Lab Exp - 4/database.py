import logging
import sqlite3
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
LOG_DIR = APP_DIR / "app_logging"
LOG_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = APP_DIR / "hardware_inventory.db"
CSV_EXPORT_PATH = APP_DIR / "inventory_report.csv"
LOG_FILE = LOG_DIR / "app.log"

logger = logging.getLogger("supplementary_auth")
logger.setLevel(logging.INFO)
logger.propagate = False
if not logger.handlers:
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(file_handler)


def init_db(db_name=None):
    db_name = str(db_name or DB_PATH)
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS hardware (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL,
            category TEXT NOT NULL,
            quantity INTEGER NOT NULL CHECK(quantity >= 0),
            unit_price REAL NOT NULL CHECK(unit_price >= 0),
            status TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()
    logger.info("Database initialized successfully at %s", db_name)
