import tkinter as tk

import database
from controllers import AuthController, InventoryController
from views import AuthView, DashboardView


class InventoryApp:
    def __init__(self, root: tk.Tk) -> None:
        root.title("Campus Hardware Inventory")
        root.geometry("760x600")
        root.resizable(False, False)

        database.init_db()

        self.auth_view = AuthView(root)
        self.dashboard_view = DashboardView(root)
        self.dashboard_view.hide()

        self.auth_controller = AuthController(self.auth_view, self._show_dashboard)
        self.inventory_controller = InventoryController(self.dashboard_view, self._show_auth)

    def _show_dashboard(self, username: str) -> None:
        self.auth_view.hide()
        self.dashboard_view.set_user_label(username)
        self.dashboard_view.show()

    def _show_auth(self) -> None:
        self.dashboard_view.hide()
        self.auth_view.show()

    def run(self) -> None:
        self.auth_view.show()
        self.auth_controller.view.show()
        self.dashboard_view.hide()
        self.auth_view.frame.master.mainloop()
