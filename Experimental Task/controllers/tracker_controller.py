import sqlite3

from pydantic import ValidationError

from database import DEFAULT_DB_PATH
from models.schemas import ExperimentSchema
from utils.logger import logger


class TrackerController:
    def __init__(self, db_name=DEFAULT_DB_PATH):
        self.db_name = db_name
        self.logger = logger

    def fetch_all_experiments(self):
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute("SELECT id, title, student_id, status FROM experiments ORDER BY id")
            rows = cursor.fetchall()
            conn.close()
            return rows
        except sqlite3.Error as exc:
            self.logger.error("Failed to fetch records %s", exc)
            return []

    def add_experiment(self, title, student_id, status):
        try:
            validated = ExperimentSchema(title=title, student_id=student_id, status=status)
        except ValidationError as exc:
            error = exc.errors()[0]
            field_name = error.get("loc", ["field"])[0]
            msg = f"{field_name.capitalize()} {error['msg']}"
            self.logger.warning("Add Experiment validation failed: %s", msg)
            return False, f"Validation Error: {msg}"

        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO experiments (title, student_id, status) VALUES (?, ?, ?)",
                (validated.title, validated.student_id, validated.status),
            )
            conn.commit()
            conn.close()
            self.logger.info("Experiment added: '%s'", validated.title)
            return True, "Experiment added successfully!"
        except sqlite3.Error as exc:
            self.logger.error("Error adding experiment: %s", exc)
            return False, "Database insertion failed."

    def update_status(self, exp_id, new_status):
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute("UPDATE experiments SET status = ? WHERE id = ?", (new_status, exp_id))
            conn.commit()
            conn.close()
            self.logger.info("Experiment ID %s updated to '%s'", exp_id, new_status)
            return True, f"Status updated to '{new_status}'!"
        except sqlite3.Error as exc:
            self.logger.error("Error updating status: %s", exc)
            return False, "Failed to update status."

    def delete_experiment(self, exp_id):
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM experiments WHERE id = ?", (exp_id,))
            conn.commit()
            conn.close()
            self.logger.info("Experiment ID %s deleted.", exp_id)
            return True, "Record deleted successfully!"
        except sqlite3.Error as exc:
            self.logger.error("Error deleting record: %s", exc)
            return False, "Failed to delete record."
