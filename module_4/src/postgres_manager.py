"""Provides a self-contained, monolithic PostgreSQL setup for a school project.

It initializes a Postgres data directory if necessary, starts Postgres as a subprocess,
creates a user, password, and database if missing, and provides a ready-to-use connection.

User Credentials:
- User: student
- Password: modernsoftwareconcepts
- Database: admissions
"""

import subprocess
import os
import atexit
import time
import shutil
import sys
import psycopg


DATA_DIR = "./pgdata"  # Directory where Postgres stores data
PG_PORT = 5432  # Port for Postgres server
PG_USER = "student"  # Postgres user for the project
PG_PASSWORD = "modernsoftwareconcepts"  # Postgres user password
PG_DB = "admissions"  # Database name


connection = None


def check_postgres_installed():
    """Check if the required PostgreSQL binaries ('postgres' and 'initdb') are installed."""
    if shutil.which("postgres") is None or shutil.which("initdb") is None:
        print("Error: Postgres binaries not found. Please install Postgres.")
        sys.exit(1)


def init_db():
    """Initialize the PostgreSQL data directory if it does not exist."""
    if not os.path.exists(DATA_DIR):
        print(f"Data directory '{DATA_DIR}' not found. Initializing...")

        result = subprocess.run(["initdb", "-D", DATA_DIR, "-U", PG_USER])

        if result.returncode != 0:
            print("Failed to initialize Postgres data directory.")
            sys.exit(1)

        print("Postgres data directory initialized.")


def stop_postgres(process):
    """Terminate the PostgreSQL subprocess."""
    print("Stopping Postgres...")

    if connection:
        connection.close()

    process.terminate()
    process.wait()


def setup_user_and_db():
    """Create the project user and database if they do not exist."""
    # Connect as default 'postgres' user
    conn = psycopg.connect(dbname="postgres", user=PG_USER, host="localhost", port=PG_PORT)
    conn.autocommit = True
    cur = conn.cursor()

    # Check if database exists, create if missing
    cur.execute("SELECT 1 FROM pg_database WHERE datname=%s;", [PG_DB])

    if not cur.fetchone():
        print(f"Creating database '{PG_DB}' owned by '{PG_USER}'...")

        cur.execute(f"CREATE DATABASE {PG_DB} OWNER {PG_USER};")

    # Close connections
    cur.close()
    conn.close()


def get_connection():
    """Create and return a psycopg connection to the project database."""
    global connection

    if not connection:
        connection = psycopg.connect(dbname=PG_DB, user=PG_USER, host="localhost", port=PG_PORT)

    return connection


def start_postgres():
    """Start PostgreSQL as a subprocess."""
    # Check Postgres installation
    check_postgres_installed()

    # Initialize data directory if necessary
    init_db()

    # Start Postgres server
    print("Starting Postgres...")

    process = subprocess.Popen(["postgres", "-D", DATA_DIR, "-p", str(PG_PORT)])

    atexit.register(stop_postgres, process)  # Ensure graceful shutdown

    # Wait until Postgres is ready to accept connections
    for i in range(15):  # try for up to 15 seconds
        try:
            conn = psycopg.connect(dbname="postgres", user=PG_USER, host="localhost", port=PG_PORT)
            conn.close()
            print("Postgres is ready.")
            break
        except psycopg.OperationalError:
            print("Waiting for Postgres to start...")
            time.sleep(1)
    else:
        print("Error: Postgres did not start after 15 seconds.")
        process.terminate()
        sys.exit(1)

    # Ensure project user and database exist
    setup_user_and_db()

    return process
