import sqlite3
from logger import  logger
from Schemas import ExperimentSchema
from pydantic import ValidationError

class TrackerController:
    def __init__(self, db_name="lab_tracker.db"):
        self.db_name = db_name
        self.logger = logger

    def fetch_all_experiments(self):
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute("SELECT id, title, student_id, status FROM experiments")
            rows = cursor.fetchall()
            conn.close()
            return rows
        except sqlite3.Error as e:
            self.logger.error(f"Failed to fetch records {e}")
            return []

    def add_experiment(self, title, student_id, status):
        try:
            validated = ExperimentSchema(title=title, student_id=student_id, status=status)
        except ValidationError as e:
            msg = e.errors()[0]['msg']
            self.logger.warning(f"Add Experiment validation failed: {msg}")
            return False, f"Validation Error: {msg}"

        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO experiments (title, student_id, status) VALUES (?, ?, ?)",
                (validated.title, validated.student_id, validated.status)
            )
            conn.commit()
            conn.close()
            self.logger.info(f"Experiment added: '{validated.title}'")
            return True, "Experiment added successfully!"
        except sqlite3.Error as e:
            self.logger.error(f"Error adding experiment: {e}")
            return False, "Database Insertion failed."

    def update_status(self, exp_id, new_status):
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute("UPDATE experiments SET status = ? WHERE id = ?", (new_status, exp_id))
            conn.commit()
            conn.close()
            self.logger.info(f"Experiment ID {exp_id} updated to '{new_status}'")
            return True, f"Status updated to '{new_status}'!"
        except sqlite3.Error as e:
            self.logger.error(f"Error updating status:{e}")
            return False, "Failed to update status."
    def delete_experiment(self, exp_id):
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM experiments WHERE id = ?", (exp_id,))
            conn.commit()
            conn.close()
            self.logger.info(f"Experiment ID {exp_id} deleted.")
            return True, "Record deleted successfully!"
        except sqlite3.Error as e:
            self.logger.error(f"Error deleting record: {e}")
            return False, "Failed to delete record."


        
        
           
        