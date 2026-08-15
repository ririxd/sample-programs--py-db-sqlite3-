import tkinter as tk
from tkinter import ttk, messagebox

from controllers.tracker_controller import TrackerController


class TrackerWindow:
    def __init__(self, root):
        self.root = root
        self.controller = TrackerController()
        self.checked_state_by_id = {}
        self.checkbox_vars = {}
        self.checkbox_widgets = {}
        self.selected_experiment_id = None

        self.root.title("Student Lab Experiment Tracker")
        self.root.geometry("680x580")

        frame_form = tk.LabelFrame(self.root, text="Add New Experiment", padx=10, pady=10)
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

        tk.Button(frame_form, text="Save Experiment", command=self.add_experiment, bg="#4CAF50", fg="white").grid(
            row=2, column=0, columnspan=4, padx=5, pady=10, sticky="ew"
        )

        frame_table = tk.Frame(self.root)
        frame_table.pack(fill="both", expand=True, padx=10, pady=5)

        headings = tk.Frame(frame_table)
        headings.pack(fill="x")

        tk.Label(headings, text="Select", width=6, anchor="w", font=(None, 10, "bold")).grid(row=0, column=0, padx=2)
        tk.Label(headings, text="ID", width=4, anchor="center", font=(None, 10, "bold")).grid(row=0, column=1, padx=2)
        tk.Label(headings, text="Experiment Title", width=30, anchor="w", font=(None, 10, "bold")).grid(row=0, column=2, padx=2)
        tk.Label(headings, text="Student ID", width=15, anchor="center", font=(None, 10, "bold")).grid(row=0, column=3, padx=2)
        tk.Label(headings, text="Status", width=15, anchor="center", font=(None, 10, "bold")).grid(row=0, column=4, padx=2)

        canvas_frame = tk.Frame(frame_table)
        canvas_frame.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(canvas_frame, borderwidth=0)
        self.rows_container = tk.Frame(self.canvas)
        self.v_scroll = tk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.v_scroll.set)

        self.v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill="both", expand=True)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.rows_container, anchor="nw")

        self.rows_container.bind("<Configure>", lambda event: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda event: self.canvas.itemconfig(self.canvas_window, width=event.width))

        frame_update = tk.LabelFrame(self.root, text="Update Experiment Status", padx=10, pady=5)
        frame_update.pack(fill="x", padx=10, pady=5)

        tk.Label(frame_update, text="New Status:").grid(row=0, column=0, padx=5)
        self.combo_update_status = ttk.Combobox(frame_update, values=["Pending", "In Progress", "Completed"], state="readonly", width=18)
        self.combo_update_status.current(0)
        self.combo_update_status.grid(row=0, column=1, padx=5, pady=5)

        tk.Button(frame_update, text="Update Status", command=self.update_experiment_status, bg="#2196F3", fg="white").grid(
            row=0, column=2, padx=10, pady=5
        )
        tk.Button(frame_update, text="Delete Selected", command=self.delete_selected, bg="#F44336", fg="white").grid(
            row=0, column=3, padx=10, pady=5
        )

        self.load_data()
        self.auto_refresh()

    def load_data(self):
        for widget in self.rows_container.winfo_children():
            widget.destroy()
        self.checkbox_vars.clear()
        self.checkbox_widgets.clear()
        self.row_frames = {}

        rows = self.controller.fetch_all_experiments()
        for row in rows:
            exp_id = row[0]
            is_checked = self.checked_state_by_id.get(exp_id, False)

            row_frame = tk.Frame(self.rows_container, pady=2)
            row_frame.pack(fill="x", expand=True)

            var = tk.BooleanVar(value=is_checked)
            cb = tk.Checkbutton(row_frame, variable=var, command=lambda eid=exp_id: self.toggle_checkbox(eid))
            cb.pack(side="left", padx=2)

            tk.Label(row_frame, text=str(exp_id), width=4, anchor="center").pack(side="left", padx=2)
            tk.Label(row_frame, text=row[1], width=30, anchor="w").pack(side="left", padx=2)
            tk.Label(row_frame, text=row[2], width=15, anchor="center").pack(side="left", padx=2)
            tk.Label(row_frame, text=row[3], width=15, anchor="center").pack(side="left", padx=2)

            self.checkbox_vars[exp_id] = var
            self.checkbox_widgets[exp_id] = cb
            self.row_frames[exp_id] = row_frame

            if is_checked:
                self.highlight_row(exp_id)

    def highlight_row(self, exp_id):
        row_frame = self.row_frames.get(exp_id)
        if not row_frame:
            return
        row_frame.configure(bg="#d6ebff")
        for child in row_frame.winfo_children():
            child.configure(bg="#d6ebff")

    def unhighlight_row(self, exp_id):
        row_frame = self.row_frames.get(exp_id)
        if not row_frame:
            return
        default_bg = self.root.cget("bg")
        row_frame.configure(bg=default_bg)
        for child in row_frame.winfo_children():
            child.configure(bg=default_bg)

    def toggle_checkbox(self, exp_id):
        var = self.checkbox_vars.get(exp_id)
        if var is None:
            return

        is_checked = bool(var.get())
        self.checked_state_by_id[exp_id] = is_checked

        if is_checked:
            for other_id, other_var in self.checkbox_vars.items():
                if other_id != exp_id:
                    other_var.set(False)
                    self.checked_state_by_id[other_id] = False
                    self.unhighlight_row(other_id)
            self.selected_experiment_id = exp_id
            self.highlight_row(exp_id)
        else:
            self.selected_experiment_id = None
            self.unhighlight_row(exp_id)

    def get_selected_item(self):
        return self.selected_experiment_id

    def add_experiment(self):
        title = self.entry_title.get().strip()
        student_id = self.entry_student_id.get().strip()
        status = self.combo_status.get()

        success, msg = self.controller.add_experiment(title, student_id, status)
        if success:
            messagebox.showinfo("Success", msg)
            self.entry_title.delete(0, tk.END)
            self.entry_student_id.delete(0, tk.END)
            self.combo_status.current(0)
            self.load_data()
        else:
            messagebox.showerror("Error", msg)

    def update_experiment_status(self):
        exp_id = self.get_selected_item()
        if not exp_id:
            messagebox.showwarning("Warning", "Please select an experiment to update!")
            return

        new_status = self.combo_update_status.get()

        success, msg = self.controller.update_status(exp_id, new_status)
        if success:
            messagebox.showinfo("Success", msg)
            self.load_data()
        else:
            messagebox.showerror("Error", msg)

    def delete_selected(self):
        exp_id = self.get_selected_item()
        if not exp_id:
            messagebox.showwarning("Warning", "Please select an experiment to delete!")
            return

        confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete experiment ID {exp_id}?")
        if confirm:
            success, msg = self.controller.delete_experiment(exp_id)
            if success:
                messagebox.showinfo("Success", msg)
                self.load_data()
            else:
                messagebox.showerror("Error", msg)

    def auto_refresh(self):
        """Periodically reloads database data every 2 seconds for real-time polling sync."""
        self.load_data()
        self.root.after(2000, self.auto_refresh)
