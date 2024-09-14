from tkinter import ttk, Menu, Label, Entry, Toplevel, Button, simpledialog, messagebox, filedialog, Text, Scrollbar
from logic import *
import tkinter as tk
from auth import add_user, update_user, delete_user, log_action
from database import init_db
import sqlite3

def setup_ui(root, db_names, user, theme=None):
    """
    Initialize the main UI, including the notebook with tabs, menu bar, status bar, and log window.

    Args:
        root (tk.Tk): The root Tkinter window.
        db_names (list of str): List of database names to create tabs for.
        user (str): The current user's name.
        theme (dict, optional): A dictionary to configure theme styles dynamically. Default is None.

    Raises:
        Exception: If a database connection fails or a UI component fails to initialize.
    """
    try:
        configure_styles(theme)
        notebook, tabs, last_timestamps = create_notebook_and_tabs(root, db_names, user)
        setup_menu_bar(root)
        setup_status_bar(root)
        setup_log_window(root)
        setup_admin_ui(root, init_db("user_management"))
        display_initial_log(root, notebook, tabs)
        start_polling_logs(root, tabs, last_timestamps)

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred while setting up the UI: {e}")
        root.quit()

def configure_styles(theme=None):
    """
    Configure the UI styles. Allows dynamic theme configuration if provided.

    Args:
        theme (dict, optional): A dictionary to configure theme styles dynamically. Default is None.
    """
    style = ttk.Style()

    if theme:
        tab_style = theme.get("tab_style", {})
        button_style = theme.get("button_style", {})
        frame_style = theme.get("frame_style", {})
        label_style = theme.get("label_style", {})
    else:
        tab_style = {
            "padding": [10, 10],
            "font": ('Arial', 10, 'bold'),
            "background": '#d1e0e0'
        }
        button_style = {
            "padding": [5, 5],
            "font": ('Arial', 10, 'bold'),
            "background": '#98b4b4'
        }
        frame_style = {"background": "#f0f0f0"}
        label_style = {"background": "#f0f0f0"}

    style.configure("TNotebook.Tab", **tab_style)
    style.configure("TButton", **button_style)
    style.configure("TFrame", **frame_style)
    style.configure("TLabel", **label_style)

def create_notebook_and_tabs(root, db_names, user):
    """
    Create the notebook and tabs for each database.

    Args:
        root (tk.Tk): The root Tkinter window.
        db_names (list of str): List of database names to create tabs for.
        user (str): The current user's name.

    Returns:
        tuple: A tuple containing the notebook, tabs dictionary, and last_timestamps dictionary.

    Raises:
        Exception: If a database connection fails or a tab fails to initialize.
    """
    notebook = ttk.Notebook(root)
    notebook.pack(fill='both', expand=True)

    tabs = {}
    last_timestamps = {}

    for db_name in db_names:
        tab = ttk.Frame(notebook)
        notebook.add(tab, text=db_name)

        try:
            conn = init_db(db_name)
            setup_tab(root, tab, db_name, user)
        except Exception as e:
            raise Exception(f"Failed to initialize tab for database '{db_name}': {e}")

        tabs[tab] = conn
        last_timestamps[tab] = tk.StringVar(value="1970-01-01 00:00:00")

    root.tabs = tabs
    root.last_timestamps = last_timestamps

    notebook.bind("<<NotebookTabChanged>>", lambda event: update_logs_on_tab_change(event, root))

    return notebook, tabs, last_timestamps

def setup_menu_bar(root):
    """
    Set up the menu bar with "File" options like Logout and Exit.

    Args:
        root (tk.Tk): The root Tkinter window.
    """
    menubar = Menu(root)
    root.config(menu=menubar)
    file_menu = Menu(menubar, tearoff=0)
    menubar.add_cascade(label="File", menu=file_menu)
    file_menu.add_command(label="Logout", command=lambda: logout(root))
    file_menu.add_command(label="Exit", command=root.quit)

def setup_status_bar(root):
    """
    Set up the status bar at the bottom of the window.

    Args:
        root (tk.Tk): The root Tkinter window.
    """
    status_bar = Label(root, text="Last Updated: Never", bd=1, relief="sunken", anchor="w")
    status_bar.pack(side="bottom", fill="x")
    root.status_bar = status_bar

