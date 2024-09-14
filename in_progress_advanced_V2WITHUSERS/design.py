from tkinter import ttk, Menu, Label, Entry, Toplevel, Button, simpledialog, messagebox, filedialog
from logic import load_excel, save_to_db, generate_report, download_excel, update_status_bar, on_double_click, get_dataframe, display_df_in_treeview
from logic import backup_data_handler, import_data_handler, execute_sql_query, download_backup
from auth import add_user, update_user, delete_user, log_action
from database import init_db
from tkinter import ttk, Menu, Label, Entry, Toplevel, Button, simpledialog, messagebox, filedialog
from logic import load_excel, save_to_db, generate_report, download_excel, update_status_bar, on_double_click, get_dataframe, display_df_in_treeview
from logic import backup_data_handler, import_data_handler, execute_sql_query, download_backup
from auth import add_user, update_user, delete_user, log_action
from database import init_db



def setup_ui(root, db_names):
    style = ttk.Style()
    style.configure("TNotebook.Tab", padding=[10, 10], font=('Arial', 10, 'bold'), background='#d1e0e0')
    style.configure("TButton", padding=[5, 5], font=('Arial', 10, 'bold'), background='#98b4b4')
    style.configure("TFrame", background="#f0f0f0")
    style.configure("TLabel", background="#f0f0f0")

    notebook = ttk.Notebook(root)
    notebook.pack(fill='both', expand=True)

    tabs = []
    for db_name in db_names:
        tab = ttk.Frame(notebook)
        notebook.add(tab, text=db_name)
        tabs.append(tab)
        setup_tab(root, tab, db_name)  # Pass the database name to setup_tab

    menubar = Menu(root)
    root.config(menu=menubar)
    file_menu = Menu(menubar, tearoff=0)
    menubar.add_cascade(label="File", menu=file_menu)
    file_menu.add_command(label="Logout", command=lambda: logout(root))
    file_menu.add_command(label="Exit", command=root.quit)

    status_bar = Label(root, text="Last Updated: Never", bd=1, relief="sunken", anchor="w")
    status_bar.pack(side="bottom", fill="x")
    root.status_bar = status_bar

    # Initialize the user management database connection
    conn = init_db("user_management")
    setup_admin_ui(root, conn)
def setup_tab(root, tab, db_name):
    conn = init_db(db_name)
    data_frame = ttk.Frame(tab)
    data_frame.pack(fill='both', expand=True)
    tree = ttk.Treeview(data_frame)
    tree.pack(fill='both', expand=True)

    df = get_dataframe(conn, "daily_data")
    if df is not None:
        df = df.fillna('')
        display_df_in_treeview(tree, df)

    tree.bind('<Double-1>', lambda event: on_double_click(event, tree))

    button_frame = ttk.Frame(tab)
    button_frame.pack(fill='x', pady=10)

    load_button = ttk.Button(button_frame, text="Load Excel", command=lambda: load_excel(tree))
    load_button.pack(side="left", padx=5)

    save_button = ttk.Button(button_frame, text="Save to Database", command=lambda: save_to_db(tree, conn))
    save_button.pack(side="left", padx=5)

    backup_button = ttk.Button(button_frame, text="Save to Backup", command=lambda: backup_data_handler(root, conn))
    backup_button.pack(side="left", padx=5)

    import_button = ttk.Button(button_frame, text="Import Data", command=lambda: import_data_handler(root, conn))
    import_button.pack(side="left", padx=5)

    query_button = ttk.Button(button_frame, text="Execute SQL Query", command=lambda: execute_sql_query(conn))
    query_button.pack(side="left", padx=5)

    download_button = ttk.Button(button_frame, text="Download Backup", command=lambda: download_backup(conn))
    download_button.pack(side="left", padx=5)

    excel_button = ttk.Button(button_frame, text="Download in Excel", command=lambda: download_excel_data(conn))
    excel_button.pack(side="left", padx=5)

    report_button = ttk.Button(button_frame, text="Reports", command=lambda: open_report_window(conn))
    report_button.pack(side="left", padx=5)


def setup_admin_ui(root, conn):
    admin_menu = Menu(root)
    root.config(menu=admin_menu)
    user_menu = Menu(admin_menu, tearoff=0)
    admin_menu.add_cascade(label="User Management", menu=user_menu)
    user_menu.add_command(label="Add User", command=lambda: open_add_user_window(root, conn))
    user_menu.add_command(label="Modify User", command=lambda: open_modify_user_window(root, conn))
    user_menu.add_command(label="Delete User", command=lambda: open_delete_user_window(root, conn))
    user_menu.add_command(label="View Users", command=lambda: open_view_users_window(root, conn))

    log_menu = Menu(admin_menu, tearoff=0)
    admin_menu.add_cascade(label="Logs", menu=log_menu)
    log_menu.add_command(label="View Logs", command=lambda: open_view_logs_window(root, conn))

