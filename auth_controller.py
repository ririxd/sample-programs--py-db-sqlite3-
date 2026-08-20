import csv
import hashlib
import os
import re
import sqlite3
import time
from pathlib import Path

from database import CSV_EXPORT_PATH, DB_PATH, logger

# Security and validation patterns

PASSWORD_PATTERN = re.compile(r"^(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$")
EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


def validate_email(email):
    email = (email or "").strip().lower()
    if not email:
        return False, "Email is required."
    if not EMAIL_PATTERN.fullmatch(email):
        return False, "Please enter a valid email address."
    return True, email


def validate_password(password):
    password = (password or "").strip()
    if not PASSWORD_PATTERN.fullmatch(password):
        if len(password) < 8:
            return False, "Password must be at least 8 characters long."
        if not re.search(r"[A-Z]", password):
            return False, "Password must contain at least 1 uppercase letter."
        if not re.search(r"\d", password):
            return False, "Password must contain at least 1 numeric character."
        if not re.search(r"[^A-Za-z0-9]", password):
            return False, "Password must contain at least 1 special character."
        return False, "Password does not meet the required format."
    return True, "Registration successful."


def compute_status(quantity):
    if quantity > 5:
        return "In Stock"
    if 1 <= quantity <= 5:
        return "Low Stock"
    if quantity == 0:
        return "Out of Stock"
    raise ValueError("Quantity must be zero or greater.")


