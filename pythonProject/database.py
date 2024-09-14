import sqlite3
import pandas as pd
import hashlib

def init_db(db_name):
    conn = sqlite3.connect(f"{db_name}.db", check_same_thread=False)
    conn.execute('PRAGMA journal_mode=WAL;')  # Enable WAL mode
    create_table_if_not_exists(conn, "users")
    create_table_if_not_exists(conn, "logs")
    if db_name == "user_management":
        add_default_admin_user(conn)
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
    elif table_name == "users":
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
        """)
    elif table_name == "logs":
        cursor.execute("""
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    username TEXT,
                    action TEXT,
                        timestamp TEXT DEFAULT (datetime('now', 'localtime')),
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
                """)
        # Create trigger to automatically update username in logs
        cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS update_logs_username
                AFTER INSERT ON logs
                FOR EACH ROW
                BEGIN
                    UPDATE logs
                    SET username = (SELECT username FROM users WHERE id = NEW.user_id)
                    WHERE id = NEW.id;
                END;
                """)
    conn.commit()

def add_default_admin_user(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username='admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", ('admin', 'admin'))
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

    cursor.execute("PRAGMA table_info(daily_data)")
    columns_info = cursor.fetchall()
    columns = [info[1] for info in columns_info]

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
        cursor.execute(create_table_query)

    columns_str = ", ".join([f'"{col}"' for col in columns])
    delete_query = f'DELETE FROM backup_data WHERE DATE("Bkp_Date_time") = DATE("now", "localtime")'
    cursor.execute(delete_query)

    insert_query = f"""
        INSERT INTO backup_data ({columns_str}, "Bkp_Date_time")
        SELECT {columns_str}, DATETIME('now', 'localtime') FROM daily_data
    """
    cursor.execute(insert_query)
    conn.commit()

def insert_backup_data(conn, df, date_time):
    cursor = conn.cursor()

    columns = df.columns.tolist()
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
        cursor.execute(create_table_query)

    columns_str = ", ".join([f'"{col}"' for col in columns])
    for _, row in df.iterrows():
        values = tuple(row) + (date_time,)
        placeholders = ", ".join(["?"] * len(values))
        insert_query = f"""
            INSERT INTO backup_data ({columns_str}, "Bkp_Date_time")
            VALUES ({placeholders})
        """
        cursor.execute(insert_query, values)
    conn.commit()

def execute_query(conn, query):
    cursor = conn.cursor()
    cursor.execute(query)
    columns = [desc[0] for desc in cursor.description]
    result = cursor.fetchall()
    return pd.DataFrame(result, columns=columns)

def create_logs_table():
    conn = sqlite3.connect('user_management.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            action TEXT,
            timestamp TEXT DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS update_logs_username
        AFTER INSERT ON logs
        FOR EACH ROW
        BEGIN
            UPDATE logs
            SET username = (SELECT username FROM users WHERE id = NEW.user_id)
            WHERE id = NEW.id;
        END;
    ''')
    conn.commit()
    conn.close()

# Call this function when initializing the application
create_logs_table()

def get_table_hash(conn, table_name):
    """Compute a hash of the entire table."""
    query = f"SELECT * FROM {table_name}"
    df = pd.read_sql_query(query, conn)
    table_str = df.to_string().encode('utf-8')
    return hashlib.sha256(table_str).hexdigest()
