import sqlite3
from logger import logger

def init_db(db_name = "lab_tracker.db"):
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        # 1. User Authetication Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS experiments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                student_id TEXT NOT NULL,
                status TEXT NOT NULL,
            )
        """)

        conn.commit
        conn.close()
        logger.info("Database initialized successfully.")
    except sqlite3.Error as e:
        logger.error(f"Error initializing database: {e}")
