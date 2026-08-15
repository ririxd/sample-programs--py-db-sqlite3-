import tkinter as tk
from tkinter import ttk, messagebox
from controller import TrackerController

class TrackerWindow:
    def __init__(self, root):
        self.root = root
        self.controller = TrackerController()

        self.root.title("Student Lab Experiment Tracker")
        self.root.geometry("600x550")

        frame_form = tk.LabelFrame(self.root, text ="Add New Experiment", padx=10, pady=10)
        frame_form.pack(fill="x", padx=10, pady=5)

        tk.Label(frame_form, text="Title:").grid(row=0, column=0, sticky="e")
        self.entry_title = tk.Entry(frame_form, width=25)
        self.entry_title.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(frame_form, text="Student ID:").grid(row=1, column=0, sticky="e")
        self.entry_student_id = tk.Entry(frame_form, width=15)
        self.entry_student_id.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(frame_form, text="Status:").grid(row=1, column=2, sticky="e")
        self.combo_status = ttk.Combobox(frame_form, values=["Pending", "In Progress", "Completed"], state="readonly", width=18)
        self.combo_status.current(0)
        self.combo_status.grid(row=1, column=3, padx=5, pady=5)

        btn_add = tk.Button(frame_form, text="Save Experiment", command=self.add_experiment, bg="#4CAF50", fg="white")
        btn_add.grid(row=2, column=0, columnspan=4, padx=5, pady=10, sticky="ew")

        frame_table = tk.Frame(self.root)
        frame_table.pack(fill="both", expand=True, padx=10, pady=5)

        scroll_y = tk.Scrollbar(frame_table, orient=tk.VERTICAL)
        self.tree = ttk.Treeview(frame_table, columns=("ID", "Title", "Student ID", "Status"), show="headings", yscrollcommand=scroll_y.set)
        scroll_y.config(command=self.tree.yview)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.heading("ID", text="ID")
        self.tree.heading("Title", text=" Experiment Title")
        self.tree.heading("Student ID", text="Student ID")
        self.tree.heading("Status", text="Status")

        self.tree.column("ID", width=40, anchor="center")
        self.tree.column("Title", width=250)
        self.tree.column("Student ID", width=1200, anchor="center")
        self.tree.column("Status", width=100, anchor="center")
        self.tree.pack(fill="both", expand=True)

        frame_update = tk.LabelFrame(self.root, text ="Update Experiment Status", padx=10, pady=5)
        frame_update.pack(fill="x", padx=10, pady=5)

        tk.Label(frame_update, text="New Status:").grid(row=0, column=0, padx=5)
        self.combo_update_status = ttk.Combobox(frame_update, values=["Pending", "In Progress", "Completed"], state="readonly", width=18)
        self.combo_status.current(0)
        self.combo_update_status.grid(row=0, column=1, padx=5, pady=5)

        btn_update = tk.Button(frame_update, text="Update Status", command=self.update_experiment_status, bg="2196F3", fg="white")
        btn_update.grid(row=0, column=2, padx=10, pady=5)

        self.load_data()
        self.auto_refresh()

    def add_experiment(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        rows = self.controller.fetch_all_experiments()
        for row in rows:
            self.tree.insert("", tk.END, values=row)

    def add_experiments(self):
        title = self.entry_title.get().strip()
        student_id = self.entry_student_id.get().strip()
        status = self.combo_status.get()

        success, msg = self.controller.add_experiment(title, student_id, status)
        if success:
            messagebox.showinfo("Success", msg)
            self.entry_title.delete(0, tk.END)
            self.entry_student.delete(0, tk.END)
            self.combo_status.current(0)
            self.load_data()
        else:
            messagebox.showerror("Error", msg)
    def update_status(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select an experiment to update!")
            return

        exp_id = self.tree.item(selected[0])["values"][0]
        new_status = self.combo_update_status.get()

        success, msg = self.controller.update_experiment_status(exp_id, new_status)
        if success:
            messagebox.showinfo("Success", msg)
            self.load_data()
        else:
            messagebox.showerror("Error", msg)

    def delete_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select an experiment to delete!")
            return

        exp_id = self.tree.item(selected[0])["values"][0]
        confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete experiment ID {exp_id}?")
        if confirm:
            success, msg = self.controller.delete_experiment(exp_id)
            if success:
                messagebox.showinfo("Success", msg)
                self.load_data()
            else:
                messagebox.showerror("Error", msg)

    def auto_refresh(self):
       """Periodically relaods database data every 2 seconds for real-time polling sync"""
       self.load_data()
       self.root.after(2000, self.auto_refresh)
       