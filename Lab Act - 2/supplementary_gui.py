import tkinter as tk

from app import InventoryApp


if __name__ == "__main__":
    root = tk.Tk()
    app = InventoryApp(root)
    app.run()
