import tkinter as tk
from tkinter import ttk, messagebox
from design import setup_ui, show_login_screen
from logic import update_status_bar, schedule_daily_backup
from database import init_db, init_auth_db

def on_closing():
    if messagebox.askokcancel("Quit", "Do you want to quit?"):
        root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # Hide the main window until login is successful

    # Initialize the authentication database
    auth_conn = init_auth_db()

    # Show login screen
    logged_in_user = show_login_screen(root, auth_conn)
    if not logged_in_user:
        root.destroy()  # Close the root if login fails
        exit()

    # Show the main window after successful login
    root.deiconify()

    db_names = ["test_db1", "test_db2", "test_db3", "test_db4"]
    conns = [init_db(db_name) for db_name in db_names]

    # Setup UI based on the logged-in user's role
    setup_ui(root, conns, logged_in_user, auth_conn)
    for conn in conns:
        schedule_daily_backup(conn)

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
