import tkinter as tk

from LoginView import LoginWindow
from auth_controller import InventoryAuthController
from tracker_view import InventoryMainWindow

#  Inventory Management System Window

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
