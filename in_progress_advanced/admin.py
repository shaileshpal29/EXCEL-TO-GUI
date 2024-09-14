# admin.py (New file for admin interface functions)

import tkinter as tk
from tkinter import messagebox
import sqlite3

def manage_users():
    user_management_window = tk.Toplevel(root)
    user_management_window.title("User Management")

    tk.Label(user_management_window, text="Username:").grid(row=0, column=0)
    username_entry = tk.Entry(user_management_window)
    username_entry.grid(row=0, column=1)

    tk.Label(user_management_window, text="Password:").grid(row=1, column=0)
    password_entry = tk.Entry(user_management_window, show="*")
    password_entry.grid(row=1, column=1)

    tk.Label(user_management_window, text="Role:").grid(row=2, column=0)
    role_entry = tk.Entry(user_management_window)
    role_entry.grid(row=2, column=1)

    def add_user():
        username = username_entry.get()
        password = password_entry.get()
        role = role_entry.get()
        conn = sqlite3.connect('auth_db.sqlite')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, password, role))
        conn.commit()
        conn.close()
        messagebox.showinfo("Success", "User added successfully")
        user_management_window.destroy()

    tk.Button(user_management_window, text="Add User", command=add_user).grid(row=3, columnspan=2)
