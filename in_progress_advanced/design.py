from tkinter import ttk, Menu, Label, Toplevel, Button, simpledialog, messagebox, filedialog
from logic import load_excel, save_to_db, generate_report, download_excel, update_status_bar, on_double_click, get_dataframe, display_df_in_treeview
from logic import backup_data_handler, import_data_handler, execute_sql_query, download_backup, log_user_action

from tkinter import ttk, Toplevel, messagebox
from database import validate_login, get_user_permissions


def show_login_screen(root, auth_conn):
    login_screen = Toplevel(root)
    login_screen.title("Login")

    user = None  # Initialize user to None

    def login():
        nonlocal user  # Allow access to the outer user variable
        username = username_entry.get()
        password = password_entry.get()
        user = validate_login(auth_conn, username, password)
        if user:
            login_screen.destroy()  # Close the login window on successful login
        else:
            messagebox.showerror("Error", "Invalid username or password")

    username_label = ttk.Label(login_screen, text="Username:")
    username_label.pack(pady=5)
    username_entry = ttk.Entry(login_screen)
    username_entry.pack(pady=5)

    password_label = ttk.Label(login_screen, text="Password:")
    password_label.pack(pady=5)
    password_entry = ttk.Entry(login_screen, show="*")
    password_entry.pack(pady=5)

    login_button = ttk.Button(login_screen, text="Login", command=login)
    login_button.pack(pady=10)

    root.wait_window(login_screen)  # Wait until the login window is closed
    return user  # Return the logged-in user details





def setup_ui(root, conns, logged_in_user, auth_conn):
    style = ttk.Style()
    style.configure("TNotebook.Tab", padding=[10, 10], font=('Arial', 10, 'bold'), background='#d1e0e0')
    style.configure("TButton", padding=[5, 5], font=('Arial', 10, 'bold'), background='#98b4b4')
    style.configure("TFrame", background="#f0f0f0")
    style.configure("TLabel", background="#f0f0f0")

    notebook = ttk.Notebook(root)
    notebook.pack(fill='both', expand=True)

    tabs = []
    tab_names = ["test1", "test2", "test3", "test4"]

    # Fetch user's permissions from the correct database
    user_permissions = get_user_permissions(auth_conn, logged_in_user['id'])

    if not user_permissions:
        messagebox.showerror("Error", "User has no permissions to view any tabs.")
        root.quit()  # Exit the application if no permissions

    for name, conn in zip(tab_names, conns):
        if user_permissions.get(name, {}).get('can_view'):
            tab = ttk.Frame(notebook)
            notebook.add(tab, text=name)
            tabs.append(tab)
            setup_tab(root, tab, conn, logged_in_user, user_permissions.get(name))
        else:
            print(f"User lacks permission for tab: {name}")

    if not tabs:
        messagebox.showerror("Error", "No tabs available for this user.")
        root.quit()  # Exit the application if no tabs are available

    menubar = Menu(root)
    root.config(menu=menubar)
    file_menu = Menu(menubar, tearoff=0)
    menubar.add_cascade(label="File", menu=file_menu)
    file_menu.add_command(label="Exit", command=root.quit)

    status_bar = Label(root, text="Last Updated: Never", bd=1, relief="sunken", anchor="w")
    status_bar.pack(side="bottom", fill="x")
    root.status_bar = status_bar  # Store reference to status bar in root


def setup_tab(root, tab, conn, logged_in_user, permissions):
    data_frame = ttk.Frame(tab)
    data_frame.pack(fill='both', expand=True)
    tree = ttk.Treeview(data_frame)
    tree.pack(fill='both', expand=True)

    # Load data from "daily_data" table and display it
    df = get_dataframe(conn, "daily_data")
    if df is not None:
        df = df.fillna('')  # Ensure NaN values are replaced with empty strings
        display_df_in_treeview(tree, df)

    # Add Treeview editable functionality
    tree.bind('<Double-1>', lambda event: on_double_click(event, tree, logged_in_user, conn))

    button_frame = ttk.Frame(tab)
    button_frame.pack(fill='x', pady=10)

    if permissions['can_edit']:
        load_button = ttk.Button(button_frame, text="Load Excel", command=lambda: load_excel(tree))
        load_button.pack(side="left", padx=5)

        save_button = ttk.Button(button_frame, text="Save to Database", command=lambda: save_to_db(tree, conn, logged_in_user))
        save_button.pack(side="left", padx=5)

    if permissions['can_delete']:
        backup_button = ttk.Button(button_frame, text="Save to Backup", command=lambda: backup_data_handler(root, conn))
        backup_button.pack(side="left", padx=5)

        import_button = ttk.Button(button_frame, text="Import Data", command=lambda: import_data_handler(root, conn))
        import_button.pack(side="left", padx=5)

    if permissions['can_edit']:
        query_button = ttk.Button(button_frame, text="Execute SQL Query", command=lambda: execute_sql_query(conn))
        query_button.pack(side="left", padx=5)

        download_button = ttk.Button(button_frame, text="Download Backup", command=lambda: download_backup(conn))
        download_button.pack(side="left", padx=5)

        excel_button = ttk.Button(button_frame, text="Download in Excel", command=lambda: download_excel_data(conn))
        excel_button.pack(side="left", padx=5)

        report_button = ttk.Button(button_frame, text="Reports", command=lambda: open_report_window(conn))
        report_button.pack(side="left", padx=5)

def view_logs_window(root, conn, logged_in_user):
    top = Toplevel(root)
    top.title("View Logs")
    tree = ttk.Treeview(top)
    tree.pack(fill='both', expand=True)

    df = get_dataframe(conn, "logs")
    if df is not None:
        df = df.fillna('')  # Ensure NaN values are replaced with empty strings
        display_df_in_treeview(tree, df)

def download_excel_data(conn):
    file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx;*.xls")])
    if file_path:
        try:
            df = get_dataframe(conn, "backup_data")
            if df is not None:
                df.to_excel(file_path, index=False)
                messagebox.showinfo("Success", "Data downloaded successfully!")
            else:
                messagebox.showinfo("No Data", "No data available to download.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

def open_report_window(conn):
    top = Toplevel()
    top.title("Generate Report")

    start_label = ttk.Label(top, text="Start Date (YYYY-MM-DD):")
    start_label.pack(pady=5)
    start_entry = ttk.Entry(top)
    start_entry.pack(pady=5)

    end_label = ttk.Label(top, text="End Date (YYYY-MM-DD):")
    end_label.pack(pady=5)
    end_entry = ttk.Entry(top)
    end_entry.pack(pady=5)

    generate_button = ttk.Button(top, text="Generate Report",
                                 command=lambda: generate_report_with_filter(conn, start_entry.get(), end_entry.get(), top))
    generate_button.pack(pady=20)

def generate_report_with_filter(conn, start_date, end_date, top):
    try:
        df = pd.read_sql_query(f"SELECT * FROM backup_data WHERE Bkp_Date_time BETWEEN '{start_date}' AND '{end_date}'", conn)
        if not df.empty:
            report_window = Toplevel(top)
            report_window.title("Report")
            tree = ttk.Treeview(report_window)
            tree.pack(fill='both', expand=True)
            tree["columns"] = list(df.columns)
            tree["show"] = "headings"
            for col in tree["columns"]:
                tree.heading(col, text=col)
            df_rows = df.to_numpy().tolist()
            for row in df_rows:
                tree.insert("", "end", values=row)
        else:
            messagebox.showinfo("No Data", "No data available for the selected date range.")
    except Exception as e:
        messagebox.showerror("Error", str(e))
