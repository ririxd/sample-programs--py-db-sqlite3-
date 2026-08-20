import time
import tkinter as tk
from tkinter import messagebox

from auth_controller import InventoryAuthController

# Login Window Interface 

class LoginWindow:
    def __init__(self, root, app_manager):
        self.root = root
        self.app_manager = app_manager
        self.controller = InventoryAuthController()
        self.lockout_end_time = None
        self.lockout_update_job = None

        self.root.title("Secure Inventory System - Authentication")
        self.root.geometry("390x260")
        self.root.resizable(False, False)

        self.mode_var = tk.StringVar(value="login")
        self.login_frame = tk.Frame(root)
        self.register_frame = tk.Frame(root)
        self.lockout_frame = tk.Frame(root, bg="#fff3f3")

        self.build_login_view()
        self.build_register_view()
        self.build_lockout_view()
        self.show_login_view()

    def build_login_view(self):
        tk.Label(self.login_frame, text="Campus Hardware Inventory Security Login", font=("Arial", 12, "bold")).pack(pady=(18, 10))

        tk.Label(self.login_frame, text="Username").pack(anchor="w", padx=24)
        self.entry_user = tk.Entry(self.login_frame, width=36)
        self.entry_user.pack(padx=24, pady=(0, 8))

        tk.Label(self.login_frame, text="Password").pack(anchor="w", padx=24)
        self.entry_pass = tk.Entry(self.login_frame, show="*", width=36)
        self.entry_pass.pack(padx=24, pady=(0, 5))

        self.show_password_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            self.login_frame,
            text="Show Password",
            variable=self.show_password_var,
            command=self.toggle_login_password_visibility,
        ).pack(anchor="w", padx=24, pady=(0, 10))

        self.lockout_label = tk.Label(self.login_frame, text="", fg="red", font=("Arial", 10, "bold"))
        self.lockout_label.pack(anchor="w", padx=24, pady=(0, 8))

        btn_frame = tk.Frame(self.login_frame)
        btn_frame.pack()
        self.login_button = tk.Button(btn_frame, text="Login", width=12, command=self.handle_login, bg="#4CAF50", fg="white")
        self.login_button.pack(side=tk.LEFT, padx=5)
        self.register_button = tk.Button(btn_frame, text="Register", width=12, command=self.show_register_view, bg="#2196F3", fg="white")
        self.register_button.pack(side=tk.LEFT, padx=5)

    def build_register_view(self):
        tk.Label(self.register_frame, text="Create Account", font=("Arial", 12, "bold")).pack(pady=(18, 10))

        tk.Label(self.register_frame, text="Username").pack(anchor="w", padx=24)
        self.reg_entry_user = tk.Entry(self.register_frame, width=36)
        self.reg_entry_user.pack(padx=24, pady=(0, 8))

        tk.Label(self.register_frame, text="Email").pack(anchor="w", padx=24)
        self.reg_entry_email = tk.Entry(self.register_frame, width=36)
        self.reg_entry_email.pack(padx=24, pady=(0, 8))

        tk.Label(self.register_frame, text="Password").pack(anchor="w", padx=24)
        self.reg_entry_pass = tk.Entry(self.register_frame, show="*", width=36)
        self.reg_entry_pass.pack(padx=24, pady=(0, 5))

        self.reg_show_password_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            self.register_frame,
            text="Show Password",
            variable=self.reg_show_password_var,
            command=self.toggle_register_password_visibility,
        ).pack(anchor="w", padx=24, pady=(0, 10))

        btn_frame = tk.Frame(self.register_frame)
        btn_frame.pack()
        tk.Button(btn_frame, text="Register", width=12, command=self.handle_register, bg="#2196F3", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Back to Login", width=12, command=self.show_login_view, bg="#d9534f", fg="white").pack(side=tk.LEFT, padx=5)

    def build_lockout_view(self):
        tk.Label(self.lockout_frame, text="Security Lockout", font=("Arial", 14, "bold"), fg="#a94442", bg="#fff3f3").pack(pady=(18, 10))
        tk.Label(self.lockout_frame, text="Too many failed login attempts.", font=("Arial", 10), bg="#fff3f3").pack()
        self.lockout_countdown_label = tk.Label(self.lockout_frame, text="", font=("Arial", 12, "bold"), fg="#b22222", bg="#fff3f3")
        self.lockout_countdown_label.pack(pady=(8, 12))
        tk.Button(self.lockout_frame, text="Back to Login", command=self.show_login_view, width=18, bg="#d9534f", fg="white").pack()

    def show_login_view(self):
        self.register_frame.pack_forget()
        self.lockout_frame.pack_forget()
        self.login_frame.pack(fill="both", expand=True)
        self.mode_var.set("login")
        self._refresh_lockout_state()

    def show_register_view(self):
        self.login_frame.pack_forget()
        self.lockout_frame.pack_forget()
        self.register_frame.pack(fill="both", expand=True)
        self.mode_var.set("register")

    def show_lockout_view(self):
        self.login_frame.pack_forget()
        self.register_frame.pack_forget()
        self.lockout_frame.pack(fill="both", expand=True)
        self.mode_var.set("lockout")

    def _set_login_controls_state(self, enabled):
        state = tk.NORMAL if enabled else tk.DISABLED
        self.entry_user.config(state=state)
        self.entry_pass.config(state=state)
        self.login_button.config(state=state)
        self.register_button.config(state=state)

    def _refresh_lockout_state(self):
        if self.lockout_end_time is None:
            remaining = self.controller.get_lockout_remaining(self.entry_user.get().strip() or "")
            if remaining > 0:
                self.lockout_end_time = time.time() + remaining
                self._start_lockout_countdown()
            else:
                self.lockout_label.config(text="")
                self._set_login_controls_state(True)
            return

        self._start_lockout_countdown()

    def _start_lockout_countdown(self):
        if self.lockout_update_job is not None:
            self.root.after_cancel(self.lockout_update_job)
            self.lockout_update_job = None

        if self.lockout_end_time is None:
            self.lockout_label.config(text="")
            self.lockout_countdown_label.config(text="")
            self._set_login_controls_state(True)
            return

        remaining = max(0, int(self.lockout_end_time - time.time()))
        if remaining > 0:
            self._set_login_controls_state(False)
            self.lockout_label.config(text=f"Login locked. Try again in {remaining} seconds.")
            self.lockout_countdown_label.config(text=f"Lockout ends in {remaining}s")
            self.show_lockout_view()
            self.lockout_update_job = self.root.after(1000, self._start_lockout_countdown)
        else:
            self.lockout_end_time = None
            self.lockout_label.config(text="")
            self.lockout_countdown_label.config(text="")
            self._set_login_controls_state(True)
            self.show_login_view()

    def start_lockout_timer(self, username):
        self.lockout_end_time = time.time() + 30
        self._start_lockout_countdown()

    def handle_login(self):
        username = self.entry_user.get().strip()
        password = self.entry_pass.get().strip()
        remaining = self.controller.get_lockout_remaining(username)
        if remaining > 0:
            self.lockout_end_time = time.time() + remaining
            self._start_lockout_countdown()
            messagebox.showerror("Login Failed", "Too many failed attempts. Please try again in 30 seconds.")
            return

        success, message = self.controller.login_user(username, password)

        if success:
            self.lockout_end_time = None
            self.lockout_label.config(text="")
            self.lockout_countdown_label.config(text="")
            self._set_login_controls_state(True)
            self.show_login_view()
            self.app_manager.show_main()
        else:
            if "Too many failed attempts" in message:
                self.start_lockout_timer(username)
            messagebox.showerror("Login Failed", message)

    def toggle_login_password_visibility(self):
        if self.show_password_var.get():
            self.entry_pass.config(show="")
        else:
            self.entry_pass.config(show="*")

    def toggle_register_password_visibility(self):
        if self.reg_show_password_var.get():
            self.reg_entry_pass.config(show="")
        else:
            self.reg_entry_pass.config(show="*")

    def handle_register(self):
        username = self.reg_entry_user.get().strip()
        email = self.reg_entry_email.get().strip()
        password = self.reg_entry_pass.get().strip()
        success, message = self.controller.register_user(username, password, email)

        if success:
            messagebox.showinfo("Registration Successful", message)
            self.show_login_view()
            self.reg_entry_user.delete(0, tk.END)
            self.reg_entry_email.delete(0, tk.END)
            self.reg_entry_pass.delete(0, tk.END)
            self.reg_show_password_var.set(False)
            self.reg_entry_pass.config(show="*")
        else:
            messagebox.showerror("Registration Error", message)