class InventoryAuthController:
    def __init__(self, db_name=None):
        self.db_name = str(db_name or DB_PATH)
        self.ensure_database()

    def ensure_database(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                email TEXT,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL
            )
            """
        )
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]
        if "email" not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN email TEXT")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users(email)")
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
        logger.info("Database initialized successfully at %s", self.db_name)

    def _hash_password(self, password, salt=None):
        if salt is None:
            salt = os.urandom(16)
        derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200000)
        return salt.hex(), derived.hex()

    def _email_exists(self, email):
        email = (email or "").strip().lower()
        if not email:
            return False
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM users WHERE LOWER(email) = LOWER(?) LIMIT 1", (email,))
        exists = cursor.fetchone() is not None
        conn.close()
        return exists

    def register_user(self, username, password, email=None):
        username = (username or "").strip()
        password = (password or "").strip()
        email = (email or "").strip()

        if not username or not password:
            logger.warning("Registration failed: username/password empty")
            return False, "Username and password are required."

        valid_email, normalized_email = validate_email(email)
        if not valid_email:
            logger.warning("Registration failed: invalid email for user '%s' - %s", username, normalized_email)
            return False, normalized_email

        if self._email_exists(normalized_email):
            logger.warning("Registration failed: duplicate email '%s' for user '%s'", normalized_email, username)
            return False, "Email already registered, please use a different email."

        valid, message = validate_password(password)
        if not valid:
            logger.warning("Registration failed: weak password for user '%s' - %s", username, message)
            return False, message

        salt, password_hash = self._hash_password(password)
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, email, password_hash, salt) VALUES (?, ?, ?, ?)",
                (username, normalized_email, password_hash, salt),
            )
            conn.commit()
            conn.close()
            logger.info("Authentication attempt: user '%s' registered successfully.", username)
            return True, "Registration successful."
        except sqlite3.IntegrityError:
            logger.warning("Authentication attempt: registration failed because user '%s' already exists.", username)
            return False, "Username already exists."

    def login_user(self, username, password):
        username = (username or "").strip()
        password = (password or "").strip()

        if not username or not password:
            logger.warning("Authentication attempt: login failed because credentials were empty.")
            return False, "Username and password are required."

        valid, message = validate_password(password)
        if not valid:
            logger.warning("Authentication attempt failed: invalid password format for '%s' - %s", username, message)
            return False, message

        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT password_hash, salt FROM users WHERE username = ?",
            (username,),
        )
        row = cursor.fetchone()
        conn.close()

        if row is None:
            logger.warning("Authentication attempt failed: unknown user '%s'", username)
            return False, "Invalid username or password."

        lockout_key = f"lockout:{username.lower()}"
        lockout_until = self._read_lockout(lockout_key)
        if lockout_until:
            if time.time() >= lockout_until:
                self._reset_failed_attempts(username)
                logger.info("Authentication lockout expired for '%s'; failed attempts reset.", username)
            else:
                remaining = max(0, int(lockout_until - time.time()))
                logger.warning("Authentication blocked for '%s' for %s seconds due to repeated failed logins.", username, remaining)
                return False, "Too many failed attempts. Please try again in 30 seconds."

        stored_hash, stored_salt = row
        _, computed_hash = self._hash_password(password, bytes.fromhex(stored_salt))

        if stored_hash == computed_hash:
            self._reset_failed_attempts(username)
            logger.info("Authentication success: user '%s' logged in.", username)
            return True, "Login successful."

        failed, message = self._record_failed_attempt(username)
        logger.warning("Authentication attempt failed: incorrect password for '%s'", username)
        if failed:
            return False, message
        return False, "Invalid username or password."

    def get_lockout_remaining(self, username):
        username_key = f"lockout:{(username or '').strip().lower()}"
        lockout_until = self._read_lockout(username_key)
        if lockout_until is None:
            return 0
        remaining = int(lockout_until - time.time())
        return max(0, remaining)

    def _read_lockout(self, username_key):
        try:
            with open(os.path.join(os.path.dirname(self.db_name), "login_lockouts.txt"), "r", encoding="utf-8") as lock_file:
                for line in lock_file:
                    if not line.strip():
                        continue
                    key, value = line.strip().split("|", 1)
                    if key == username_key:
                        return float(value)
        except FileNotFoundError:
            return None
        return None

    def _write_lockout(self, username_key, timestamp):
        lockout_path = os.path.join(os.path.dirname(self.db_name), "login_lockouts.txt")
        entries = {}
        try:
            with open(lockout_path, "r", encoding="utf-8") as lock_file:
                for line in lock_file:
                    if not line.strip():
                        continue
                    key, value = line.strip().split("|", 1)
                    entries[key] = value
        except FileNotFoundError:
            entries = {}

        entries[username_key] = str(timestamp)
        with open(lockout_path, "w", encoding="utf-8") as lock_file:
            for key, value in entries.items():
                lock_file.write(f"{key}|{value}\n")

    def _clear_lockout(self, username_key):
        lockout_path = os.path.join(os.path.dirname(self.db_name), "login_lockouts.txt")
        entries = {}
        try:
            with open(lockout_path, "r", encoding="utf-8") as lock_file:
                for line in lock_file:
                    if not line.strip():
                        continue
                    key, value = line.strip().split("|", 1)
                    if key != username_key:
                        entries[key] = value
        except FileNotFoundError:
            return

        with open(lockout_path, "w", encoding="utf-8") as lock_file:
            for key, value in entries.items():
                lock_file.write(f"{key}|{value}\n")

    def _record_failed_attempt(self, username):
        username_key = f"failed:{username.lower()}"
        attempts_path = os.path.join(os.path.dirname(self.db_name), "login_attempts.txt")
        attempts = {}
        try:
            with open(attempts_path, "r", encoding="utf-8") as attempts_file:
                for line in attempts_file:
                    if not line.strip():
                        continue
                    key, value = line.strip().split("|", 1)
                    attempts[key] = float(value)
        except FileNotFoundError:
            attempts = {}

        count = attempts.get(username_key, 0)
        count += 1
        attempts[username_key] = count

        if count >= 3:
            lockout_until = time.time() + 30
            self._write_lockout(f"lockout:{username.lower()}", lockout_until)
            logger.warning("User '%s' locked out for 30 seconds after %s failed login attempts.", username, count)
            with open(attempts_path, "w", encoding="utf-8") as attempts_file:
                for key, value in attempts.items():
                    attempts_file.write(f"{key}|{value}\n")
            return True, "Too many failed attempts. Please try again in 30 seconds."

        with open(attempts_path, "w", encoding="utf-8") as attempts_file:
            for key, value in attempts.items():
                attempts_file.write(f"{key}|{value}\n")
        return False, "Invalid username or password."

    def _reset_failed_attempts(self, username):
        username_key = f"failed:{username.lower()}"
        attempts_path = os.path.join(os.path.dirname(self.db_name), "login_attempts.txt")
        try:
            with open(attempts_path, "r", encoding="utf-8") as attempts_file:
                entries = {}
                for line in attempts_file:
                    if not line.strip():
                        continue
                    key, value = line.strip().split("|", 1)
                    if key != username_key:
                        entries[key] = value
        except FileNotFoundError:
            entries = {}

        with open(attempts_path, "w", encoding="utf-8") as attempts_file:
            for key, value in entries.items():
                attempts_file.write(f"{key}|{value}\n")

        self._clear_lockout(f"lockout:{username.lower()}")

    def _item_name_exists(self, item_name, exclude_item_id=None):
        item_name = (item_name or "").strip()
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        if exclude_item_id is None:
            cursor.execute("SELECT 1 FROM hardware WHERE LOWER(item_name) = LOWER(?) LIMIT 1", (item_name,))
        else:
            cursor.execute(
                "SELECT 1 FROM hardware WHERE LOWER(item_name) = LOWER(?) AND item_id != ? LIMIT 1",
                (item_name, int(exclude_item_id)),
            )
        exists = cursor.fetchone() is not None
        conn.close()
        return exists

    def add_inventory_item(self, item_name, category, quantity, unit_price):
        item_name = (item_name or "").strip()
        category = (category or "").strip()

        if not item_name or not category:
            logger.warning("Validation failure: item name/category required.")
            return False, "Item name and category are required."

        if self._item_name_exists(item_name):
            logger.warning("Duplicate inventory item name prevented: '%s'", item_name)
            return False, f"Item '{item_name}' already exists in the inventory."

        try:
            quantity_int = int(quantity)
            unit_price_value = float(unit_price)
        except (TypeError, ValueError):
            logger.warning("Validation failure: quantity/price must be numeric.")
            return False, "Quantity and unit price must be valid numbers."

        if quantity_int < 0:
            logger.warning("Validation failure: quantity cannot be negative for '%s'.", item_name)
            return False, "Quantity cannot be negative."

        if unit_price_value < 0:
            logger.warning("Validation failure: unit price cannot be negative for '%s'.", item_name)
            return False, "Unit price cannot be negative."

        try:
            status = compute_status(quantity_int)
        except ValueError as exc:
            logger.warning("Validation failure: %s", exc)
            return False, str(exc)

        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO hardware (item_name, category, quantity, unit_price, status)
            VALUES (?, ?, ?, ?, ?)
            """,
            (item_name, category, quantity_int, unit_price_value, status),
        )
        conn.commit()
        conn.close()
        logger.info(
            "Inventory item saved: %s (%s), qty=%s, price=%s, status=%s",
            item_name,
            category,
            quantity_int,
            unit_price_value,
            status,
        )
        return True, "Item saved successfully."

    def update_inventory_item(self, item_id, item_name, category, quantity, unit_price, status=None):
        item_name = (item_name or "").strip()
        category = (category or "").strip()

        if not item_name or not category:
            logger.warning("Validation failure: item name/category required for ID %s.", item_id)
            return False, "Item name and category are required."

        if self._item_name_exists(item_name, exclude_item_id=item_id):
            logger.warning("Duplicate inventory item name prevented during update: '%s'", item_name)
            return False, f"Item '{item_name}' already exists in the inventory."

        try:
            item_id_int = int(item_id)
            quantity_int = int(quantity)
            unit_price_value = float(unit_price)
        except (TypeError, ValueError):
            logger.warning("Validation failure: item ID, quantity, or price is invalid for ID %s.", item_id)
            return False, "Item ID, quantity, and unit price must be valid numbers."

        if item_id_int <= 0:
            return False, "Valid item ID is required."
        if quantity_int < 0:
            return False, "Quantity cannot be negative."
        if unit_price_value < 0:
            return False, "Unit price cannot be negative."

        final_status = compute_status(quantity_int)

        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE hardware
            SET item_name = ?, category = ?, quantity = ?, unit_price = ?, status = ?
            WHERE item_id = ?
            """,
            (item_name, category, quantity_int, unit_price_value, final_status, item_id_int),
        )
        conn.commit()
        conn.close()
        logger.info(
            "Inventory item updated: ID %s, %s (%s), qty=%s, price=%s, status=%s",
            item_id_int,
            item_name,
            category,
            quantity_int,
            unit_price_value,
            final_status,
        )
        return True, "Item updated successfully."

    def delete_inventory_item(self, item_id):
        try:
            item_id_int = int(item_id)
        except (TypeError, ValueError):
            return False, "A valid item ID is required."

        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM hardware WHERE item_id = ?", (item_id_int,))
        conn.commit()
        conn.close()
        logger.info("Inventory item deleted: ID %s", item_id_int)
        return True, "Item deleted successfully."

    def fetch_inventory(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT item_id, item_name, category, quantity, unit_price, status FROM hardware ORDER BY item_id"
        )
        rows = cursor.fetchall()
        conn.close()
        return rows

    def get_total_asset_value(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT COALESCE(SUM(quantity * unit_price), 0) FROM hardware")
        total = cursor.fetchone()[0] or 0
        conn.close()
        return float(total)

    def export_inventory_csv(self, csv_path=None):
        target = Path(csv_path or CSV_EXPORT_PATH)
        rows = self.fetch_inventory()
        with target.open("w", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(["item_id", "item_name", "category", "quantity", "unit_price", "status"])
            writer.writerows(rows)

        logger.info("Inventory report generated at %s", target)
        return str(target)