def setup_log_window(root):
    """
    Set up the log window with a scrollbar.

    Args:
        root (tk.Tk): The root Tkinter window.
    """
    log_frame = ttk.Frame(root)
    log_frame.pack(side="bottom", fill="x")

    scrollbar = Scrollbar(log_frame)
    scrollbar.pack(side="right", fill="y")

    log_window = Text(log_frame, height=5, yscrollcommand=scrollbar.set, state='disabled', bg='#f0f0f0', font=('Arial', 10))
    log_window.pack(side="left", fill="both", expand=True)
    scrollbar.config(command=log_window.yview)

    root.log_window = log_window

def display_initial_log(root, notebook, tabs):
    """
    Display logs for the first tab upon UI setup.

    Args:
        root (tk.Tk): The root Tkinter window.
        notebook (ttk.Notebook): The notebook widget containing the tabs.
        tabs (dict): Dictionary mapping tabs to their database connections.
    """
    first_tab = list(tabs.keys())[0]
    last_timestamp_var = root.last_timestamps[first_tab]
    display_log(root, tabs[first_tab], last_timestamp_var.get())

def start_polling_logs(root, tabs, last_timestamps):
    """
    Start polling logs for all tabs.

    Args:
        root (tk.Tk): The root Tkinter window.
        tabs (dict): Dictionary mapping tabs to their database connections.
        last_timestamps (dict): Dictionary mapping tabs to their last log timestamps.
    """
    for tab, conn in tabs.items():
        start_log_polling(root, conn, last_timestamps[tab])

def update_logs_on_tab_change(event, root):
    notebook = event.widget
    selected_tab = notebook.select()
    selected_tab_widget = notebook.nametowidget(selected_tab)
    conn = root.tabs[selected_tab_widget]
    last_timestamp_var = root.last_timestamps[selected_tab_widget]
    display_log(root, conn, last_timestamp_var.get())

def log_and_execute(func, *args, **kwargs):
    action = kwargs.pop('action_description', '')
    user = kwargs.pop('user', None)
    conn = kwargs.pop('conn', None)
    result = func(*args, **kwargs)
    if user and conn:
        log_action(user[0], user[1], action, conn)  # Pass user[1] (username) here
    return result


import tkinter as tk
from tkinter import ttk

