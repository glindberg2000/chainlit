# ella_dbo/db_manager.py

import sqlite3
import os

# Get the directory of the current file (__file__ is the path to the current script)
current_dir = os.path.dirname(__file__)

# Define the database file path as relative to the current directory
DB_FILE = os.path.join(current_dir, 'database.db')


def create_connection():
    """Create and return a database connection to the SQLite database specified by db_file."""
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
    except sqlite3.Error as e:
        print(e)
    return conn

def create_table(conn):
    """Create a table to store user info, given a connection."""
    create_table_sql = """CREATE TABLE IF NOT EXISTS users (
                            id integer PRIMARY KEY,
                            user_id text NOT NULL,
                            email text,
                            name text,
                            roles text
                          );"""
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except sqlite3.Error as e:
        print(e)


def upsert_user(conn, user_id, email, name, roles):
    """
    Insert a new user or update an existing user in the users table.
    Adjusted to handle roles as a string.
    """
    cur = conn.cursor()
    # Convert list of roles to a comma-separated string
    roles_str = ", ".join(roles) if isinstance(roles, list) else roles

    # Check if user already exists
    cur.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    existing_user = cur.fetchone()

    if existing_user:
        # Update existing user
        sql = '''UPDATE users 
                 SET email=?, name=?, roles=?
                 WHERE user_id=?'''
        cur.execute(sql, (email, name, roles_str, user_id))
    else:
        # Insert new user
        sql = '''INSERT INTO users(user_id, email, name, roles)
                 VALUES(?,?,?,?)'''
        cur.execute(sql, (user_id, email, name, roles_str))
    
    conn.commit()


# You might want to include a function to close the database connection if needed
def close_connection(conn):
    """Close a database connection."""
    if conn:
        conn.close()

# import sqlite3

# def create_connection(db_file):
#     """Create a database connection to the SQLite database."""
#     conn = None
#     try:
#         conn = sqlite3.connect(db_file)
#     except sqlite3.Error as e:
#         print(e)
#     return conn

# def create_table(conn):
#     """Create a table to store user info."""
#     create_table_sql = """CREATE TABLE IF NOT EXISTS users (
#                             id integer PRIMARY KEY,
#                             user_id text NOT NULL UNIQUE,
#                             email text,
#                             name text,
#                             roles text
#                           );"""
#     try:
#         c = conn.cursor()
#         c.execute(create_table_sql)
#     except sqlite3.Error as e:
#         print(e)

