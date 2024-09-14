import sqlite3
import pandas as pd
import os


def init_auth_db():
    # Check if the database file already exists
    db_exists = os.path.exists("auth_db.sqlite")

    # Connect to the authentication database
    conn = sqlite3.connect("auth_db.sqlite")
    cursor = conn.cursor()

    # Create users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('admin', 'user'))
    )
    """)

    # Create permissions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS permissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        notebook_name TEXT NOT NULL,
        can_view BOOLEAN DEFAULT FALSE,
        can_edit BOOLEAN DEFAULT FALSE,
        can_delete BOOLEAN DEFAULT FALSE,
        button_permissions TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)

    # Create logs table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        notebook_name TEXT NOT NULL,
        operation_type TEXT NOT NULL CHECK(operation_type IN ('insert', 'update', 'delete')),
        old_value TEXT,
        new_value TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)

    # Insert default admin user if the database was just created
    if not db_exists:
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", ('admin', 'admin', 'admin'))

    conn.commit()

    # Debugging: Check the tables that exist in the database
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables in the database:", tables)

    return conn

def init_db(db_name):
    conn = sqlite3.connect(f"{db_name}.db")
    create_table_if_not_exists(conn, "daily_data")
    return conn

def create_table_if_not_exists(conn, table_name):
    cursor = conn.cursor()
    if table_name == "daily_data":
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            col1 TEXT,
            col2 TEXT,
            col3 TEXT,
            date_column TEXT DEFAULT (datetime('now', 'localtime'))
        )
        """)
    conn.commit()

def create_table_from_df(conn, df, table_name):
    df.to_sql(table_name, conn, if_exists='replace', index=False)

def get_dataframe(conn, table_name):
    query = f"SELECT * FROM {table_name}"
    try:
        df = pd.read_sql_query(query, conn)
        if df.empty:
            return None
        return df
    except Exception as e:
        print(f"Error fetching data from {table_name}: {e}")
        return None

def backup_data(conn):
    cursor = conn.cursor()

    # Get the column names from daily_data
    cursor.execute("PRAGMA table_info(daily_data)")
    columns_info = cursor.fetchall()
    columns = [info[1] for info in columns_info]

    # Check if backup_data table exists and create if it does not
    cursor.execute("PRAGMA table_info(backup_data)")
    existing_columns_info = cursor.fetchall()
    existing_columns = [info[1] for info in existing_columns_info]

    if not existing_columns:
        columns_def = ", ".join([f'"{col}" TEXT' for col in columns])
        create_table_query = f"""
            CREATE TABLE IF NOT EXISTS backup_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                {columns_def},
                "Bkp_Date_time" TEXT
            )
        """
        print(f"Executing SQL: {create_table_query}")  # Debug print
        cursor.execute(create_table_query)

    # Insert data from daily_data to backup_data
    columns_str = ", ".join([f'"{col}"' for col in columns])
    delete_query = f'DELETE FROM backup_data WHERE DATE("Bkp_Date_time") = DATE("now", "localtime")'
    print(f"Executing SQL: {delete_query}")  # Debug print
    cursor.execute(delete_query)

    insert_query = f"""
        INSERT INTO backup_data ({columns_str}, "Bkp_Date_time")
        SELECT {columns_str}, DATETIME('now', 'localtime') FROM daily_data
    """
    print(f"Executing SQL: {insert_query}")  # Debug print
    cursor.execute(insert_query)
    conn.commit()

def insert_backup_data(conn, df, date_time):
    cursor = conn.cursor()

    # Get the column names from the dataframe
    columns = df.columns.tolist()

    # Check if backup_data table exists and create if it does not
    cursor.execute("PRAGMA table_info(backup_data)")
    existing_columns_info = cursor.fetchall()
    existing_columns = [info[1] for info in existing_columns_info]

    if not existing_columns:
        columns_def = ", ".join([f'"{col}" TEXT' for col in columns])
        create_table_query = f"""
            CREATE TABLE IF NOT EXISTS backup_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                {columns_def},
                "Bkp_Date_time" TEXT
            )
        """
        print(f"Executing SQL: {create_table_query}")  # Debug print
        cursor.execute(create_table_query)

    # Insert data from dataframe to backup_data
    columns_str = ", ".join([f'"{col}"' for col in columns])
    for _, row in df.iterrows():
        values = tuple(row) + (date_time,)
        placeholders = ", ".join(["?"] * len(values))
        insert_query = f"""
            INSERT INTO backup_data ({columns_str}, "Bkp_Date_time")
            VALUES ({placeholders})
        """
        print(f"Executing SQL: {insert_query} with values {values}")  # Debug print
        cursor.execute(insert_query, values)
    conn.commit()

def execute_query(conn, query):
    cursor = conn.cursor()
    cursor.execute(query)
    columns = [desc[0] for desc in cursor.description]
    result = cursor.fetchall()
    return pd.DataFrame(result, columns=columns)

# New functions for authentication and role management



def validate_login(conn, username, password):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()
    if user:
        return {'id': user[0], 'username': user[1], 'role': user[3]}
    else:
        return None

def get_user_permissions(conn, user_id):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM permissions WHERE user_id = ?", (user_id,))
    permissions = cursor.fetchall()
    permission_dict = {}
    for permission in permissions:
        permission_dict[permission[2]] = {
            'can_view': permission[3],
            'can_edit': permission[4],
            'can_delete': permission[5],
            'button_permissions': permission[6].split(',') if permission[6] else []
        }
    return permission_dict

def log_action(conn, user_id, operation_type, notebook_name, old_value, new_value):
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO logs (user_id, notebook_name, operation_type, old_value, new_value, timestamp)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, notebook_name, operation_type, old_value, new_value, datetime.datetime.now()))
    conn.commit()
