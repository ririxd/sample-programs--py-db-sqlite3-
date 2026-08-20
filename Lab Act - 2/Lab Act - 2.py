import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk
 
# ==========================================
# 1. DATABASE & EVENT LOGIC
# ==========================================
CHECKED = "☑"
UNCHECKED = "☐"
selected_items = set()
editing_update_fields = False
 
def init_db():
    """Create the database and table if it doesn't exist."""
    conn = sqlite3.connect("lab_tracker.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS experiments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            student_id TEXT NOT NULL,
            status TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()
 
 
def add_experiment():
    """Insert a new record from GUI input fields into SQLite."""
    title = entry_title.get().strip()
    student_id = entry_student.get().strip()
    status = combo_status.get()
 
    if not title or not student_id:
        messagebox.showwarning("Input Error", "Please fill in all fields!")
        return

    # Prevent duplicate titles (case-insensitive)
    conn = sqlite3.connect("lab_tracker.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(1) FROM experiments WHERE LOWER(title)=?", (title.lower(),))
    if cursor.fetchone()[0]:
        conn.close()
        messagebox.showwarning("Duplicate Entry", f"An experiment titled '{title}' already exists.")
        return
 
    conn = sqlite3.connect("lab_tracker.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO experiments (title, student_id, status) VALUES (?, ?, ?)",
        (title, student_id, status)
    )
 
    conn.commit()
    conn.close()
 
    # Clear input fields & refresh
    entry_title.delete(0, tk.END)
    entry_student.delete(0, tk.END)
    combo_status.current(0)
    load_data()
    messagebox.showinfo("Success", "Experiment added successfully!")
 
 
def load_data():
    """Fetch all records from SQLite and refresh the Treeview table."""
    # remember currently selected id to restore after reload
    selected_id = None
    cur_sel = tree.selection()
    if cur_sel:
        try:
            selected_id = int(tree.item(cur_sel[0], "values")[1])
        except Exception:
            selected_id = None

    for row in tree.get_children():
        tree.delete(row)

    conn = sqlite3.connect("lab_tracker.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM experiments")
    rows = cursor.fetchall()
    conn.close()

    for row in rows:
        checkbox = CHECKED if row[0] in selected_items else UNCHECKED
        # values: Select, ID, Title, Student ID, Status
        tree.insert("", tk.END, values=(checkbox, row[0], row[1], row[2], row[3]))

    # restore selection and update fields if not editing
    if selected_id is not None:
        for child in tree.get_children():
            try:
                vals = tree.item(child, "values")
                if int(vals[1]) == selected_id:
                    tree.selection_set(child)
                    tree.focus(child)
                    tree.see(child)
                    if not is_editing_update_fields():
                        update_status_fields_from_selection()
                    break
            except Exception:
                continue
 
 
def get_selected_id():
    """Return the ID of the currently selected Treeview row, or None."""
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("No Selection", "Please select a record first!")
        return None
    item_values = tree.item(selected[0], "values")
    try:
        return int(item_values[1])
    except Exception:
        return item_values[1]


def is_editing_update_fields():
    try:
        if editing_update_fields:
            return True
    except NameError:
        pass
    focused = root.focus_get()
    return focused == combo_update_status if focused is not None else False


def start_edit(event=None):
    global editing_update_fields
    editing_update_fields = True


def end_edit():
    global editing_update_fields
    editing_update_fields = False


def toggle_checkbox(event):
    region = tree.identify_region(event.x, event.y)
    if region != "cell":
        return
    column = tree.identify_column(event.x)
    if column != "#1":
        return
    row_id = tree.identify_row(event.y)
    if not row_id:
        return

    values = list(tree.item(row_id, "values"))
    try:
        item_id = int(values[1])
    except Exception:
        item_id = values[1]

    if values[0] == UNCHECKED:
        values[0] = CHECKED
        selected_items.add(item_id)
    else:
        values[0] = UNCHECKED
        selected_items.discard(item_id)
    tree.item(row_id, values=values)

    # make clicked row selected so update fields populate
    tree.selection_set(row_id)
    tree.focus(row_id)
    update_status_fields_from_selection()


def update_status_fields_from_selection():
    sel = tree.selection()
    if not sel:
        return
    vals = tree.item(sel[0], "values")
    combo_update_status.set(vals[4])
 
 
def update_status():
    """Update the status of the selected record."""
    exp_id = get_selected_id()
    if exp_id is None:
        return
 
    new_status = combo_update_status.get()
    # finish edit mode, update DB, then reload
    end_edit()
    conn = sqlite3.connect("lab_tracker.db")
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE experiments SET status = ? WHERE id = ?",
        (new_status, exp_id)
    )
    conn.commit()
    conn.close()

    load_data()
    messagebox.showinfo("Updated", f"Experiment ID {exp_id} status updated!")
 
 
