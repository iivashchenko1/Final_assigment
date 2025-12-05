"""
Database helper functions for the chat application.

This module is responsible for:
- creating the SQLite database and tables (users and messages),
- inserting new users with hashed passwords,
- authenticating users during login,
- storing chat messages and retrieving them when needed.
"""

from datetime import datetime # To store when messages are sent

from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError # Help us to find Duplicate Username Error

from auth import hash_password, verify_password  #reuse our password helpers; this is SRP/DRY

# SQLite database URL. The file "chat.db" will be created in the project folder.
DATABASE_URL = "sqlite:///chat.db" # Tells where is our database exist

# Global SQLAlchemy engine object that knows how to connnect to database, similar to the examples in the lectures.
engine = create_engine(DATABASE_URL, echo=False)

def init_db() -> None: #Doesn't return anything , just create tables
    """
    Create the required database tables if they do not already exist.

    Tables:
        users(
            username TEXT PRIMARY KEY,
            password_salt TEXT NOT NULL,
            password_hash TEXT NOT NULL
        )

        messages(
            message_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """
    users_sql = """
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password_salt TEXT NOT NULL,
            password_hash TEXT NOT NULL
        )
    """

    messages_sql = """
        CREATE TABLE IF NOT EXISTS messages (
            message_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """

    # engine.begin() opens a connection and starts a transaction.
    # When the 'with' block ends, it automatically commits or rolls back.
    with engine.begin() as conn:
        conn.exec_driver_sql(users_sql) #Sends the Create table command to SQLite
        conn.exec_driver_sql(messages_sql)

def create_user(username: str, password: str) -> bool: #Return True or False
    """
    Create a new user account.

    Args:
        username: The username chosen by the user. Must be unique.
        password: The plain-text password provided during registration.

    Returns:
        True if the user was created successfully.
        False if the username already exists.
    """
    # First, hash the password using the helper from auth.py to turn it into a safe format.
    salt_hex, hash_hex = hash_password(password) 

    #Uses named parameters instead of putting them directly into the SQL string.
    #SQLAlchemy sends the values separately, so user input cannot break the SQL.
    insert_sql = """
        INSERT INTO users (username, password_salt, password_hash)
        VALUES (:username, :salt, :hash)
    """

    try:
        with engine.begin() as conn:
            conn.execute(
                text(insert_sql),
                {"username": username, "salt": salt_hex, "hash": hash_hex},
            )
        return True
    except IntegrityError:
        # This happens if the username already exists due to the PRIMARY KEY constraint.
        return False
        #iNSTEAD of crashing the program, we just return False
  


def _get_user_credentials(username: str) -> tuple[str, str] | None:
    """
    Fetch the stored (salt, hash) pair for a given username.

    Returns:
        (salt_hex, hash_hex) if the user exists, or None if not found.
    """
    query_sql = """
        SELECT password_salt, password_hash
        FROM users
        WHERE username = :username
    """

    with engine.connect() as conn: # We use engine.connect because we are only reading
        row = conn.execute(
            text(query_sql),
            {"username": username},
        ).first()
    
    if row is None:
        return None

    # row[0] and row[1] correspond to password_salt and password_hash.
    return row[0], row[1]
    
    """
    If no user found = row is None
    Otherwise row behaves like tuple
    If user doesn't exist , return None
    If they are exist, return the two stings.
    """

def authenticate_user(username: str, password: str) -> bool: # Return True or False
    """
    Check whether the given username / password pair is valid.

    Returns:
        True if the credentials are correct, False otherwise.
    """
    creds = _get_user_credentials(username)
    if creds is None:
        # No such user.
        return False

    salt_hex, stored_hash_hex = creds
    return verify_password(password, salt_hex, stored_hash_hex)


def save_message(username: str, content: str) -> None:
    """
    Store a chat message in the database.

    Args:
        username: The sender of the message (must be a valid logged-in user).
        content: The text of the message.
    """
    insert_sql = """
        INSERT INTO messages (username, content, created_at)
        VALUES (:username, :content, :created_at)
    """

    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")# Returns a nice readble string 

    with engine.begin() as conn:
        conn.execute(
            text(insert_sql),
            #Again we use SQL
            {
                "username": username,
                "content": content,
                "created_at": created_at,
            },
        )
        #No return Values; we just insert


def get_recent_messages(limit: int = 20) -> list[tuple[str, str, str]]:
    """
    Retrieve the most recent chat messages.

    Args:
        limit: Maximum number of messages to return (default: 20).

    Returns:
        A list of tuples (username, content, created_at), ordered from oldest to newest.
    """
    query_sql = """
        SELECT username, content, created_at
        FROM messages
        ORDER BY message_id DESC
        LIMIT :limit
    """

    with engine.connect() as conn:
        rows = conn.execute(
            text(query_sql),
            {"limit": limit},
        ).all()

    # rows are returned newest-first, so we reverse to show oldest-first.
    rows = list(rows)[::-1]

    return [(row[0], row[1], row[2]) for row in rows]


if __name__ == "__main__":
    # Simple manual test to make sure the module works on its own.
    print("Initializing database...")
    init_db()

    print("Creating a test user 'alice' with password 'secret'...")
    created = create_user("alice", "secret")
    print("Created:", created)

    print("Trying to login with correct password:", authenticate_user("alice", "secret"))
    print("Trying to login with wrong password:", authenticate_user("alice", "wrong"))

    print("Saving a test message...")
    save_message("alice", "Hello from the manual test!")

    print("Recent messages:")
    for username, content, created_at in get_recent_messages():
        print(f"[{created_at}] {username}: {content}")





