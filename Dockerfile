# -----------------------------------------------------------------------------
# Dockerfile for the chatroom SERVER
#
# This file defines how to build a Docker image that can run server.py
# inside an isolated container. The image includes:
#   - Python 3.12
#   - All dependencies listed in requirements.txt (SQLAlchemy)
#   - Our project files (server.py, database.py, auth.py, etc.)
#
# According to the assignment, since we are using SQLite, the database file
# (chat.db) can be kept inside the same container as the server. 
# -----------------------------------------------------------------------------


# 1) Base image:
#    Use the official Python 3.12 image with a slimmed-down Linux system.
#    This is very similar to the example from Lecture 10. 
FROM python:3.12-slim

# 2) Working directory inside the container:
#    All subsequent commands (COPY, RUN, CMD) will be relative to /app.
WORKDIR /app

# 3) Copy the dependency list and install them:
#    We copy ONLY requirements.txt first so Docker can cache this layer.
#    If requirements.txt does not change, Docker will not reinstall packages.
COPY requirements.txt .

# Install Python packages listed in requirements.txt inside the image.
# --no-cache-dir avoids keeping pip's cache, making the image smaller.
RUN pip install --no-cache-dir -r requirements.txt

# 4) Copy the rest of the project files into the image:
#    This includes server.py, client.py, auth.py, database.py, and any
#    other modules (plus chat.db if it already exists when building).
COPY . .

# 5) Expose the TCP port that the server listens on:
#    In server.py we configured the server to listen on port 5000.
#    EXPOSE 5000 documents that this container will use port 5000.
#    When running the container, we will map this to a port on the host
#    using:  docker run -p 5000:5000 ...
EXPOSE 5000

# 6) Default command:
#    When a container created from this image starts, it will run:
#        python server.py
#    This starts the chat server inside the container.
CMD ["python", "server.py"]
