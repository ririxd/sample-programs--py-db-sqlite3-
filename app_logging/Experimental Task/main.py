import os
import sys
import tkinter as tk

from database import init_db
from views.login_view import LoginWindow
from views.tracker_view import TrackerWindow


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)


def launch_main_app(root):
    """Clear the login window and load the main Lab Tracker GUI."""
    for widget in root.winfo_children():
        widget.destroy()
    TrackerWindow(root)


if __name__ == "__main__":
    db_path = init_db()
    root = tk.Tk()
    LoginWindow(root, on_login_success=lambda: launch_main_app(root))
    root.mainloop()
