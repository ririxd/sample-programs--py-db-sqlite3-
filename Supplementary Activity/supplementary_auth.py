import csv
import hashlib
import logging
import os
import sqlite3
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, ttk


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
        logger.info("Database initialized successfully at %s", self.db_name)

    def _hash_password(self, password, salt=None):
        if salt is None:
            salt = os.urandom(16)
        derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200000)
        return salt.hex(), derived.hex()

    def register_user(self, username, password):
        username = (username or "").strip()
        password = (password or "").strip()

        if not username or not password:
            logger.warning("Registration failed: username/password empty")
            return False, "Username and password are required."

        if len(password) < 6:
            logger.warning("Registration failed: weak password for user '%s'", username)
            return False, "Password must be at least 6 characters long."

        salt, password_hash = self._hash_password(password)
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, password_hash, salt) VALUES (?, ?, ?)",
                (username, password_hash, salt),
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

        stored_hash, stored_salt = row
        _, computed_hash = self._hash_password(password, bytes.fromhex(stored_salt))

        if stored_hash == computed_hash:
            logger.info("Authentication success: user '%s' logged in.", username)
            return True, "Login successful."

        logger.warning("Authentication attempt failed: incorrect password for '%s'", username)
        return False, "Invalid username or password."

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


class AppManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Campus Hardware & Component Inventory Log")
        self.root.geometry("1180x720")
        self.root.resizable(True, True)
        self.auth = InventoryAuthController()
        self.show_login()

    def show_login(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        LoginWindow(self.root, self)

    def show_main(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        InventoryMainWindow(self.root, self)


class LoginWindow:
    def __init__(self, root, app_manager):
        self.root = root
        self.app_manager = app_manager
        self.controller = InventoryAuthController()

        self.root.title("Secure Inventory System - Authentication")
        self.root.geometry("360x230")

        tk.Label(root, text="Campus Hardware Inventory Security Login", font=("Arial", 12, "bold")).pack(pady=(18, 10))

        tk.Label(root, text="Username").pack(anchor="w", padx=24)
        self.entry_user = tk.Entry(root, width=36)
        self.entry_user.pack(padx=24, pady=(0, 8))

        tk.Label(root, text="Password").pack(anchor="w", padx=24)
        self.entry_pass = tk.Entry(root, show="*", width=36)
        self.entry_pass.pack(padx=24, pady=(0, 12))

        btn_frame = tk.Frame(root)
        btn_frame.pack()
        tk.Button(btn_frame, text="Login", width=12, command=self.handle_login, bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Register", width=12, command=self.handle_register, bg="#2196F3", fg="white").pack(side=tk.LEFT, padx=5)

    def handle_login(self):
        username = self.entry_user.get().strip()
        password = self.entry_pass.get().strip()
        success, message = self.controller.login_user(username, password)

        if success:
            logger.info("User '%s' accessed the inventory dashboard.", username)
            self.app_manager.show_main()
        else:
            logger.warning("Login denied for '%s': %s", username, message)
            messagebox.showerror("Login Failed", message)

    def handle_register(self):
        username = self.entry_user.get().strip()
        password = self.entry_pass.get().strip()
        success, message = self.controller.register_user(username, password)

        if success:
            logger.info("User '%s' completed registration.", username)
            messagebox.showinfo("Registration Successful", message)
        else:
            logger.warning("Registration failed: %s", message)
            messagebox.showerror("Registration Error", message)


class InventoryMainWindow:
    def __init__(self, root, app_manager):
        self.root = root
        self.app_manager = app_manager
        self.controller = InventoryAuthController()
        self.selected_item_id = None

        self.root.title("Campus Hardware & Component Inventory Log")
        self.root.geometry("1180x720")

        header = tk.Frame(self.root, bg="#1f3a5f", padx=16, pady=12)
        header.pack(fill="x")
        tk.Label(header, text="Campus Hardware & Component Inventory Log", fg="white", bg="#1f3a5f", font=("Arial", 15, "bold")).pack(anchor="w")

        self.total_label = tk.Label(header, text="Total Asset Value: ₱0.00", fg="white", bg="#1f3a5f", font=("Arial", 12, "bold"))
        self.total_label.pack(anchor="e")

        logout_button = tk.Button(header, text="Logout", bg="#d9534f", fg="white", font=("Arial", 10, "bold"), command=self.logout)
        logout_button.pack(anchor="e", pady=(8, 0))

        form_frame = tk.LabelFrame(self.root, text="Add Inventory Item", padx=12, pady=12)
        form_frame.pack(fill="x", padx=10, pady=(10, 5))

        tk.Label(form_frame, text="Item Name:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.entry_name = tk.Entry(form_frame, width=28)
        self.entry_name.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(form_frame, text="Category:").grid(row=0, column=2, sticky="e", padx=5, pady=5)
        self.entry_category = tk.Entry(form_frame, width=20)
        self.entry_category.grid(row=0, column=3, padx=5, pady=5)

        tk.Label(form_frame, text="Quantity:").grid(row=0, column=4, sticky="e", padx=5, pady=5)
        self.entry_quantity = tk.Entry(form_frame, width=10)
        self.entry_quantity.grid(row=0, column=5, padx=5, pady=5)

        tk.Label(form_frame, text="Unit Price (Php):").grid(row=0, column=6, sticky="e", padx=5, pady=5)
        self.entry_price = tk.Entry(form_frame, width=12)
        self.entry_price.grid(row=0, column=7, padx=5, pady=5)

        tk.Button(form_frame, text="Save Item", command=self.save_item, bg="#5cb85c", fg="white", width=16, font=("Arial", 10, "bold")).grid(
            row=1, column=0, columnspan=4, sticky="ew", pady=(10, 0), padx=(0, 5)
        )
        tk.Button(form_frame, text="Refresh", command=self.refresh_inventory, bg="#ff9800", fg="white", width=16, font=("Arial", 10, "bold")).grid(
            row=1, column=4, columnspan=2, sticky="ew", pady=(10, 0), padx=(0, 5)
        )
        export_button = tk.Button(form_frame, text="Export Inventory to CSV Report", command=self.export_inventory, bg="#337ab7", fg="white", width=26, font=("Arial", 10, "bold"))
        export_button.grid(row=2, column=0, columnspan=8, sticky="ew", pady=(8, 0))

        columns = ("item_id", "item_name", "category", "quantity", "unit_price", "status")
        self.tree = ttk.Treeview(self.root, columns=columns, show="headings", height=14)
        self.tree.heading("item_id", text="ID")
        self.tree.heading("item_name", text="Name")
        self.tree.heading("category", text="Category")
        self.tree.heading("quantity", text="Qty")
        self.tree.heading("unit_price", text="Price (Php)")
        self.tree.heading("status", text="Status")

        for col in columns:
            self.tree.column(col, anchor="center", width=150)
        self.tree.column("item_id", width=60)
        self.tree.column("item_name", width=180)
        self.tree.column("category", width=160)
        self.tree.column("quantity", width=80)
        self.tree.column("unit_price", width=120)
        self.tree.column("status", width=130)

        self.tree.tag_configure("out_of_stock", background="#f8c6c6")
        self.tree.tag_configure("low_stock", background="#fff2a8")
        self.tree.tag_configure("in_stock", background="#c8f7c5")
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

        self.tree.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        update_frame = tk.LabelFrame(self.root, text="Update Selected Item", padx=12, pady=12)
        update_frame.pack(fill="x", padx=10, pady=(0, 10))

        tk.Label(update_frame, text="Item Name:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.update_name = tk.Entry(update_frame, width=28)
        self.update_name.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(update_frame, text="Category:").grid(row=0, column=2, sticky="e", padx=5, pady=5)
        self.update_category = tk.Entry(update_frame, width=20)
        self.update_category.grid(row=0, column=3, padx=5, pady=5)

        tk.Label(update_frame, text="Quantity:").grid(row=0, column=4, sticky="e", padx=5, pady=5)
        self.update_quantity = tk.Entry(update_frame, width=10)
        self.update_quantity.grid(row=0, column=5, padx=5, pady=5)

        tk.Label(update_frame, text="Price (Php):").grid(row=0, column=6, sticky="e", padx=5, pady=5)
        self.update_price = tk.Entry(update_frame, width=12)
        self.update_price.grid(row=0, column=7, padx=5, pady=5)

        tk.Button(update_frame, text="Update Selected", command=self.update_selected_item, bg="#2196F3", fg="white", width=16).grid(row=1, column=6, columnspan=2, padx=5, pady=(6, 10), sticky="ew")
        tk.Button(update_frame, text="Delete Selected", command=self.delete_selected_item, bg="#d9534f", fg="white", width=16).grid(row=2, column=6, columnspan=2, padx=5, pady=(0, 10), sticky="ew")

        self.refresh_inventory()

    def on_tree_select(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        values = self.tree.item(selected[0], "values")
        if not values:
            return
        self.selected_item_id = values[0]
        self.update_name.delete(0, tk.END)
        self.update_name.insert(0, values[1])
        self.update_category.delete(0, tk.END)
        self.update_category.insert(0, values[2])
        self.update_quantity.delete(0, tk.END)
        self.update_quantity.insert(0, str(values[3]))
        self.update_price.delete(0, tk.END)
        self.update_price.insert(0, str(values[4]))

    def refresh_inventory(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        rows = self.controller.fetch_inventory()
        for item_id, item_name, category, quantity, unit_price, status in rows:
            stock_tag = "out_of_stock" if status == "Out of Stock" else "low_stock" if status == "Low Stock" else "in_stock"
            self.tree.insert(
                "",
                tk.END,
                values=(item_id, item_name, category, quantity, f"{unit_price:.2f}", status),
                tags=(stock_tag,),
            )

        total_value = self.controller.get_total_asset_value()
        self.total_label.config(text=f"Total Asset Value: ₱{total_value:,.2f}")
        self.root.update_idletasks()

    def save_item(self):
        item_name = self.entry_name.get().strip()
        category = self.entry_category.get().strip()
        quantity = self.entry_quantity.get().strip()
        unit_price = self.entry_price.get().strip()

        success, message = self.controller.add_inventory_item(item_name, category, quantity, unit_price)
        if success:
            self.entry_name.delete(0, tk.END)
            self.entry_category.delete(0, tk.END)
            self.entry_quantity.delete(0, tk.END)
            self.entry_price.delete(0, tk.END)
            logger.info("Inventory save success: %s", message)
            self.refresh_inventory()
            messagebox.showinfo("Success", message)
        else:
            logger.warning("Inventory save failure: %s", message)
            messagebox.showerror("Validation Error", message)

    def update_selected_item(self):
        if self.selected_item_id is None:
            messagebox.showwarning("Selection Required", "Please select an item from the table first.")
            return

        success, message = self.controller.update_inventory_item(
            self.selected_item_id,
            self.update_name.get(),
            self.update_category.get(),
            self.update_quantity.get(),
            self.update_price.get(),
            None,
        )

        if success:
            self.refresh_inventory()
            messagebox.showinfo("Success", message)
        else:
            messagebox.showerror("Update Failed", message)

    def delete_selected_item(self):
        if self.selected_item_id is None:
            messagebox.showwarning("Selection Required", "Please select an item from the table first.")
            return

        confirm = messagebox.askyesno("Confirm Delete", f"Delete item ID {self.selected_item_id}?")
        if not confirm:
            return

        success, message = self.controller.delete_inventory_item(self.selected_item_id)
        if success:
            self.selected_item_id = None
            self.update_name.delete(0, tk.END)
            self.update_category.delete(0, tk.END)
            self.update_quantity.delete(0, tk.END)
            self.update_price.delete(0, tk.END)
            self.refresh_inventory()
            messagebox.showinfo("Success", message)
        else:
            messagebox.showerror("Delete Failed", message)

    def export_inventory(self):
        try:
            exported_path = self.controller.export_inventory_csv(CSV_EXPORT_PATH)
            logger.info("CSV report exported successfully to %s", exported_path)
            messagebox.showinfo("Export Complete", f"Inventory report exported to {exported_path}")
        except Exception as exc:
            logger.exception("Failed to export report: %s", exc)
            messagebox.showerror("Export Failed", f"Unable to export inventory report: {exc}")

    def logout(self):
        logger.info("User logged out from the inventory dashboard.")
        self.app_manager.show_login()


def main():
    root = tk.Tk()
    AppManager(root)
    root.mainloop()


if __name__ == "__main__":
    main()
