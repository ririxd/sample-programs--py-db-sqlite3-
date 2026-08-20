import tkinter as tk
from tkinter import messagebox, ttk

from auth_controller import InventoryAuthController
from database import CSV_EXPORT_PATH, logger

#Inventory Main Window Interface

class InventoryMainWindow:
    def __init__(self, root, app_manager):
        self.root = root
        self.app_manager = app_manager
        self.controller = InventoryAuthController()
        self.selected_item_id = None
        self.current_user = app_manager.current_user or {}

        self.root.title("Campus Hardware & Component Inventory Log")
        self.root.geometry("1280x800")
        self.root.minsize(1100, 700)
        self.root.resizable(True, True)

        header = tk.Frame(self.root, bg="#1f3a5f", padx=24, pady=18)
        header.pack(fill="x")
        tk.Label(header, text="Campus Hardware & Component Inventory Log", fg="white", bg="#1f3a5f", font=("Arial", 20, "bold")).pack(anchor="w")

        self.total_label = tk.Label(header, text="Total Asset Value: ₱0.00", fg="white", bg="#1f3a5f", font=("Arial", 15, "bold"))
        self.total_label.pack(anchor="e")

        logout_button = tk.Button(header, text="Logout", bg="#d9534f", fg="white", font=("Arial", 11, "bold"), height=1, padx=12, command=self.logout)
        logout_button.pack(anchor="e", pady=(8, 0))
        tk.Button(header, text="My Profile & Security", command=self.show_profile, height=1, padx=12, font=("Arial", 10, "bold")).pack(anchor="e", pady=(4, 0))
        if self.current_user.get("role") == "ADMIN":
            tk.Button(header, text="Admin Approvals", command=self.show_admin_approvals, height=1, padx=12, font=("Arial", 10, "bold")).pack(anchor="e", pady=(4, 0))
            tk.Button(header, text="System History", command=self.show_history, height=1, padx=12, font=("Arial", 10, "bold")).pack(anchor="e", pady=(4, 0))

        form_frame = tk.LabelFrame(self.root, text="Add Inventory Item", padx=18, pady=18)
        form_frame.pack(fill="x", padx=16, pady=(16, 8))

        tk.Label(form_frame, text="Item Name:", font=("Arial", 11)).grid(row=0, column=0, sticky="e", padx=6, pady=6)
        self.entry_name = tk.Entry(form_frame, width=34, font=("Arial", 12))
        self.entry_name.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(form_frame, text="Category:", font=("Arial", 11)).grid(row=0, column=2, sticky="e", padx=6, pady=6)
        self.entry_category = tk.Entry(form_frame, width=26, font=("Arial", 12))
        self.entry_category.grid(row=0, column=3, padx=5, pady=5)

        tk.Label(form_frame, text="Quantity:", font=("Arial", 11)).grid(row=0, column=4, sticky="e", padx=6, pady=6)
        self.entry_quantity = tk.Entry(form_frame, width=13, font=("Arial", 12))
        self.entry_quantity.grid(row=0, column=5, padx=5, pady=5)

        tk.Label(form_frame, text="Unit Price (Php):", font=("Arial", 11)).grid(row=0, column=6, sticky="e", padx=6, pady=6)
        self.entry_price = tk.Entry(form_frame, width=16, font=("Arial", 12))
        self.entry_price.grid(row=0, column=7, padx=5, pady=5)

        tk.Button(form_frame, text="Save Item", command=self.save_item, bg="#5cb85c", fg="white", width=15, height=1, font=("Arial", 11, "bold")).grid(
            row=1, column=0, columnspan=4, sticky="ew", pady=(10, 0), padx=(0, 5)
        )
        tk.Button(form_frame, text="Refresh", command=self.refresh_inventory, bg="#ff9800", fg="white", width=15, height=1, font=("Arial", 11, "bold")).grid(
            row=1, column=4, columnspan=2, sticky="ew", pady=(10, 0), padx=(0, 5)
        )
        export_button = tk.Button(form_frame, text="Export Inventory to CSV Report", command=self.export_inventory, bg="#337ab7", fg="white", width=27, height=1, font=("Arial", 11, "bold"))
        export_button.grid(row=2, column=0, columnspan=8, sticky="ew", pady=(8, 0))

        filter_frame = tk.Frame(self.root)
        filter_frame.pack(fill="x", padx=10, pady=(4, 4))
        tk.Label(filter_frame, text="Search:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        tk.Entry(filter_frame, textvariable=self.search_var, width=28).pack(side=tk.LEFT, padx=5)
        tk.Label(filter_frame, text="Category:").pack(side=tk.LEFT)
        self.category_var = tk.StringVar(value="All")
        self.category_menu = tk.OptionMenu(filter_frame, self.category_var, "All")
        self.category_menu.pack(side=tk.LEFT, padx=5)
        tk.Button(filter_frame, text="Apply Filter", command=self.refresh_inventory, width=12, height=1, font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=6)

        columns = ("item_id", "item_name", "category", "quantity", "unit_price", "status")
        self.tree = ttk.Treeview(self.root, columns=columns, show="headings", height=9)
        self.tree.heading("item_id", text="ID")
        self.tree.heading("item_name", text="Name")
        self.tree.heading("category", text="Category")
        self.tree.heading("quantity", text="Qty")
        self.tree.heading("unit_price", text="Price (Php)")
        self.tree.heading("status", text="Status")

        for col in columns:
            self.tree.column(col, anchor="center", width=190)
        self.tree.column("item_id", width=80)
        self.tree.column("item_name", width=240)
        self.tree.column("category", width=210)
        self.tree.column("quantity", width=110)
        self.tree.column("unit_price", width=160)
        self.tree.column("status", width=170)

        self.tree.tag_configure("out_of_stock", background="#f8c6c6")
        self.tree.tag_configure("low_stock", background="#fff2a8")
        self.tree.tag_configure("in_stock", background="#c8f7c5")
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

        self.tree.pack(fill="both", expand=False, padx=16, pady=(0, 10))

        update_frame = tk.LabelFrame(self.root, text="Update Selected Item", padx=18, pady=18)
        update_frame.pack(fill="x", padx=16, pady=(0, 16))

        tk.Label(update_frame, text="Item Name:", font=("Arial", 11)).grid(row=0, column=0, sticky="e", padx=6, pady=6)
        self.update_name = tk.Entry(update_frame, width=34, font=("Arial", 12))
        self.update_name.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(update_frame, text="Category:", font=("Arial", 11)).grid(row=0, column=2, sticky="e", padx=6, pady=6)
        self.update_category = tk.Entry(update_frame, width=26, font=("Arial", 12))
        self.update_category.grid(row=0, column=3, padx=5, pady=5)

        tk.Label(update_frame, text="Quantity:", font=("Arial", 11)).grid(row=0, column=4, sticky="e", padx=6, pady=6)
        self.update_quantity = tk.Entry(update_frame, width=13, font=("Arial", 12))
        self.update_quantity.grid(row=0, column=5, padx=5, pady=5)

        tk.Label(update_frame, text="Price (Php):", font=("Arial", 11)).grid(row=0, column=6, sticky="e", padx=6, pady=6)
        self.update_price = tk.Entry(update_frame, width=16, font=("Arial", 12))
        self.update_price.grid(row=0, column=7, padx=5, pady=5)

        tk.Button(update_frame, text="Update Selected", command=self.update_selected_item, bg="#2196F3", fg="white", width=16, height=1, font=("Arial", 11, "bold")).grid(row=1, column=6, columnspan=2, padx=5, pady=(6, 10), sticky="ew")
        tk.Button(update_frame, text="Delete Selected", command=self.delete_selected_item, bg="#d9534f", fg="white", width=16, height=1, font=("Arial", 11, "bold")).grid(row=2, column=6, columnspan=2, padx=5, pady=(0, 10), sticky="ew")

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

        categories = ["All"] + self.controller.get_categories()
        self.category_menu["menu"].delete(0, tk.END)
        for category in categories:
            self.category_menu["menu"].add_command(label=category, command=tk._setit(self.category_var, category))
        if self.category_var.get() not in categories:
            self.category_var.set("All")
        rows = self.controller.fetch_inventory(self.search_var.get(), self.category_var.get())
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
        self.app_manager.current_user = None
        self.app_manager.show_login()

    def show_profile(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("My Profile & Security")
        dialog.geometry("430x430")
        dialog.minsize(430, 430)
        user = self.controller.get_user(self.current_user.get("username")) or self.current_user
        tk.Label(dialog, text=f"Username: {user.get('username', '')}", font=("Arial", 12)).pack(anchor="w", padx=24, pady=7)
        tk.Label(dialog, text=f"Email: {user.get('email', '')}", font=("Arial", 12)).pack(anchor="w", padx=24, pady=7)
        tk.Label(dialog, text=f"Assigned Role: {user.get('role', '')}", font=("Arial", 12)).pack(anchor="w", padx=24, pady=7)
        old = tk.Entry(dialog, show="*", width=32, font=("Arial", 12)); new = tk.Entry(dialog, show="*", width=32, font=("Arial", 12))
        tk.Label(dialog, text="Current Password", font=("Arial", 11)).pack(anchor="w", padx=24, pady=(8, 2)); old.pack(padx=24)
        tk.Label(dialog, text="New Password", font=("Arial", 11)).pack(anchor="w", padx=24, pady=(10, 2)); new.pack(padx=24)
        def change():
            ok, message = self.controller.change_password(user["username"], old.get(), new.get())
            (messagebox.showinfo if ok else messagebox.showerror)("Password", message)
            if ok:
                dialog.destroy()
        tk.Button(dialog, text="Change Password", command=change, width=18, height=1, font=("Arial", 11, "bold")).pack(pady=12)

    def show_admin_approvals(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Admin Approvals")
        dialog.geometry("1000x520")
        dialog.minsize(850, 420)
        style = ttk.Style(dialog)
        style.configure("Treeview", font=("Arial", 11), rowheight=28)
        style.configure("Treeview.Heading", font=("Arial", 11, "bold"))
        tree = ttk.Treeview(dialog, columns=("id", "user", "email", "status", "requested"), show="headings")
        for column in tree["columns"]:
            tree.heading(column, text=column.title())
            tree.column(column, anchor="center", width=180)
        tree.column("id", width=70)
        tree.column("email", width=260)
        tree.column("requested", width=220)
        tree.pack(fill="both", expand=True, padx=12, pady=12)
        for row in self.controller.get_reset_requests():
            tree.insert("", tk.END, values=row[:5])
        buttons = tk.Frame(dialog); buttons.pack(pady=6)
        def review(approve):
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("Selection Required", "Select a reset request first.", parent=dialog)
                return
            request_id = tree.item(selected[0], "values")[0]
            ok, message = self.controller.approve_reset_request(request_id, self.current_user["username"], approve)
            (messagebox.showinfo if ok else messagebox.showerror)("Admin Approval", message, parent=dialog)
            if ok:
                dialog.destroy()
                self.show_admin_approvals()
        tk.Button(buttons, text="Approve", command=lambda: review(True), width=14, height=1, font=("Arial", 12, "bold"), bg="#5cb85c", fg="white").pack(side=tk.LEFT, padx=6)
        tk.Button(buttons, text="Reject", command=lambda: review(False), width=14, height=1, font=("Arial", 12, "bold"), bg="#d9534f", fg="white").pack(side=tk.LEFT, padx=6)

    def show_history(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("System History")
        text = tk.Text(dialog, width=100, height=24)
        text.pack(fill="both", expand=True, padx=10, pady=10)
        for created, username, action, details in self.controller.get_audit_log():
            text.insert(tk.END, f"{created} | {username or '-'} | {action} | {details}\n")
        text.config(state="disabled")
