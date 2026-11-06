
import tkinter as tk
from tkinter import messagebox
import sqlite3
from pathlib import Path
from datetime import datetime


# =========================================================
# STUDYFLOW - LIGHT LAVENDER EDITION
# =========================================================

DB_PATH = Path(__file__).with_name("tasks.db")

# Colour palette
BG = "#F5F4F8"
SIDEBAR = "#FFFFFF"
PANEL = "#FFFFFF"
CARD = "#FAF9FC"
CARD_HOVER = "#F0EDF6"

ACCENT = "#8B79B7"
ACCENT_DARK = "#75649F"
ACCENT_LIGHT = "#EAE5F3"

TEXT = "#292635"
MUTED = "#858092"
BORDER = "#E7E3EE"

GREEN = "#729C83"
RED = "#C77F8C"
YELLOW = "#B79553"

DELETE_BG = "#F9E9ED"


# =========================================================
# DATABASE
# =========================================================

def get_connection():
    return sqlite3.connect(DB_PATH)


def initialize_database():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS tasks (
                                                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                        title TEXT,
                                                        subject TEXT,
                                                        due_date TEXT,
                                                        priority TEXT DEFAULT 'Medium',
                                                        status TEXT DEFAULT 'Pending'
                   )
                   """)

    cursor.execute("PRAGMA table_info(tasks)")
    columns = [column[1] for column in cursor.fetchall()]

    # Support an older database with a "task" column.
    if "title" not in columns:

        cursor.execute(
            "ALTER TABLE tasks ADD COLUMN title TEXT"
        )

        if "task" in columns:
            cursor.execute("""
                           UPDATE tasks
                           SET title = task
                           WHERE title IS NULL
                           """)

    if "subject" not in columns:
        cursor.execute(
            "ALTER TABLE tasks ADD COLUMN subject TEXT"
        )

    if "due_date" not in columns:
        cursor.execute(
            "ALTER TABLE tasks ADD COLUMN due_date TEXT"
        )

    if "priority" not in columns:
        cursor.execute("""
                       ALTER TABLE tasks
                           ADD COLUMN priority TEXT DEFAULT 'Medium'
                       """)

    if "status" not in columns:
        cursor.execute("""
                       ALTER TABLE tasks
                           ADD COLUMN status TEXT DEFAULT 'Pending'
                       """)

    cursor.execute("""
                   UPDATE tasks
                   SET status = 'Pending'
                   WHERE status IS NULL OR status = ''
                   """)

    cursor.execute("""
                   UPDATE tasks
                   SET priority = 'Medium'
                   WHERE priority IS NULL OR priority = ''
                   """)

    conn.commit()
    conn.close()


# =========================================================
# MAIN APPLICATION
# =========================================================

class StudyFlow:

    def __init__(self, root):

        self.root = root
        self.root.title("StudyFlow")
        self.root.geometry("1250x780")
        self.root.minsize(950, 600)
        self.root.configure(bg=BG)

        self.current_filter = "All"
        self.search_text = tk.StringVar()
        self.search_placeholder = True

        self.build_interface()
        self.refresh_tasks()

    # =====================================================
    # CUSTOM CLICKABLE LABEL BUTTON
    # =====================================================

    def add_button(
            self,
            parent,
            label,
            command,
            bg_color,
            fg_color,
            hover_color=None,
            font_size=9
    ):

        button = tk.Label(
            parent,
            text=label,
            bg=bg_color,
            fg=fg_color,
            font=("Helvetica", font_size, "bold"),
            padx=16,
            pady=9,
            cursor="hand2",
            relief="flat",
            bd=0
        )

        button.bind(
            "<Button-1>",
            lambda event: command()
        )

        if hover_color:

            button.bind(
                "<Enter>",
                lambda event: button.config(
                    bg=hover_color
                )
            )

            button.bind(
                "<Leave>",
                lambda event: button.config(
                    bg=bg_color
                )
            )

        return button

    # =====================================================
    # MAIN INTERFACE
    # =====================================================

    def build_interface(self):

        self.sidebar = tk.Frame(
            self.root,
            bg=SIDEBAR,
            width=200
        )

        self.sidebar.pack(
            side="left",
            fill="y"
        )

        self.sidebar.pack_propagate(False)

        self.main = tk.Frame(
            self.root,
            bg=BG
        )

        self.main.pack(
            side="left",
            fill="both",
            expand=True
        )

        self.build_sidebar()
        self.build_dashboard()

    # =====================================================
    # SIDEBAR
    # =====================================================

    def build_sidebar(self):

        tk.Label(
            self.sidebar,
            text="S/ StudyFlow",
            font=("Helvetica", 19, "bold"),
            bg=SIDEBAR,
            fg=ACCENT
        ).pack(
            anchor="w",
            padx=20,
            pady=(30, 5)
        )

        tk.Label(
            self.sidebar,
            text="YOUR PERSONAL STUDY SPACE",
            font=("Helvetica", 8, "bold"),
            bg=SIDEBAR,
            fg=MUTED
        ).pack(
            anchor="w",
            padx=21,
            pady=(0, 38)
        )

        tk.Label(
            self.sidebar,
            text="WORKSPACE",
            font=("Helvetica", 9, "bold"),
            bg=SIDEBAR,
            fg=MUTED
        ).pack(
            anchor="w",
            padx=20,
            pady=(0, 12)
        )

        self.nav_buttons = {}

        navigation = [
            ("Dashboard", "All"),
            ("All Tasks", "All"),
            ("Pending", "Pending"),
            ("Completed", "Completed")
        ]

        for label, filter_value in navigation:

            button = tk.Label(
                self.sidebar,
                text=label,
                bg=SIDEBAR,
                fg=TEXT,
                font=("Helvetica", 10),
                anchor="w",
                padx=16,
                pady=11,
                cursor="hand2"
            )

            button.bind(
                "<Button-1>",
                lambda event, f=filter_value, l=label:
                self.set_filter(f, l)
            )

            button.pack(
                fill="x",
                padx=12,
                pady=3
            )

            self.nav_buttons[label] = button

        # Sidebar footer
        bottom = tk.Frame(
            self.sidebar,
            bg=SIDEBAR
        )

        bottom.pack(
            side="bottom",
            fill="x",
            padx=20,
            pady=22
        )

        tk.Label(
            bottom,
            text="One task at a time.",
            font=("Helvetica", 9),
            bg=SIDEBAR,
            fg=MUTED
        ).pack(anchor="w")

        tk.Label(
            bottom,
            text="FOCUS ON PROGRESS",
            font=("Helvetica", 9, "bold"),
            bg=SIDEBAR,
            fg=ACCENT
        ).pack(
            anchor="w",
            pady=(20, 0)
        )

        self.highlight_navigation("Dashboard")

    # =====================================================
    # DASHBOARD
    # =====================================================

    def build_dashboard(self):

        # Header
        header = tk.Frame(
            self.main,
            bg=BG
        )

        header.pack(
            fill="x",
            padx=28,
            pady=(25, 20)
        )

        header_left = tk.Frame(
            header,
            bg=BG
        )

        header_left.pack(side="left")

        tk.Label(
            header_left,
            text="Dashboard",
            font=("Helvetica", 23, "bold"),
            bg=BG,
            fg=TEXT
        ).pack(anchor="w")

        today = datetime.now().strftime(
            "%A, %d %B %Y"
        )

        tk.Label(
            header_left,
            text=today,
            font=("Helvetica", 10),
            bg=BG,
            fg=MUTED
        ).pack(
            anchor="w",
            pady=(5, 0)
        )

        self.add_button(
            header,
            "+ Add Task",
            self.open_add_task,
            ACCENT,
            "#FFFFFF",
            ACCENT_DARK
        ).pack(side="right", pady=8)

        # Statistics
        stats = tk.Frame(
            self.main,
            bg=BG
        )

        stats.pack(
            fill="x",
            padx=28,
            pady=(0, 20)
        )

        self.total_value = self.create_stat_card(
            stats,
            "TOTAL TASKS",
            ACCENT
        )

        self.pending_value = self.create_stat_card(
            stats,
            "PENDING",
            YELLOW
        )

        self.completed_value = self.create_stat_card(
            stats,
            "COMPLETED",
            GREEN
        )

        # Search and filter
        search_frame = tk.Frame(
            self.main,
            bg=BG
        )

        search_frame.pack(
            fill="x",
            padx=28,
            pady=(0, 17)
        )

        self.search_entry = tk.Entry(
            search_frame,
            textvariable=self.search_text,
            font=("Helvetica", 11),
            bg="#FFFFFF",
            fg=TEXT,
            insertbackground=TEXT,
            relief="flat",
            highlightthickness=1,
            highlightbackground=BORDER,
            highlightcolor=ACCENT
        )

        self.search_entry.pack(
            side="left",
            fill="x",
            expand=True,
            ipady=10
        )

        self.search_entry.insert(
            0,
            "Search tasks or subjects..."
        )

        self.search_entry.bind(
            "<FocusIn>",
            self.clear_search_placeholder
        )

        self.search_entry.bind(
            "<FocusOut>",
            self.restore_search_placeholder
        )

        self.search_entry.bind(
            "<KeyRelease>",
            self.refresh_tasks
        )

        # Filter dropdown
        self.filter_var = tk.StringVar(
            value="All"
        )

        filter_menu = tk.OptionMenu(
            search_frame,
            self.filter_var,
            "All",
            "Pending",
            "Completed",
            command=lambda value: self.refresh_tasks()
        )

        filter_menu.config(
            bg="#FFFFFF",
            fg=TEXT,
            activebackground=CARD_HOVER,
            activeforeground=ACCENT_DARK,
            font=("Helvetica", 10),
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=BORDER,
            padx=12,
            pady=7
        )

        filter_menu["menu"].config(
            bg="#FFFFFF",
            fg=TEXT,
            activebackground=CARD_HOVER,
            activeforeground=ACCENT_DARK,
            font=("Helvetica", 10)
        )

        filter_menu.pack(
            side="right",
            padx=(12, 0)
        )

        # Task panel
        self.task_panel = tk.Frame(
            self.main,
            bg=PANEL,
            highlightbackground=BORDER,
            highlightthickness=1
        )

        self.task_panel.pack(
            fill="both",
            expand=True,
            padx=25,
            pady=(0, 22)
        )

        panel_header = tk.Frame(
            self.task_panel,
            bg=PANEL
        )

        panel_header.pack(
            fill="x",
            padx=18,
            pady=15
        )

        tk.Label(
            panel_header,
            text="YOUR TASKS",
            font=("Helvetica", 10, "bold"),
            bg=PANEL,
            fg=MUTED
        ).pack(side="left")

        self.task_count_label = tk.Label(
            panel_header,
            text="0 tasks",
            font=("Helvetica", 9),
            bg=PANEL,
            fg=MUTED
        )

        self.task_count_label.pack(side="right")

        # Scrollable task area
        task_area = tk.Frame(
            self.task_panel,
            bg=PANEL
        )

        task_area.pack(
            fill="both",
            expand=True,
            padx=12,
            pady=(0, 12)
        )

        self.canvas = tk.Canvas(
            task_area,
            bg=PANEL,
            highlightthickness=0,
            bd=0
        )

        self.scrollbar = tk.Scrollbar(
            task_area,
            orient="vertical",
            command=self.canvas.yview
        )

        self.task_container = tk.Frame(
            self.canvas,
            bg=PANEL
        )

        self.task_window = self.canvas.create_window(
            (0, 0),
            window=self.task_container,
            anchor="nw"
        )

        self.canvas.configure(
            yscrollcommand=self.scrollbar.set
        )

        self.task_container.bind(
            "<Configure>",
            self.update_scroll_region
        )

        self.canvas.bind(
            "<Configure>",
            self.resize_task_container
        )

        self.canvas.pack(
            side="left",
            fill="both",
            expand=True
        )

        self.scrollbar.pack(
            side="right",
            fill="y"
        )

        self.canvas.bind_all(
            "<MouseWheel>",
            self.on_mousewheel
        )

    # =====================================================
    # STATISTICS
    # =====================================================

    def create_stat_card(self, parent, heading, color):

        card = tk.Frame(
            parent,
            bg=PANEL,
            highlightbackground=BORDER,
            highlightthickness=1
        )

        card.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0, 8)
        )

        tk.Label(
            card,
            text=heading,
            font=("Helvetica", 9, "bold"),
            bg=PANEL,
            fg=MUTED
        ).pack(
            anchor="w",
            padx=16,
            pady=(12, 3)
        )

        value = tk.Label(
            card,
            text="0",
            font=("Helvetica", 23, "bold"),
            bg=PANEL,
            fg=color
        )

        value.pack(
            anchor="w",
            padx=16,
            pady=(0, 10)
        )

        return value

    def update_statistics(self):

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT COUNT(*) FROM tasks"
        )
        total = cursor.fetchone()[0]

        cursor.execute("""
                       SELECT COUNT(*) FROM tasks
                       WHERE status = 'Pending'
                       """)
        pending = cursor.fetchone()[0]

        cursor.execute("""
                       SELECT COUNT(*) FROM tasks
                       WHERE status = 'Completed'
                       """)
        completed = cursor.fetchone()[0]

        conn.close()

        self.total_value.config(text=str(total))
        self.pending_value.config(text=str(pending))
        self.completed_value.config(text=str(completed))

    # =====================================================
    # SEARCH AND FILTER
    # =====================================================

    def clear_search_placeholder(self, event=None):

        if self.search_placeholder:

            self.search_entry.delete(0, "end")
            self.search_placeholder = False

    def restore_search_placeholder(self, event=None):

        if not self.search_entry.get().strip():

            self.search_entry.delete(0, "end")

            self.search_entry.insert(
                0,
                "Search tasks or subjects..."
            )

            self.search_placeholder = True

    def set_filter(self, filter_value, label):

        self.current_filter = filter_value
        self.filter_var.set(filter_value)

        self.highlight_navigation(label)
        self.refresh_tasks()

    def highlight_navigation(self, selected):

        for label, button in self.nav_buttons.items():

            if label == selected:

                button.config(
                    bg=CARD_HOVER,
                    fg=ACCENT_DARK,
                    font=("Helvetica", 10, "bold")
                )

            else:

                button.config(
                    bg=SIDEBAR,
                    fg=TEXT,
                    font=("Helvetica", 10)
                )

    # =====================================================
    # REFRESH TASKS
    # =====================================================

    def refresh_tasks(self, event=None):

        for widget in self.task_container.winfo_children():
            widget.destroy()

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
                       SELECT id, title, subject, due_date, priority, status
                       FROM tasks
                       ORDER BY
                           CASE status
                               WHEN 'Pending' THEN 0
                               ELSE 1
                               END,
                           id DESC
                       """)

        tasks = cursor.fetchall()
        conn.close()

        search = ""

        if not self.search_placeholder:
            search = self.search_text.get().strip().lower()

        selected_filter = self.filter_var.get()

        if selected_filter == "All":
            selected_filter = self.current_filter

        filtered_tasks = []

        for task in tasks:

            task_id, title, subject, due_date, priority, status = task

            title = title or ""
            subject = subject or ""
            priority = priority or "Medium"
            status = status or "Pending"

            if (
                    selected_filter != "All"
                    and status != selected_filter
            ):
                continue

            if search:
                if (
                        search not in title.lower()
                        and search not in subject.lower()
                ):
                    continue

            filtered_tasks.append(task)

        self.task_count_label.config(
            text=f"{len(filtered_tasks)} tasks"
        )

        if not filtered_tasks:

            tk.Label(
                self.task_container,
                text="No tasks found.\nAdd a task to get started.",
                font=("Helvetica", 12),
                bg=PANEL,
                fg=MUTED,
                justify="center"
            ).pack(pady=55)

        else:

            for task in filtered_tasks:
                self.create_task_card(task)

        self.update_statistics()

        self.task_container.update_idletasks()
        self.update_scroll_region()

    # =====================================================
    # TASK CARD
    # =====================================================

    def create_task_card(self, task):

        task_id, title, subject, due_date, priority, status = task

        title = title or ""
        subject = subject or ""
        due_date = due_date or ""
        priority = priority or "Medium"
        status = status or "Pending"

        card = tk.Frame(
            self.task_container,
            bg=CARD,
            highlightbackground=BORDER,
            highlightthickness=1
        )

        card.pack(
            fill="x",
            padx=5,
            pady=5
        )

        # Checkbox
        completed = tk.BooleanVar(
            value=(status == "Completed")
        )

        checkbox = tk.Checkbutton(
            card,
            variable=completed,
            command=lambda tid=task_id, var=completed:
            self.toggle_status(tid, var.get()),
            bg=CARD,
            activebackground=CARD,
            selectcolor=ACCENT_LIGHT,
            fg=ACCENT_DARK,
            activeforeground=ACCENT_DARK,
            relief="flat",
            bd=0,
            highlightthickness=0,
            cursor="hand2"
        )

        checkbox.pack(
            side="left",
            padx=(10, 12),
            pady=15
        )

        # Task details
        info = tk.Frame(
            card,
            bg=CARD
        )

        info.pack(
            side="left",
            fill="x",
            expand=True,
            pady=12
        )

        title_color = (
            MUTED if status == "Completed" else TEXT
        )

        tk.Label(
            info,
            text=title,
            font=("Helvetica", 11, "bold"),
            bg=CARD,
            fg=title_color
        ).pack(anchor="w")

        details = subject

        if due_date:

            if details:
                details += "   |   "

            details += "Due: " + due_date

        tk.Label(
            info,
            text=details,
            font=("Helvetica", 9),
            bg=CARD,
            fg=MUTED
        ).pack(
            anchor="w",
            pady=(5, 0)
        )

        # Priority
        priority_color = {
            "High": RED,
            "Medium": YELLOW,
            "Low": GREEN
        }.get(priority, MUTED)

        tk.Label(
            card,
            text=priority.upper(),
            font=("Helvetica", 8, "bold"),
            bg=CARD,
            fg=priority_color
        ).pack(
            side="left",
            padx=12
        )

        # Edit
        self.add_button(
            card,
            "Edit",
            lambda tid=task_id:
            self.open_edit_task(tid),
            ACCENT_LIGHT,
            ACCENT_DARK,
            CARD_HOVER
        ).pack(
            side="left",
            padx=5,
            pady=12
        )

        # Delete
        self.add_button(
            card,
            "Delete",
            lambda tid=task_id:
            self.delete_task(tid),
            DELETE_BG,
            RED,
            "#F4DDE3"
        ).pack(
            side="left",
            padx=(5, 12),
            pady=12
        )

    # =====================================================
    # ADD TASK
    # =====================================================

    def open_add_task(self):

        self.task_form()

    # =====================================================
    # EDIT TASK
    # =====================================================

    def open_edit_task(self, task_id):

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
                       SELECT title, subject, due_date, priority
                       FROM tasks
                       WHERE id = ?
                       """, (task_id,))

        task = cursor.fetchone()
        conn.close()

        if task:
            self.task_form(task_id, task)

    # =====================================================
    # TASK FORM
    # =====================================================

    def task_form(self, task_id=None, existing=None):

        window = tk.Toplevel(self.root)

        window.title(
            "Edit Task" if task_id else "Add Task"
        )

        window.geometry("430x470")
        window.resizable(False, False)
        window.configure(bg=BG)
        window.transient(self.root)
        window.grab_set()

        tk.Label(
            window,
            text="Edit Task" if task_id else "Add New Task",
            font=("Helvetica", 19, "bold"),
            bg=BG,
            fg=TEXT
        ).pack(
            anchor="w",
            padx=25,
            pady=(25, 20)
        )

        def create_field(label, default=""):

            tk.Label(
                window,
                text=label,
                font=("Helvetica", 10, "bold"),
                bg=BG,
                fg=MUTED
            ).pack(
                anchor="w",
                padx=25,
                pady=(7, 5)
            )

            entry = tk.Entry(
                window,
                font=("Helvetica", 11),
                bg="#FFFFFF",
                fg=TEXT,
                insertbackground=TEXT,
                relief="flat",
                highlightthickness=1,
                highlightbackground=BORDER,
                highlightcolor=ACCENT
            )

            entry.pack(
                fill="x",
                padx=25,
                ipady=8
            )

            if default:
                entry.insert(0, default)

            return entry

        title_entry = create_field(
            "Task Title",
            existing[0] if existing else ""
        )

        subject_entry = create_field(
            "Subject",
            existing[1] if existing else ""
        )

        date_entry = create_field(
            "Due Date (YYYY-MM-DD)",
            existing[2] if existing else ""
        )

        tk.Label(
            window,
            text="Priority",
            font=("Helvetica", 10, "bold"),
            bg=BG,
            fg=MUTED
        ).pack(
            anchor="w",
            padx=25,
            pady=(12, 5)
        )

        priority_var = tk.StringVar(
            value=existing[3] if existing else "Medium"
        )

        priority_menu = tk.OptionMenu(
            window,
            priority_var,
            "High",
            "Medium",
            "Low"
        )

        priority_menu.config(
            bg="#FFFFFF",
            fg=TEXT,
            activebackground=CARD_HOVER,
            activeforeground=ACCENT_DARK,
            font=("Helvetica", 10),
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=BORDER
        )

        priority_menu["menu"].config(
            bg="#FFFFFF",
            fg=TEXT,
            activebackground=CARD_HOVER,
            activeforeground=ACCENT_DARK
        )

        priority_menu.pack(
            anchor="w",
            padx=25
        )

        # Save
        def save_task():

            title = title_entry.get().strip()
            subject = subject_entry.get().strip()
            due_date = date_entry.get().strip()
            priority = priority_var.get()

            if not title:

                messagebox.showwarning(
                    "Missing Information",
                    "Please enter a task title.",
                    parent=window
                )

                return

            if due_date:

                try:
                    datetime.strptime(
                        due_date,
                        "%Y-%m-%d"
                    )

                except ValueError:

                    messagebox.showwarning(
                        "Invalid Date",
                        "Use YYYY-MM-DD format for the due date.",
                        parent=window
                    )

                    return

            conn = get_connection()
            cursor = conn.cursor()

            if task_id:

                cursor.execute("""
                               UPDATE tasks
                               SET title = ?,
                                   subject = ?,
                                   due_date = ?,
                                   priority = ?
                               WHERE id = ?
                               """, (
                                   title,
                                   subject,
                                   due_date,
                                   priority,
                                   task_id
                               ))

            else:

                cursor.execute("""
                               INSERT INTO tasks
                                   (title, subject, due_date, priority, status)
                               VALUES (?, ?, ?, ?, 'Pending')
                               """, (
                                   title,
                                   subject,
                                   due_date,
                                   priority
                               ))

            conn.commit()
            conn.close()

            window.destroy()
            self.refresh_tasks()

        self.add_button(
            window,
            "Save Task",
            save_task,
            ACCENT,
            "#FFFFFF",
            ACCENT_DARK
        ).pack(
            fill="x",
            padx=25,
            pady=22
        )

        title_entry.focus_set()

    # =====================================================
    # COMPLETE / PENDING
    # =====================================================

    def toggle_status(self, task_id, is_completed):

        new_status = (
            "Completed" if is_completed else "Pending"
        )

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
                       UPDATE tasks
                       SET status = ?
                       WHERE id = ?
                       """, (new_status, task_id))

        conn.commit()
        conn.close()

        self.refresh_tasks()

    # =====================================================
    # DELETE TASK
    # =====================================================

    def delete_task(self, task_id):

        confirm = messagebox.askyesno(
            "Delete Task",
            "Are you sure you want to delete this task?"
        )

        if not confirm:
            return

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM tasks WHERE id = ?",
            (task_id,)
        )

        conn.commit()
        conn.close()

        self.refresh_tasks()

    # =====================================================
    # SCROLLING
    # =====================================================

    def update_scroll_region(self, event=None):

        self.canvas.configure(
            scrollregion=self.canvas.bbox("all")
        )

    def resize_task_container(self, event):

        self.canvas.itemconfigure(
            self.task_window,
            width=event.width
        )

    def on_mousewheel(self, event):

        if self.canvas.winfo_exists():

            self.canvas.yview_scroll(
                int(-1 * (event.delta / 120)),
                "units"
            )


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    initialize_database()

    root = tk.Tk()

    app = StudyFlow(root)

    root.mainloop()
