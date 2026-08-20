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
