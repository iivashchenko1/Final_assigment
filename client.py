"""
TCP chat client for the final SEP300 assignment.

This program connects to the chat server, sends user input to the server,
and prints all messages received from the server.
"""

import socket # To connect to the server
import threading # to listen to server messages in the background
import sys # to call sys.exit if the server disconnects

# The server must use the same HOST and PORT as in server.py.
SERVER_HOST = "127.0.0.1"  # localhost
SERVER_PORT = 5000        # must match PORT in server.py

def send_line(sock: socket.socket, text: str) -> None:
    """
    Send a line of text to the server, adding a newline at the end.
    """
    data = (text + "\n").encode("utf-8")
    sock.sendall(data)

def listen_to_server(sock: socket.socket) -> None:
    """
    Continuously read lines from the server and print them.

    Runs in a separate thread so that the main thread can handle user input.
    """
    # Wrap the socket as a file-like object so we can use .readline().
    file_obj = sock.makefile("r", encoding="utf-8")

    try:
        while True:
            line = file_obj.readline()
            if not line:
                # Server closed the connection.
                print("\n[INFO] Server closed the connection.")
                # Exit the whole program.
                sys.exit(0)

            # Strip the newline and print the message.
            line = line.rstrip("\n")
            print(f"\n{line}")
            print("> ", end="", flush=True)  # re-show prompt
    except Exception as exc:
        print(f"\n[ERROR] Connection error: {exc}")
        sys.exit(1)

def main() -> None:
    """
    Connect to the chat server and start the send/receive loops.
    """
    # 1. Create a TCP socket.
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # 2. Connect to the server.
        sock.connect((SERVER_HOST, SERVER_PORT))
    except OSError as exc:
        print(f"Could not connect to server at {SERVER_HOST}:{SERVER_PORT}: {exc}")
        return

    print(f"Connected to chat server at {SERVER_HOST}:{SERVER_PORT}")
    print("Follow the instructions from the server to register or log in.")
    print("Type '/quit' to exit.\n")

    # 3. Start the background listener thread.
    listener_thread = threading.Thread(
        target=listen_to_server,
        args=(sock,),
        daemon=True,  # exits automatically when main thread exits
    )
    listener_thread.start()

    # 4. Main loop: read user input and send it to the server.
    try:
        while True:
            # Show a prompt and read a line from the user.
            user_input = input("> ").strip()
            if not user_input:
                continue

            # If the user types /quit, send it and break.
            if user_input == "/quit":
                send_line(sock, user_input)
                break

            # Otherwise, send the line to the server.
            send_line(sock, user_input)
    except KeyboardInterrupt:
        print("\n[INFO] KeyboardInterrupt: exiting.") # IF we want to exit by Ctrl+C
    finally:
        # Close the socket when done.
        try:
            sock.close()
        except OSError:
            pass


if __name__ == "__main__":
    main()
