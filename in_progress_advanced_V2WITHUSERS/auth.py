import sqlite3

def login(username, password, conn):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = cursor.fetchone()
    return user

def add_user(username, password, conn):
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def update_user(user_id, username, password, conn):
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET username=?, password=? WHERE id=?", (username, password, user_id))
    conn.commit()

def delete_user(user_id, conn):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()

def log_action(user_id, action, conn):
    cursor = conn.cursor()
    cursor.execute("INSERT INTO logs (user_id, action) VALUES (?, ?)", (user_id, action))
    conn.commit()
