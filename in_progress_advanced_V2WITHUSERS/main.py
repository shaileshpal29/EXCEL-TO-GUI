import tkinter as tk
from tkinter import ttk, messagebox
from design import setup_ui, setup_login_screen
from logic import update_status_bar, schedule_daily_backup
from database import init_db
from auth import login, log_action

def on_closing():
    if messagebox.askokcancel("Quit", "Do you want to quit?"):
        root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Data Entry and Reporting App")
    user_conn = init_db("user_management")

    def authenticate(username, password):
        user = login(username, password, user_conn)
        if user:
            root.deiconify()
            login_window.destroy()
            setup_ui(root, ["test1", "test2", "test3", "test4"])  # Pass the database names as a list
            log_action(user[0], "Logged in", user_conn)
        else:
            messagebox.showerror("Login Failed", "Invalid username or password")

    login_window = tk.Toplevel(root)
    setup_login_screen(login_window, authenticate)
    root.withdraw()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
