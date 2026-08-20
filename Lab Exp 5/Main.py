import tkinter as tk

from controller import AppManager


def main():
    root = tk.Tk()
    AppManager(root)
    root.mainloop()


if __name__ == "__main__":
    main()


from auth_controller import InventoryAuthController, compute_status

__all__ = ["InventoryAuthController", "compute_status", "main"]
