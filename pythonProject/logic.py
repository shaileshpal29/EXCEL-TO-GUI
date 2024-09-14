import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, Entry, Toplevel, simpledialog
from database import create_table_from_df, get_dataframe, backup_data, insert_backup_data, execute_query, init_db, get_table_hash
import datetime
import threading
import time
import sqlite3
from auth import login, log_action
def load_excel(tree):
    file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx;*.xls")])
    if file_path:
        df = pd.read_excel(file_path)
        df = df.fillna('')
        display_df_in_treeview(tree, df)

def display_df_in_treeview(tree, df):
    tree.delete(*tree.get_children())
    tree["column"] = list(df.columns)
    tree["show"] = "headings"
    for col in tree["column"]:
        tree.heading(col, text=col)
    df_rows = df.to_numpy().tolist()
    for row in df_rows:
        tree.insert("", "end", values=row)
    for col in tree["column"]:
        tree.heading(col, text=col)
    tree.pack(fill='both', expand=True)
    add_summary(tree, df)
def add_summary(tree, df):
    # Clear any existing summary frame
    for child in tree.master.winfo_children():
        if isinstance(child, ttk.Frame):
            child.destroy()

    # Create a new summary frame
    summary_frame = ttk.Frame(tree.master)
    summary_frame.pack(fill='x', pady=5)

    # Add summary labels to the frame
    for col in df.columns:
        total = df[col].sum() if pd.api.types.is_numeric_dtype(df[col]) else len(df[col])
        label = ttk.Label(summary_frame, text=f"{col} Total: {total}")
        label.pack(side="left", padx=5)

def save_to_db(tree, conn, user):
    try:
        data = []
        for row_id in tree.get_children():
            row = tree.item(row_id)['values']
            data.append(row)
        df = pd.DataFrame(data, columns=tree["column"])
        df.to_sql("daily_data", conn, if_exists='replace', index=False)
        log_action(user[0], user[1], "Saved to Database", conn)
        update_status_bar(tree.master.master.master.master, "Data saved to database successfully!")
    except Exception as e:
        messagebox.showerror("Error", str(e))
        log_action(user[0], user[1], f"Failed to Save Database: {str(e)}", conn)



def generate_report(conn, start_date=None, end_date=None):
    query = "SELECT * FROM daily_data"
    if start_date and end_date:
        query += f" WHERE date_column BETWEEN '{start_date}' AND '{end_date}'"
    summary_df = pd.read_sql_query(query, conn)
    summary = summary_df.describe(include='all')
    summary_text = summary.to_string()
    messagebox.showinfo("Report", summary_text)

def download_excel(tree):
    try:
        data = []
        for row_id in tree.get_children():
            row = tree.item(row_id)['values']
            data.append(row)
        df = pd.DataFrame(data, columns=tree["column"])
        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                                 filetypes=[("Excel files", "*.xlsx;*.xls")])
        if file_path:
            df.to_excel(file_path, index=False)
            update_status_bar(tree.master.master.master.master, "Data downloaded as Excel successfully!")
    except Exception as e:
        messagebox.showerror("Error", str(e))

def update_status_bar(root, message):
    status_bar = root.status_bar
    status_bar.config(text=f"Last Updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}")

def schedule_daily_backup(db_name):
    def daily_backup():
        while True:
            conn = init_db(db_name)  # Reinitialize connection within the thread
            backup_data(conn)
            conn.close()
            time.sleep(86400)  # 24 hours in seconds

    threading.Thread(target=daily_backup, daemon=True).start()


def on_double_click(event, tree, conn, user):
    rowid = tree.identify_row(event.y)
    column = tree.identify_column(event.x)
    if rowid and column:
        row_values = tree.item(rowid)['values']
        column_index = int(column[1:]) - 1
        current_value = row_values[column_index]
        entry_popup(event.widget, current_value, rowid, column, tree, conn, user)

def entry_popup(tree, value, rowid, column, treeview, conn, user):
    top = Toplevel(tree)
    top.geometry("200x100")
    top.title("Edit Cell")
    entry = Entry(top)
    entry.insert(0, value)
    entry.pack(pady=20)
    entry.focus()
    entry.bind("<Return>", lambda event: on_return(event, entry, rowid, column, treeview, top, conn, user))
    entry.bind("<FocusOut>", lambda event: top.destroy())

