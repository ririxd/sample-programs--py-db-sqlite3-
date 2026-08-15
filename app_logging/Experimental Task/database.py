import os
import sqlite3
from pathlib import Path

from utils.logger import logger


PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_DB_PATH = PROJECT_ROOT / "lab_tracker.db"


def init_db(db_name=None):
    db_path = Path(db_name) if db_name else DEFAULT_DB_PATH
    db_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS experiments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                student_id TEXT NOT NULL,
                status TEXT NOT NULL
            )
            """
        )

        conn.commit()
        conn.close()
        logger.info("Database initialized successfully at %s", db_path)
        return str(db_path)
    except sqlite3.Error as exc:
        logger.error("Error initializing database: %s", exc)
        raise