def delete_selected():
    """Delete the currently selected record."""
    exp_id = get_selected_id()
    if exp_id is None:
        return
 
    confirm = messagebox.askyesno(
        "Confirm Delete",
        f"Are you sure you want to delete Experiment ID {exp_id}?"
    )
    if not confirm:
        return
 
    conn = sqlite3.connect("lab_tracker.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM experiments WHERE id = ?", (exp_id,))
    conn.commit()
    conn.close()

    load_data()
    messagebox.showinfo("Deleted", f"Experiment ID {exp_id} removed!")
 
 
def auto_refresh():
    """Periodically reloads data from SQLite every 2 seconds for real-time sync."""
    # do not auto-reload while user is editing the update status
    if not is_editing_update_fields():
        load_data()
    root.after(2000, auto_refresh)
 
# =========================================
# 2. GUI LAYOUT
# =========================================
 
init_db()
 
root = tk.Tk()
root.title("Student Lab Tracker")
root.geometry("650x550")
 
# --- Form Inputs Frame ---
frame_form = tk.LabelFrame(root, text="Add New Experiment", padx=10, pady=10)
frame_form.pack(fill="x", padx=10, pady=5)
 
tk.Label(frame_form, text="Title:").grid(row=0, column=0, sticky="e")
entry_title = tk.Entry(frame_form, width=25)
entry_title.grid(row=0, column=1, padx=5, pady=5)
 
tk.Label(frame_form, text="Student ID:").grid(row=0, column=2, sticky="e")
entry_student = tk.Entry(frame_form, width=15)
entry_student.grid(row=0, column=3, padx=5, pady=5)
 
tk.Label(frame_form, text="Status:").grid(row=1, column=0, sticky="e")
combo_status = ttk.Combobox(
    frame_form,
    values=["Pending", "In Progress", "Completed"],
    state="readonly",
    width=22
)
combo_status.current(0)
combo_status.grid(row=1, column=1, padx=5, pady=5)
 
btn_add = tk.Button(
    frame_form,
    text="Save Experiment",
    command=add_experiment,
    bg="#4CAF50",
    fg="white"
)
btn_add.grid(row=1, column=2, columnspan=2, padx=5, pady=5, sticky="ew")
 
# --- Data Grid Display Frame ---
frame_table = tk.Frame(root)
frame_table.pack(fill="both", expand=True, padx=10, pady=5)
 
scroll_y = tk.Scrollbar(frame_table, orient=tk.VERTICAL)
tree = ttk.Treeview(
    frame_table,
    columns=("Select", "ID", "Title", "Student ID", "Status"),
    show="headings",
    yscrollcommand=scroll_y.set,
    selectmode="browse"
)
scroll_y.config(command=tree.yview)
scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
 
tree.heading("Select", text="Select")
tree.heading("ID", text="ID")
tree.heading("Title", text="Experiment Title")
tree.heading("Student ID", text="Student ID")
tree.heading("Status", text="Status")

tree.column("Select", width=60, anchor="center")
tree.column("ID", width=40, anchor="center")
tree.column("Title", width=250)
tree.column("Student ID", width=100, anchor="center")
tree.column("Status", width=100, anchor="center")
 
tree.pack(fill="both", expand=True)
tree.bind("<Button-1>", toggle_checkbox)
def on_tree_selection_event(event):
    if not is_editing_update_fields():
        update_status_fields_from_selection()

tree.bind("<<TreeviewSelect>>", on_tree_selection_event)
 
# --- Status Update Frame ---
frame_update = tk.LabelFrame(
    root,
    text="Update Selected Record Status",
    padx=10,
    pady=5
)
frame_update.pack(fill="x", padx=10, pady=5)
 
tk.Label(frame_update, text="New Status:").grid(
    row=0, column=0, padx=5, pady=5
)
combo_update_status = ttk.Combobox(
    frame_update,
    values=["Pending", "In Progress", "Completed"],
    state="readonly",
    width=18
)
combo_update_status.current(0)
combo_update_status.grid(row=0, column=1, padx=5, pady=5)
combo_update_status.bind("<FocusIn>", start_edit)
combo_update_status.bind("<FocusOut>", lambda e: end_edit())
 
btn_update = tk.Button(
    frame_update,
    text="Update Status",
    command=update_status,
    bg="#2196F3",
    fg="white"
)
btn_update.grid(row=0, column=2, padx=10, pady=5)

btn_cancel_update = tk.Button(frame_update, text="Cancel Edit", command=lambda: (end_edit(), update_status_fields_from_selection()))
btn_cancel_update.grid(row=0, column=3, padx=5, pady=5)
 
# --- Delete Button ---
btn_delete = tk.Button(
    root,
    text="Delete Selected Record",
    command=delete_selected,
    bg="#f44336",
    fg="white"
)
btn_delete.pack(fill="x", padx=10, pady=10)
 
# =========================================
# 3. APPLICATION LAUNCH
# =========================================
 
auto_refresh()
root.mainloop()
 
 