import csv
import hashlib
import os
import re
import sqlite3
from pathlib import Path

from database import CSV_EXPORT_PATH, DB_PATH, logger

PASSWORD_PATTERN = re.compile(r"^(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$")
EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


class ManagedConnection(sqlite3.Connection):
    def __exit__(self, exc_type, exc_value, traceback):
        try:
            return super().__exit__(exc_type, exc_value, traceback)
        finally:
            self.close()


def validate_email(email):
    email = (email or "").strip().lower()
    if not email:
        return False, "Email is required."
    if not EMAIL_PATTERN.fullmatch(email):
        return False, "Please enter a valid email address."
    return True, email


def validate_password(password):
    password = password or ""
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
    return True, "Password is valid."


def compute_status(quantity):
    if quantity > 5:
        return "In Stock"
    if quantity >= 1:
        return "Low Stock"
    if quantity == 0:
        return "Out of Stock"
    raise ValueError("Quantity must be zero or greater.")


class InventoryAuthController:
    def __init__(self, db_name=None):
        self.db_name = str(db_name or DB_PATH)
        self.ensure_database()

    def _connect(self):
        conn = sqlite3.connect(self.db_name, factory=ManagedConnection)
        conn.row_factory = sqlite3.Row
        return conn

    def ensure_database(self):
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    email TEXT UNIQUE,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'USER',
                    failed_attempts INTEGER NOT NULL DEFAULT 0,
                    locked INTEGER NOT NULL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS hardware (
                    item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    quantity INTEGER NOT NULL CHECK(quantity >= 0),
                    unit_price REAL NOT NULL CHECK(unit_price >= 0),
                    status TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS password_reset_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    email TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'PENDING',
                    requested_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    reviewed_at TEXT,
                    reviewed_by TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                );
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT,
                    action TEXT NOT NULL,
                    details TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
            """)
            columns = {row[1] for row in conn.execute("PRAGMA table_info(users)")}
            for name, definition in (("role", "TEXT NOT NULL DEFAULT 'USER'"), ("failed_attempts", "INTEGER NOT NULL DEFAULT 0"), ("locked", "INTEGER NOT NULL DEFAULT 0")):
                if name not in columns:
                    conn.execute(f"ALTER TABLE users ADD COLUMN {name} {definition}")
        logger.info("Database initialized successfully at %s", self.db_name)

    def _audit(self, username, action, details=""):
        with self._connect() as conn:
            conn.execute("INSERT INTO audit_log (username, action, details) VALUES (?, ?, ?)", (username, action, details))
        logger.info("%s: %s", action, details)

    def _hash_password(self, password, salt=None):
        salt = salt or os.urandom(16)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200000)
        return salt.hex(), digest.hex()

    def _user(self, username):
        with self._connect() as conn:
            return conn.execute("SELECT * FROM users WHERE username = ?", ((username or "").strip(),)).fetchone()

    def register_user(self, username, password, email=None, role="USER"):
        username, email, role = (username or "").strip(), (email or "").strip().lower(), (role or "USER").strip().upper()
        if not username:
            return False, "Username is required."
        valid, message = validate_email(email)
        if not valid:
            return False, message
        valid, message = validate_password(password)
        if not valid:
            return False, message
        if role not in {"USER", "ADMIN"}:
            return False, "Role must be USER or ADMIN."
        salt, password_hash = self._hash_password(password)
        try:
            with self._connect() as conn:
                conn.execute("INSERT INTO users (username, email, password_hash, salt, role) VALUES (?, ?, ?, ?, ?)", (username, email, password_hash, salt, role))
            self._audit(username, "REGISTRATION", f"role={role}, email={email}")
            return True, "Registration successful."
        except sqlite3.IntegrityError as exc:
            return False, "Email already registered, please use a different email." if "email" in str(exc).lower() else "Username already exists."

    def login_user(self, username, password):
        username = (username or "").strip()
        user = self._user(username)
        if user is None:
            self._audit(username, "LOGIN_FAILED", "unknown user")
            return False, "Invalid username or password."
        if user["locked"]:
            self._audit(username, "LOGIN_BLOCKED", "account locked")
            return False, "Account is locked. Submit a password-reset request using your registered email."
        valid, message = validate_password(password)
        if not valid:
            return False, message
        _, computed = self._hash_password(password, bytes.fromhex(user["salt"]))
        if computed != user["password_hash"]:
            attempts = user["failed_attempts"] + 1
            locked = int(attempts >= 3)
            with self._connect() as conn:
                conn.execute("UPDATE users SET failed_attempts = ?, locked = ? WHERE id = ?", (attempts, locked, user["id"]))
            self._audit(username, "LOGIN_FAILED", f"attempt={attempts}")
            return False, "Account locked after three unsuccessful attempts. Submit a password-reset request." if locked else "Invalid username or password."
        with self._connect() as conn:
            conn.execute("UPDATE users SET failed_attempts = 0 WHERE id = ?", (user["id"],))
        self._audit(username, "LOGIN_SUCCESS", f"role={user['role']}")
        return True, "Login successful."

    def get_user(self, username):
        user = self._user(username)
        return dict(user) if user else None

    def is_account_locked(self, username):
        user = self._user(username)
        return bool(user and user["locked"])

    def request_password_reset(self, email):
        valid, normalized = validate_email(email)
        if not valid:
            return False, normalized
        with self._connect() as conn:
            user = conn.execute("SELECT id, username FROM users WHERE LOWER(email) = ?", (normalized,)).fetchone()
            if user is None:
                return False, "No account is registered with that email."
            if conn.execute("SELECT id FROM password_reset_requests WHERE user_id = ? AND status = 'PENDING'", (user["id"],)).fetchone():
                return False, "A password-reset request is already pending approval."
            conn.execute("INSERT INTO password_reset_requests (user_id, email) VALUES (?, ?)", (user["id"], normalized))
        self._audit(user["username"], "PASSWORD_RESET_REQUESTED", normalized)
        return True, "Password-reset request submitted for admin approval."

    request_reset = request_password_reset

    def get_reset_requests(self, status=None):
        query = "SELECT r.id, u.username, r.email, r.status, r.requested_at, r.reviewed_at, r.reviewed_by FROM password_reset_requests r JOIN users u ON u.id = r.user_id"
        params = ()
        if status:
            query += " WHERE r.status = ?"
            params = (status.upper(),)
        with self._connect() as conn:
            return [tuple(row) for row in conn.execute(query + " ORDER BY r.id DESC", params).fetchall()]

    def approve_reset_request(self, request_id, admin_username, approve=True):
        admin = self._user(admin_username)
        if not admin or admin["role"] != "ADMIN":
            return False, "Administrator access is required."
        status = "APPROVED" if approve else "REJECTED"
        with self._connect() as conn:
            request = conn.execute("SELECT user_id FROM password_reset_requests WHERE id = ? AND status = 'PENDING'", (int(request_id),)).fetchone()
            if not request:
                return False, "Pending reset request not found."
            conn.execute("UPDATE password_reset_requests SET status = ?, reviewed_at = CURRENT_TIMESTAMP, reviewed_by = ? WHERE id = ?", (status, admin_username, int(request_id)))
            if approve:
                conn.execute("UPDATE users SET locked = 0, failed_attempts = 0 WHERE id = ?", (request["user_id"],))
        self._audit(admin_username, "PASSWORD_RESET_REVIEWED", f"request={request_id}, status={status}")
        return True, f"Password-reset request {status.lower()}."

    approve_reset = approve_reset_request

    def change_password(self, username, current_password, new_password):
        user = self._user(username)
        if not user:
            return False, "User not found."
        _, computed = self._hash_password(current_password or "", bytes.fromhex(user["salt"]))
        if computed != user["password_hash"]:
            return False, "Current password is incorrect."
        valid, message = validate_password(new_password)
        if not valid:
            return False, message
        salt, password_hash = self._hash_password(new_password)
        with self._connect() as conn:
            conn.execute("UPDATE users SET password_hash = ?, salt = ? WHERE username = ?", (password_hash, salt, username))
        self._audit(username, "PASSWORD_CHANGED")
        return True, "Password changed successfully."

    def reset_password(self, username, new_password):
        valid, message = validate_password(new_password)
        if not valid:
            return False, message
        with self._connect() as conn:
            user = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
            approved = conn.execute("SELECT id FROM password_reset_requests WHERE user_id = ? AND status = 'APPROVED' ORDER BY id DESC LIMIT 1", (user["id"],)).fetchone() if user else None
            if not user or not approved:
                return False, "An approved password-reset request is required."
            salt, password_hash = self._hash_password(new_password)
            conn.execute("UPDATE users SET password_hash = ?, salt = ?, locked = 0, failed_attempts = 0 WHERE id = ?", (password_hash, salt, user["id"]))
        self._audit(username, "PASSWORD_RESET_COMPLETED")
        return True, "Password reset successfully."

    def add_inventory_item(self, item_name, category, quantity, unit_price):
        return self._save_inventory(None, item_name, category, quantity, unit_price)

    def update_inventory_item(self, item_id, item_name, category, quantity, unit_price, status=None):
        return self._save_inventory(item_id, item_name, category, quantity, unit_price)

    def _save_inventory(self, item_id, item_name, category, quantity, unit_price):
        item_name, category = (item_name or "").strip(), (category or "").strip()
        if not item_name or not category:
            return False, "Item name and category are required."
        try:
            quantity, unit_price = int(quantity), float(unit_price)
            if quantity < 0 or unit_price < 0:
                raise ValueError
            status = compute_status(quantity)
        except (TypeError, ValueError):
            return False, "Quantity and unit price must be valid non-negative numbers."
        with self._connect() as conn:
            duplicate = conn.execute("SELECT item_id FROM hardware WHERE LOWER(item_name) = LOWER(?) AND item_id != COALESCE(?, -1)", (item_name, item_id)).fetchone()
            if duplicate:
                return False, f"Item '{item_name}' already exists in the inventory."
            if item_id is None:
                conn.execute("INSERT INTO hardware (item_name, category, quantity, unit_price, status) VALUES (?, ?, ?, ?, ?)", (item_name, category, quantity, unit_price, status))
                message, action = "Item saved successfully.", "INVENTORY_ADDED"
            else:
                conn.execute("UPDATE hardware SET item_name = ?, category = ?, quantity = ?, unit_price = ?, status = ? WHERE item_id = ?", (item_name, category, quantity, unit_price, status, int(item_id)))
                message, action = "Item updated successfully.", "INVENTORY_UPDATED"
        self._audit(None, action, f"{item_name}, category={category}, quantity={quantity}, status={status}")
        return True, message

    def delete_inventory_item(self, item_id):
        with self._connect() as conn:
            conn.execute("DELETE FROM hardware WHERE item_id = ?", (int(item_id),))
        self._audit(None, "INVENTORY_DELETED", f"item_id={item_id}")
        return True, "Item deleted successfully."

    def fetch_inventory(self, search="", category="All"):
        query = "SELECT item_id, item_name, category, quantity, unit_price, status FROM hardware WHERE (item_name LIKE ? OR category LIKE ?)"
        params = (f"%{search}%", f"%{search}%")
        if category and category != "All":
            query += " AND category = ?"
            params += (category,)
        with self._connect() as conn:
            return [tuple(row) for row in conn.execute(query + " ORDER BY item_id", params).fetchall()]

    def get_categories(self):
        with self._connect() as conn:
            return [row[0] for row in conn.execute("SELECT DISTINCT category FROM hardware ORDER BY category")]

    def get_total_asset_value(self):
        with self._connect() as conn:
            return float(conn.execute("SELECT COALESCE(SUM(quantity * unit_price), 0) FROM hardware").fetchone()[0])

    def export_inventory_csv(self, csv_path=None):
        target = Path(csv_path or CSV_EXPORT_PATH)
        with target.open("w", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(["item_id", "item_name", "category", "quantity", "unit_price", "status"])
            writer.writerows(self.fetch_inventory())
        self._audit(None, "INVENTORY_EXPORTED", str(target))
        return str(target)

    def get_audit_log(self):
        with self._connect() as conn:
            return [tuple(row) for row in conn.execute("SELECT created_at, username, action, details FROM audit_log ORDER BY id DESC").fetchall()]