def setup_login_screen(root, authenticate_callback):
    root.title("Login")
    root.geometry("300x150")

    username_label = ttk.Label(root, text="Username:")
    username_label.pack(pady=5)
    username_entry = ttk.Entry(root)
    username_entry.pack(pady=5)

    password_label = ttk.Label(root, text="Password:")
    password_label.pack(pady=5)
    password_entry = ttk.Entry(root, show='*')
    password_entry.pack(pady=5)

    login_button = ttk.Button(root, text="Login", command=lambda: authenticate_callback(username_entry.get(), password_entry.get()))
    login_button.pack(pady=5)


def open_add_user_window(root, conn):
    top = Toplevel(root)
    top.title("Add User")

    username_label = ttk.Label(top, text="Username:")
    username_label.pack(pady=5)
    username_entry = ttk.Entry(top)
    username_entry.pack(pady=5)

    password_label = ttk.Label(top, text="Password:")
    password_label.pack(pady=5)
    password_entry = ttk.Entry(top, show='*')
    password_entry.pack(pady=5)

    add_button = ttk.Button(top, text="Add", command=lambda: add_user_handler(username_entry.get(), password_entry.get(), conn, top))
    add_button.pack(pady=20)

def add_user_handler(username, password, conn, top):
    if add_user(username, password, conn):
        messagebox.showinfo("Success", "User added successfully")
        top.destroy()
    else:
        messagebox.showerror("Error", "Username already exists")

def open_modify_user_window(root, conn):
    top = Toplevel(root)
    top.title("Modify User")

    user_id_label = ttk.Label(top, text="User ID:")
    user_id_label.pack(pady=5)
    user_id_entry = ttk.Entry(top)
    user_id_entry.pack(pady=5)

    username_label = ttk.Label(top, text="Username:")
    username_label.pack(pady=5)
    username_entry = ttk.Entry(top)
    username_entry.pack(pady=5)

    password_label = ttk.Label(top, text="Password:")
    password_label.pack(pady=5)
    password_entry = ttk.Entry(top, show='*')
    password_entry.pack(pady=5)

    update_button = ttk.Button(top, text="Update", command=lambda: update_user_handler(user_id_entry.get(), username_entry.get(), password_entry.get(), conn, top))
    update_button.pack(pady=5)

def update_user_handler(user_id, username, password, conn, top):
    update_user(user_id, username, password, conn)
    messagebox.showinfo("Success", "User updated successfully")
    top.destroy()

def open_delete_user_window(root, conn):
    top = Toplevel(root)
    top.title("Delete User")

    user_id_label = ttk.Label(top, text="User ID:")
    user_id_label.pack(pady=5)
    user_id_entry = ttk.Entry(top)
    user_id_entry.pack(pady=5)

    delete_button = ttk.Button(top, text="Delete", command=lambda: delete_user_handler(user_id_entry.get(), conn, top))
    delete_button.pack(pady=5)

def delete_user_handler(user_id, conn, top):
    delete_user(user_id, conn)
    messagebox.showinfo("Success", "User deleted successfully")
    top.destroy()

def open_view_users_window(root, conn):
    top = Toplevel(root)
    top.title("View Users")

    tree = ttk.Treeview(top)
    tree.pack(fill='both', expand=True)

    cursor = conn.cursor()
    cursor.execute("SELECT id, username FROM users")
    users = cursor.fetchall()

    tree["columns"] = ("ID", "Username")
    tree["show"] = "headings"

    for col in tree["columns"]:
        tree.heading(col, text=col)

    for user_row in users:
        tree.insert("", "end", values=user_row)

    tree.bind('<Double-1>', lambda event: on_user_double_click(event, tree, conn))


def on_user_double_click(event, tree, conn):
    item = tree.selection()[0]
    user_id = tree.item(item, "values")[0]

    top = Toplevel()
    top.title("Edit User")

    username_label = ttk.Label(top, text="Username:")
    username_label.pack(pady=5)
    username_entry = ttk.Entry(top)
    username_entry.insert(0, tree.item(item, "values")[1])
    username_entry.pack(pady=5)

    password_label = ttk.Label(top, text="Password:")
    password_label.pack(pady=5)
    password_entry = ttk.Entry(top)
    password_entry.pack(pady=5)

    update_button = ttk.Button(top, text="Update", command=lambda: update_user_handler(user_id, username_entry.get(), password_entry.get(), conn, top))
    update_button.pack(pady=5)

    delete_button = ttk.Button(top, text="Delete", command=lambda: delete_user_handler(user_id, conn, top))
    delete_button.pack(pady=5)

def open_view_logs_window(root, conn):
    top = Toplevel(root)
    top.title("View Logs")

    tree = ttk.Treeview(top)
    tree.pack(fill='both', expand=True)

    cursor = conn.cursor()
    cursor.execute("SELECT logs.id, users.username, logs.action, logs.timestamp FROM logs INNER JOIN users ON logs.user_id = users.id")
    logs = cursor.fetchall()

    tree["columns"] = ("ID", "User", "Action", "Timestamp")
    tree["show"] = "headings"

    for col in tree["columns"]:
        tree.heading(col, text=col)

    for log_row in logs:
        tree.insert("", "end", values=log_row)


def logout(root, conn):
    root.destroy()
