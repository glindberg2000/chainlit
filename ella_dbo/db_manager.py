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
                            auth0_user_id text NOT NULL,
                            memgpt_user_id text,
                            email text,
                            name text,
                            roles text
                          );"""
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except sqlite3.Error as e:
        print(e)

def upsert_user(conn, auth0_user_id, email=None, name=None, roles=None, memgpt_user_id=None):
    """
    Insert a new user or update an existing user in the users table.
    This function allows for selective updating of user information based on what is provided,
    without wiping or requiring existing data.
    """
    cur = conn.cursor()

    # Initialize SQL update parts and parameters list
    update_parts = []
    params = []

    # Add provided values to the update parts and params, if available
    if email is not None:
        update_parts.append("email = ?")
        params.append(email)
    if name is not None:
        update_parts.append("name = ?")
        params.append(name)
    if roles is not None:
        # Convert list of roles to a comma-separated string if roles are provided
        roles_str = ", ".join(roles) if isinstance(roles, list) else roles
        update_parts.append("roles = ?")
        params.append(roles_str)
    if memgpt_user_id is not None:
        update_parts.append("memgpt_user_id = ?")
        params.append(memgpt_user_id)

    # Check if user already exists
    cur.execute("SELECT * FROM users WHERE auth0_user_id=?", (auth0_user_id,))
    existing_user = cur.fetchone()

    if existing_user:
        # Only proceed with update if there are fields to update
        if update_parts:
            sql = f"UPDATE users SET {', '.join(update_parts)} WHERE auth0_user_id = ?"
            params.append(auth0_user_id)
            cur.execute(sql, params)
    else:
        # Insert new user with whatever information is provided
        fields = ['auth0_user_id'] + [field.split(" ")[0] for field in update_parts]
        placeholders = ["?"] * len(fields)
        sql = f"INSERT INTO users({', '.join(fields)}) VALUES({', '.join(placeholders)})"
        cur.execute(sql, [auth0_user_id] + params)
    
    conn.commit()

def get_memgpt_user_id(conn, auth0_user_id):
    """
    Retrieve the MemGPT user ID for a given Auth0 user ID.

    Parameters:
    - conn: The database connection object.
    - auth0_user_id: The Auth0 user ID.

    Returns:
    - The MemGPT user ID if found, None otherwise.
    """
    sql = '''SELECT memgpt_user_id FROM users WHERE auth0_user_id = ?'''
    cur = conn.cursor()
    cur.execute(sql, (auth0_user_id,))
    result = cur.fetchone()
    return result[0] if result else None

    
# close the database connection if needed
def close_connection(conn):
    """Close a database connection."""
    if conn:
        conn.close()
