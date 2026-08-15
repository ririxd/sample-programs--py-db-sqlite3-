import sys
import os

# Automatically add the project root directory to Python's import search path

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk
from database import init_db
from LoginView import LoginWindow
from tracker_view import TrackerWindow

def launch_main_app():
    """Wipes the login window and loads the main Lab Tracker GUI."""
    for widget in root.winfo_children():
        widget.destroy()
        TrackerWindow(root)

if __name__ == "__main__":
    init_db
    root =tk.Tk()
    app = LoginWindow(root, on_login_success=launch_main_app)
    root.mainloop()