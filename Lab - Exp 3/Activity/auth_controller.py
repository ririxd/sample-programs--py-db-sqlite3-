import sqlite3
import bcrypt
from logger import logger
from Schemas import UserRegisterSchema
from pydantic import ValidationError

class AuthController:
    def __init__(self, db_name="lab_tracker.db"):
        self.db_name = db_name

    def register_user(self, username, password):
        try:
            validated = UserRegisterSchema(username=username, password=password)
        except ValidationError as e:
            return False, f"Validation Error: {e.errors()[0]['msg']}"

        hashed_pw = bcrypt.hashpw(validated.password.encode ('utf-8'), bcrypt.gensalt())

        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", 
                           (validated.username, hashed_pw.decode('utf-8')))

            conn.commit()
            conn.close()
            logger.info(f"Account Created: '{validated.username}'")
            return True, "User registered successfully."
        except sqlite3.IntegrityError:
            return False, "Username already exists."

    def login_user(self, username, password):
        if not username or not password:
            return False, "Username and password cannot be empty."

        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        conn.close()

        if row and bcrypt.checkpw(password.encode('utf-8'), row[0].encode('utf-8')):
            logger.info(f"User Logged In: '{username}' logged in.")
            return True, "Login successful."
        else:
            return False, "Invalid username or password."
        