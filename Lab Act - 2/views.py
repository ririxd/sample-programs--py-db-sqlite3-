import tkinter as tk
from tkinter import messagebox, ttk


class AuthView:
    def __init__(self, root: tk.Tk) -> None:
        self.frame = ttk.Frame(root, padding=16)
        self.frame.pack(fill="both", expand=True)

        title = ttk.Label(self.frame, text="Hardware Inventory Login", font=("Segoe UI", 16, "bold"))
        title.pack(pady=(0, 12))

        notebook = ttk.Notebook(self.frame)
        notebook.pack(fill="both", expand=True)

        login_tab = ttk.Frame(notebook, padding=12)
        register_tab = ttk.Frame(notebook, padding=12)
        notebook.add(login_tab, text="Login")
        notebook.add(register_tab, text="Register")

        self.login_username = self._build_labeled_entry(login_tab, "Username:")
        self.login_password = self._build_labeled_entry(login_tab, "Password:", show="*")
        self.login_button = ttk.Button(login_tab, text="Login", command=self._on_login)
        self.login_button.pack(fill="x", pady=(12, 0))

        self.register_username = self._build_labeled_entry(register_tab, "Username:")
        self.register_password = self._build_labeled_entry(register_tab, "Password:", show="*")
        self.register_button = ttk.Button(register_tab, text="Register", command=self._on_register)
        self.register_button.pack(fill="x", pady=(12, 0))

        self._login_callback = None
        self._register_callback = None

    def _build_labeled_entry(self, parent: ttk.Frame, label_text: str, show: str | None = None) -> ttk.Entry:
        frame = ttk.Frame(parent)
        frame.pack(fill="x", pady=4)
        label = ttk.Label(frame, text=label_text)
        label.pack(side="left")
        entry = ttk.Entry(frame, show=show)
        entry.pack(side="right", fill="x", expand=True)
        return entry

    def set_callbacks(self, login_callback, register_callback) -> None:
        self._login_callback = login_callback
        self._register_callback = register_callback

    def _on_login(self) -> None:
        if self._login_callback is None:
            return
        username = self.login_username.get().strip()
        password = self.login_password.get()
        self._login_callback(username, password)

    def _on_register(self) -> None:
        if self._register_callback is None:
            return
        username = self.register_username.get().strip()
        password = self.register_password.get()
        self._register_callback(username, password)

    def show_error(self, title: str, message: str) -> None:
        messagebox.showerror(title, message)

    def show_info(self, title: str, message: str) -> None:
        messagebox.showinfo(title, message)

    def clear_login_fields(self) -> None:
        self.login_username.delete(0, tk.END)
        self.login_password.delete(0, tk.END)

    def clear_register_fields(self) -> None:
        self.register_username.delete(0, tk.END)
        self.register_password.delete(0, tk.END)

    def hide(self) -> None:
        self.frame.pack_forget()

    def show(self) -> None:
        self.frame.pack(fill="both", expand=True)