def on_return(event, entry, rowid, column, treeview, top, conn, user):
    new_value = entry.get()
    old_value = treeview.item(rowid)['values'][int(column[1:]) - 1]
    if new_value != old_value:
        action = f"Updated row {rowid} column {column} from '{old_value}' to '{new_value}'"
        #log_action(user[0], action, conn)
        log_action(user[0], user[1], action, conn)  # Pass user[1] (username) here

    treeview.set(rowid, column=column, value=new_value)
    entry.destroy()
    top.destroy()
    update_status_bar(treeview.master.master.master.master, "Data modified")

def backup_data_handler(root, conn, user):
    try:
        print("Starting backup...")
        backup_data(conn)
        update_status_bar(root, "Data backed up successfully!")
        #print(f"Logging action for user: {user[0]}")
        print(f"Logging action for user: {user[1]}")
        log_action(user[0], user[1],"Saved to Backup", conn)
        #print("Action logged successfully.")

    except Exception as e:
        print(f"Error during backup: {e}")
        messagebox.showerror("Error", str(e))
        log_action(user[0], user[1],f"Failed to Save Backup: {str(e)}", conn)



def import_data_handler(root, conn):
    file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx;*.xls")])
    if file_path:
        df = pd.read_excel(file_path)
        date_time = simpledialog.askstring("Input", "Enter date and time (YYYY-MM-DD HH:MM:SS):")
        try:
            insert_backup_data(conn, df, date_time)
            update_status_bar(root, "Data imported successfully!")
        except Exception as e:
            messagebox.showerror("Error", str(e))

def execute_sql_query(conn):
    top = Toplevel()
    top.title("Execute SQL Query")

    query_label = ttk.Label(top, text="SQL Query:")
    query_label.pack(pady=5)
    query_entry = ttk.Entry(top, width=100)
    query_entry.pack(pady=5)

    def execute():
        query = query_entry.get()
        result_df = execute_query(conn, query)
        result_window = Toplevel(top)
        result_window.title("Query Result")

        tree = ttk.Treeview(result_window)
        tree.pack(fill='both', expand=True)
        tree["columns"] = list(result_df.columns)
        tree["show"] = "headings"

        for col in tree["columns"]:
            tree.heading(col, text=col)

        for row in result_df.to_numpy():
            tree.insert("", "end", values=row)

    execute_button = ttk.Button(top, text="Execute", command=execute)
    execute_button.pack(pady=5)

def download_backup(conn):
    file_path = filedialog.asksaveasfilename(defaultextension=".db", filetypes=[("SQLite files", "*.db")])
    if file_path:
        conn.backup(sqlite3.connect(file_path))
        update_status_bar(root, "Database backup downloaded successfully!")
def display_log(root, conn, last_timestamp):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT user_id, username, action, timestamp FROM logs WHERE timestamp > ? ORDER BY timestamp ASC",
        (last_timestamp,))
    logs = cursor.fetchall()

    log_window = root.log_window
    log_window.config(state='normal')

    for log in logs:
        user_id, username, action, timestamp = log
        #log_window.insert('end', f"{timestamp}: {user_id} {username} {action}\n")
        log_window.insert('end', f"{timestamp}: USER ID:{user_id} {action}\n")
    log_window.config(state='disabled')
    log_window.yview('end')

    if logs:
        last_timestamp = logs[-1][-1]

    return last_timestamp

def start_log_polling(root, conn, last_timestamp_var):
    last_timestamp = last_timestamp_var.get()
    last_timestamp = display_log(root, conn, last_timestamp)
    last_timestamp_var.set(last_timestamp)
    root.after(1000, start_log_polling, root, conn, last_timestamp_var)


def start_data_refresh(root, db_names):
    def refresh_data():
        last_hashes = [None] * len(db_names)
        while True:
            for i, (db_name, tab) in enumerate(zip(db_names, root.tabs)):
                conn = init_db(db_name)  # Open a new connection in this thread
                try:
                    current_hash = get_table_hash(conn, "daily_data")

                    if last_hashes[i] is None or current_hash != last_hashes[i]:
                        last_hashes[i] = current_hash
                        full_data_df = get_dataframe(conn, "daily_data")

                        # Ensure tree exists and refresh the data
                        if hasattr(tab, 'tree'):
                            display_df_in_treeview(tab.tree, full_data_df)
                            tab.treeview_df = full_data_df
                            update_status_bar(root,
                                              f"Data refreshed at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                except Exception as e:
                    print(f"Error refreshing data: {e}")
                finally:
                    conn.close()  # Ensure the connection is closed
            time.sleep(2)  # Poll every 2 seconds

    threading.Thread(target=refresh_data, daemon=True).start()