'''
def setup_tab(root, tab, db_name, user):
    # Initialize the database connection
    conn = init_db(db_name)

    # Create a frame to hold the treeview
    data_frame = ttk.Frame(tab)
    data_frame.pack(fill='both', expand=True)

    # Create the treeview and store it in the tab
    treeview = ttk.Treeview(data_frame)
    treeview.pack(fill='both', expand=True)
    tab.treeview = treeview

    # Load data from the "daily_data" table and display it in the treeview
    df = get_dataframe(conn, "daily_data")
    if df is not None:
        df = df.fillna('')  # Replace NaN values with empty strings
        display_df_in_treeview(treeview, df)
        tab.treeview_df = df  # Store the dataframe in the tab

    # Bind a double-click event to the treeview
    treeview.bind('<Double-1>', lambda event: on_double_click(event, treeview, conn, user))

    # Create a frame to hold the buttons
    button_frame = ttk.Frame(tab)
    button_frame.pack(fill='x', pady=10)

    # Helper function to create buttons
    def create_button(parent, text, command):
        button = ttk.Button(parent, text=text, command=command)
        button.pack(side="left", padx=5)
        return button

    # Create all buttons with associated commands
    create_button(button_frame, "Load Excel",
                  lambda: log_and_execute(load_excel, treeview, conn, user, "Loaded Excel data"))
    create_button(button_frame, "Save to Database",
                  lambda: log_and_execute(save_to_db, treeview, conn, user, "Saved to Database"))
    create_button(button_frame, "Save to Backup", lambda: backup_data_handler(root, conn, user))
    create_button(button_frame, "Import Data",
                  lambda: log_and_execute(import_data_handler, root, conn, user, "Imported Data"))
    create_button(button_frame, "Execute SQL Query",
                  lambda: log_and_execute(execute_sql_query, conn, user, "Executed SQL Query"))
    create_button(button_frame, "Download Backup",
                  lambda: log_and_execute(download_backup, conn, user, "Downloaded Backup"))
    create_button(button_frame, "Download in Excel",
                  lambda: log_and_execute(download_excel, conn, user, "Downloaded in Excel"))
    create_button(button_frame, "Reports", lambda: log_and_execute(open_report_window, conn, user, "Opened Reports"))

'''
def setup_tab(root, tab, db_name, user):
    conn = init_db(db_name)

    data_frame = ttk.Frame(tab)
    data_frame.pack(fill='both', expand=True)
    tree = ttk.Treeview(data_frame)
    tree.pack(fill='both', expand=True)
    # Store the treeview in the tab
    tab.tree = tree

    # Load data from "daily_data" table and display it
    df = get_dataframe(conn, "daily_data")
    if df is not None:
        df = df.fillna('')  # Ensure NaN values are replaced with empty strings
        display_df_in_treeview(tree, df)
        tab.treeview_df = df  # Store the dataframe as well

    tree.bind('<Double-1>', lambda event: on_double_click(event, tree, conn, user))

    button_frame = ttk.Frame(tab)
    button_frame.pack(fill='x', pady=10)

    load_button = ttk.Button(button_frame, text="Load Excel",
                             command=lambda: log_and_execute(load_excel, tree, action_description="Loaded Excel data",
                                                             user=user, conn=conn))
    load_button.pack(side="left", padx=5)

    #save_button = ttk.Button(button_frame, text="Save to Database",command=lambda: log_and_execute(save_to_db, tree, conn,action_description="Saved to Database", user=user))
    save_button = ttk.Button(button_frame, text="Save to Database",
                             command=lambda: log_and_execute(save_to_db, tree, conn, user,
                                                             action_description="Saved to Database"))
    save_button.pack(side="left", padx=5)

    backup_button = ttk.Button(button_frame, text="Save to Backup",
                               command=lambda: backup_data_handler(root, conn, user))
    backup_button.pack(side="left", padx=5)

    import_button = ttk.Button(button_frame, text="Import Data",
                               command=lambda: log_and_execute(import_data_handler, root, conn,
                                                               action_description="Imported Data", user=user))
    import_button.pack(side="left", padx=5)

    query_button = ttk.Button(button_frame, text="Execute SQL Query",
                              command=lambda: log_and_execute(execute_sql_query, conn,
                                                              action_description="Executed SQL Query", user=user))
    query_button.pack(side="left", padx=5)

    download_button = ttk.Button(button_frame, text="Download Backup",
                                 command=lambda: log_and_execute(download_backup, conn,
                                                                 action_description="Downloaded Backup", user=user))
    download_button.pack(side="left", padx=5)

    excel_button = ttk.Button(button_frame, text="Download in Excel",
                              command=lambda: log_and_execute(download_excel, conn,
                                                              action_description="Downloaded in Excel", user=user))
    excel_button.pack(side="left", padx=5)

    report_button = ttk.Button(button_frame, text="Reports", command=lambda: log_and_execute(open_report_window, conn,
                                                                                             action_description="Opened Reports",
                                                                                             user=user))
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

    login_button = ttk.Button(root, text="Login",
                              command=lambda: authenticate_callback(username_entry.get(), password_entry.get()))
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

    add_button = ttk.Button(top, text="Add",
                            command=lambda: add_user_handler(username_entry.get(), password_entry.get(), conn, top))
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

    update_button = ttk.Button(top, text="Update",
                               command=lambda: update_user_handler(user_id_entry.get(), username_entry.get(),
                                                                   password_entry.get(), conn, top))
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

    update_button = ttk.Button(top, text="Update",
                               command=lambda: update_user_handler(user_id, username_entry.get(), password_entry.get(),
                                                                   conn, top))
    update_button.pack(pady=5)

    delete_button = ttk.Button(top, text="Delete", command=lambda: delete_user_handler(user_id, conn, top))
    delete_button.pack(pady=5)


def open_view_logs_window(root, conn):
    top = Toplevel(root)
    top.title("View Logs")

    tree = ttk.Treeview(top)
    tree.pack(fill='both', expand=True)

    cursor = conn.cursor()
    cursor.execute(
        "SELECT logs.id, users.username, logs.action, logs.timestamp FROM logs INNER JOIN users ON logs.user_id = users.id")
    logs = cursor.fetchall()

    tree["columns"] = ("ID", "User", "Action", "Timestamp")
    tree["show"] = "headings"

    for col in tree["columns"]:
        tree.heading(col, text=col)

    for log_row in logs:
        tree.insert("", "end", values=log_row)


def logout(root, conn):
    root.destroy()