class DashboardView:
    def __init__(self, root: tk.Tk) -> None:
        self.frame = ttk.Frame(root, padding=16)

        header = ttk.Frame(self.frame)
        header.pack(fill="x")
        self.user_label = ttk.Label(header, text="", font=("Segoe UI", 14, "bold"))
        self.user_label.pack(side="left")
        self.logout_button = ttk.Button(header, text="Logout", command=self._on_logout)
        self.logout_button.pack(side="right")

        add_frame = ttk.LabelFrame(self.frame, text="Add New Hardware Item", padding=12)
        add_frame.pack(fill="x", pady=(12, 10))
        self.entry_name = self._build_labeled_entry(add_frame, "Item Name:")
        self.entry_category = self._build_labeled_entry(add_frame, "Category:")
        self.entry_quantity = self._build_labeled_entry(add_frame, "Quantity:")
        self.entry_price = self._build_labeled_entry(add_frame, "Unit Price ($):")
        self.add_button = ttk.Button(add_frame, text="Save Item", command=self._on_add)
        self.add_button.pack(fill="x", pady=(8, 0))

        table_frame = ttk.Frame(self.frame)
        table_frame.pack(fill="both", expand=True)
        scroll_y = ttk.Scrollbar(table_frame, orient="vertical")
        scroll_x = ttk.Scrollbar(table_frame, orient="horizontal")
        self.tree = ttk.Treeview(
            table_frame,
            columns=("ID", "Name", "Category", "Qty", "Price", "Status"),
            show="headings",
            yscrollcommand=scroll_y.set,
            xscrollcommand=scroll_x.set,
            selectmode="browse",
        )
        scroll_y.config(command=self.tree.yview)
        scroll_x.config(command=self.tree.xview)
        scroll_y.pack(side="right", fill="y")
        scroll_x.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True)

        self._configure_columns()
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

        update_frame = ttk.LabelFrame(self.frame, text="Update Selected Item", padding=12)
        update_frame.pack(fill="x", pady=(10, 0))
        self.entry_update_quantity = self._build_labeled_entry(update_frame, "Quantity:")
        self.entry_update_price = self._build_labeled_entry(update_frame, "Unit Price ($):")
        buttons_frame = ttk.Frame(update_frame)
        buttons_frame.pack(fill="x", pady=(8, 0))
        self.update_button = ttk.Button(buttons_frame, text="Update Item", command=self._on_update)
        self.update_button.pack(side="left", fill="x", expand=True, padx=(0, 4))
        self.delete_button = ttk.Button(buttons_frame, text="Delete Selected Item", command=self._on_delete)
        self.delete_button.pack(side="left", fill="x", expand=True, padx=(4, 0))

        self._add_callback = None
        self._update_callback = None
        self._delete_callback = None
        self._logout_callback = None

    def _configure_columns(self) -> None:
        headings = [
            ("ID", 50, "center"),
            ("Name", 200, "w"),
            ("Category", 130, "center"),
            ("Qty", 80, "center"),
            ("Price", 100, "center"),
            ("Status", 120, "center"),
        ]
        for column, width, anchor in headings:
            self.tree.heading(column, text=column)
            self.tree.column(column, width=width, anchor=anchor)

    def _build_labeled_entry(self, parent: ttk.Frame, label_text: str, show: str | None = None) -> ttk.Entry:
        frame = ttk.Frame(parent)
        frame.pack(fill="x", pady=4)
        label = ttk.Label(frame, text=label_text)
        label.pack(side="left")
        entry = ttk.Entry(frame, show=show)
        entry.pack(side="right", fill="x", expand=True)
        return entry

    def bind_callbacks(self, add_callback, update_callback, delete_callback, logout_callback) -> None:
        self._add_callback = add_callback
        self._update_callback = update_callback
        self._delete_callback = delete_callback
        self._logout_callback = logout_callback

    def _on_add(self) -> None:
        if self._add_callback is None:
            return
        self._add_callback(
            self.entry_name.get().strip(),
            self.entry_category.get().strip(),
            self.entry_quantity.get().strip(),
            self.entry_price.get().strip(),
        )

    def _on_update(self) -> None:
        if self._update_callback is None:
            return
        item_id = self.get_selected_item_id()
        if item_id is None:
            self.show_error("No selection", "Please select a hardware item first.")
            return
        self._update_callback(
            item_id,
            self.entry_update_quantity.get().strip(),
            self.entry_update_price.get().strip(),
        )

    def _on_delete(self) -> None:
        if self._delete_callback is None:
            return
        item_id = self.get_selected_item_id()
        if item_id is None:
            self.show_error("No selection", "Please select a hardware item first.")
            return
        self._delete_callback(item_id)

    def _on_logout(self) -> None:
        if self._logout_callback is None:
            return
        self._logout_callback()

    def _on_tree_select(self, event: tk.Event) -> None:
        selected = self.tree.selection()
        if not selected:
            self.clear_update_fields()
            return
        values = self.tree.item(selected[0], "values")
        self.entry_update_quantity.delete(0, tk.END)
        self.entry_update_quantity.insert(0, values[3])
        self.entry_update_price.delete(0, tk.END)
        self.entry_update_price.insert(0, values[4])

    def set_user_label(self, username: str) -> None:
        self.user_label.config(text=f"Welcome, {username}")

    def get_selected_item_id(self) -> int | None:
        selected = self.tree.selection()
        if not selected:
            return None
        values = self.tree.item(selected[0], "values")
        try:
            return int(values[0])
        except (TypeError, ValueError):
            return None

    def populate_items(self, rows: list[dict]) -> None:
        for row in self.tree.get_children():
            self.tree.delete(row)
        for row in rows:
            self.tree.insert(
                "", "end",
                values=(row["item_id"], row["item_name"], row["category"], row["quantity"], f"{row['unit_price']:.2f}", row["status"]),
            )

    def clear_add_fields(self) -> None:
        self.entry_name.delete(0, tk.END)
        self.entry_category.delete(0, tk.END)
        self.entry_quantity.delete(0, tk.END)
        self.entry_price.delete(0, tk.END)

    def clear_update_fields(self) -> None:
        self.entry_update_quantity.delete(0, tk.END)
        self.entry_update_price.delete(0, tk.END)

    def show_error(self, title: str, message: str) -> None:
        messagebox.showerror(title, message)

    def show_info(self, title: str, message: str) -> None:
        messagebox.showinfo(title, message)

    def hide(self) -> None:
        self.frame.pack_forget()

    def show(self) -> None:
        self.frame.pack(fill="both", expand=True)
