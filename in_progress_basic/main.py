import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from design import setup_ui
from logic import update_status_bar, schedule_daily_backup, start_data_refresh
from database import init_db

def admin_login():
    while True:
        username = simpledialog.askstring("Admin Login", "Enter Username:")
        password = simpledialog.askstring("Admin Login", "Enter Password:", show='*')
        if username == "admin" and password == "admin":
            return True
        else:
            messagebox.showerror("Login Failed", "Invalid Username or Password. Please try again.")

def on_closing():
    if messagebox.askokcancel("Quit", "Do you want to quit?"):
        root.destroy()

if __name__ == "__main__":
    if not admin_login():
        exit()

    root = tk.Tk()
    root.title("Data Entry and Reporting App")

    db_names = ["test_db1", "test_db2", "test_db3", "test_db4"]
    conns = [init_db(db_name) for db_name in db_names]

    setup_ui(root, conns)
    start_data_refresh(root, db_names)  # Start the data refresh process

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
