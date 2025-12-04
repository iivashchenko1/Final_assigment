"""
TCP chat server for the final SEP300 assignment.

Responsibilities:
- listen for incoming TCP connections on a fixed PORT,
- handle registration and login using the database module,
- broadcast chat messages to all connected clients,
- store chat messages in the SQLite database.
"""

import socket 
import threading # Run each client connection in its own thread

from database import ( # We reuse all the database that we created before
    init_db,
    create_user,
    authenticate_user,
    save_message,
    get_recent_messages,
)

# Server configuration: one host, one port.
HOST = "0.0.0.0"   # Listen on all network interfaces and accept connection only on IP. 
PORT = 5000       # You can change this if you want to one port for all clients.

# Global list of connected clients.
# Each item is a dictionary: {"conn": socket_object, "username": str}
clients: list[dict] = []  

# A lock so that multiple threads can modify 'clients' safely.
clients_lock = threading.Lock() # perevents race conditoins when several threads try to modify the clients list at the same time.

def send_line(conn: socket.socket, text: str) -> None:
    """
    Send a single line of text to the client, adding a newline at the end.
    """
    data = (text + "\n").encode("utf-8") #Ensure that client sees full message by encoding it to bytes
    conn.sendall(data) # sends all bytes

def broadcast_message(sender_username: str, content: str) -> None:
    """
    Save a chat message to the database and send it to all connected clients.
    """
    # 1) Save in the database.
    save_message(sender_username, content) # Use our database module 

    # 2) Prepare the line to send to clients.
    line = f"[{sender_username}] {content}" # simple format for chat message

    # 3) Send to every connected client.
    with clients_lock:
        # Make a copy so we don't get issues if the list changes while iterating.
        current_clients = list(clients)

    for client in current_clients:
        conn = client["conn"]
        try:
            send_line(conn, line)
        except OSError:
            # If sending fails (client closed connection), ignore here.
            # The client thread will clean up.
            continue

def handle_client(conn: socket.socket, addr) -> None:
    """
    Handle a single client connection in its own thread.
    """
    print(f"[INFO] New connection from {addr}")
    username: str | None = None

    # Wrap the raw socket in a file-like object so we can use .readline().
    file_obj = conn.makefile("r", encoding="utf-8")

    try:
        # --- Step 1: Welcome and authentication ---
        send_line(conn, "Welcome to the chat server!")
        send_line(conn, "Type 'register' to create an account or 'login' to sign in:")

        while username is None:
            command = file_obj.readline() # Turns the socket into a file-like object so we call readline
            if not command:
                # Client disconnected before doing anything.
                print(f"[INFO] {addr} disconnected during auth.")
                return

            command = command.strip().lower()

            if command == "register":
                # Ask for username and password and call create_user.
                send_line(conn, "Choose a username:")
                uname = file_obj.readline()
                if not uname:
                    return
                uname = uname.strip()

                send_line(conn, "Choose a password:")
                pw = file_obj.readline()
                if not pw:
                    return
                pw = pw.strip()

                if not uname or not pw:
                    send_line(conn, "Username and password cannot be empty. Try again.")
                    continue

                if create_user(uname, pw):
                    send_line(conn, "Account created successfully! Type 'login' to sign in.") #Infrom if it is successful
                else:
                    send_line(conn, "Username already exists. Try another username.")#Inform if username is already taken

            elif command == "login":
                # Ask for username and password and call authenticate_user.
                send_line(conn, "Username:")
                uname = file_obj.readline()
                if not uname:
                    return
                uname = uname.strip()

                send_line(conn, "Password:")
                pw = file_obj.readline()
                if not pw:
                    return
                pw = pw.strip()

                if authenticate_user(uname, pw):
                    username = uname
                    send_line(conn, f"Login successful. Welcome, {username}!") # If returs True, login is successful. We set username to exit the loop
                else:
                    send_line(conn, "Invalid username or password. Try again.") # Failed with username or password
            else:
                send_line(conn, "Please type either 'register' or 'login'.") # Asking to choose an action .

        # At this point, username is set → user is authenticated.

        # Add this client to the global clients list.
        with clients_lock:
            clients.append({"conn": conn, "username": username})

        # Optionally send recent history.
        send_line(conn, "--- Recent messages ---")
        for u, content, created_at in get_recent_messages():
            send_line(conn, f"[{created_at}] {u}: {content}")
        send_line(conn, "--- End of history ---")

        # Inform others.
        broadcast_message("SYSTEM", f"{username} has joined the chat.")

        # --- Step 2: Main chat loop ---
        send_line(conn, "You are now in the chatroom. Type messages and press Enter.")
        send_line(conn, "Type '/quit' to exit.")

        while True:
            line = file_obj.readline()
            if not line:
                # Client closed the connection.
                print(f"[INFO] {username} at {addr} disconnected.")
                break

            message = line.strip()
            if not message:
                continue

            if message == "/quit":
                send_line(conn, "Goodbye!")
                break

            # Broadcast this message to everyone.
            broadcast_message(username, message)

    except Exception as exc:
        # Any unexpected error: log it server-side.
        print(f"[ERROR] Exception in client handler for {addr}: {exc}")
    finally:
        # Remove client from global list if logged in.
        if username is not None:
            with clients_lock:
                clients[:] = [
                    c for c in clients if c["conn"] is not conn
                ]
            broadcast_message("SYSTEM", f"{username} has left the chat.")

        conn.close()
        print(f"[INFO] Connection with {addr} closed.")

    
def main() -> None:
    """
    Entry point for the chat server: initialize the database,
    create a listening socket, and handle incoming connections.
    """
    # Make sure the database and tables exist before any clients connects.
    init_db()

    # Create a TCP socket.
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Allow quick reuse of the same port after restarting the server.
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Bind the socket to the chosen HOST and PORT.
    server_sock.bind((HOST, PORT))

    # Start listening and accepting for incoming connections.
    server_sock.listen()
    print(f"[INFO] Chat server listening on {HOST}:{PORT}")

    try:
        while True:
            # Accept a new client connection.
            conn, addr = server_sock.accept()

            # Start a new thread for this client.
            thread = threading.Thread(
                target=handle_client,
                args=(conn, addr),
                daemon=True,  # Daemon thread will exit when main program exits.
            )
            thread.start()
    except KeyboardInterrupt:
        print("\n[INFO] Server shutting down...")
    finally:
        server_sock.close()


if __name__ == "__main__":
    main()



