import tkinter as tk
from tkinter import ttk, messagebox
from database import init_db

def show_login_window(on_login):
    login_window = tk.Toplevel()
    login_window.title("Login")

    tk.Label(login_window, text="Username:").grid(row=0, column=0, padx=10, pady=10)
    username_entry = ttk.Entry(login_window)
    username_entry.grid(row=0, column=1, padx=10, pady=10)

    tk.Label(login_window, text="Password:").grid(row=1, column=0, padx=10, pady=10)
    password_entry = ttk.Entry(login_window, show="*")
    password_entry.grid(row=1, column=1, padx=10, pady=10)

    def attempt_login():
        username = username_entry.get()
        password = password_entry.get()
        conn = init_db("user_management")
        user = get_user(conn, username)
        if user and user[2] == password:
            messagebox.showinfo("Login Success", f"Welcome {username}!")
            on_login(username)
            login_window.destroy()
        else:
            messagebox.showerror("Login Failed", "Invalid username or password")

    login_button = ttk.Button(login_window, text="Login", command=attempt_login)
    login_button.grid(row=2, columnspan=2, pady=10)

    login_window.grab_set()
    login_window.wait_window()
