import sqlite3
import pandas as pd
import hashlib
import pandas as pd
def init_db(db_name):
    conn = sqlite3.connect(f"{db_name}.db", check_same_thread=False)
    conn.execute('PRAGMA journal_mode=WAL;')  # Enable WAL mode
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

def get_table_hash(conn, table_name):
    """Compute a hash of the entire table."""
    query = f"SELECT * FROM {table_name}"
    df = pd.read_sql_query(query, conn)
    table_str = df.to_string().encode('utf-8')
    return hashlib.sha256(table_str).hexdigest()