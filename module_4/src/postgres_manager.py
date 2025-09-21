"""PostgreSQL database management functions.

Manages PostgreSQL server lifecycle, database initialization, and connections.
"""

import subprocess
import os
import atexit
import time
import shutil
import sys
import psycopg
from psycopg import sql


DATA_DIR = os.getenv("PG_DATA_DIR", "pgdata")     # Directory where Postgres stores data
PG_HOST = os.getenv("PG_HOST", "localhost")       # Host for Postgres server
PG_PORT = int(os.getenv("PG_PORT", 5432))         # Port for Postgres server
PG_USER = os.getenv("PG_USER", "student")         # Postgres user for the project
PG_DB = os.getenv("PG_DB", "admissions")          # Database name

# Per assignment instructions
PG_HOST = PG_HOST or os.getenv("DATABASE_URL")


def check_postgres_installed() -> None:
    """Check if PostgreSQL binaries are installed.
    
    :raises SystemExit: If postgres or initdb binaries not found.
    """
    if shutil.which("postgres") is None or shutil.which("initdb") is None:
        print("Error: Postgres binaries not found. Please install Postgres.")
        sys.exit(1)


def init_db() -> None:
    """Initialize PostgreSQL data directory if it doesn't exist."""
    if not os.path.exists(DATA_DIR):
        print(f"Data directory '{DATA_DIR}' not found. Initializing...")

        subprocess.run(["initdb", "-D", DATA_DIR, "-U", PG_USER])


def stop_postgres(process: subprocess.Popen) -> None:
    """Terminate PostgreSQL subprocess.
    
    :param process: PostgreSQL process to terminate.
    :type process: subprocess.Popen
    """
    print("Stopping Postgres...")

    process.terminate()
    process.wait()


def setup_user_and_db() -> None:
    """Create project database if it doesn't exist.
    
    :raises psycopg.Error: If database connection or creation fails.
    """
    # Connect as default 'postgres' user
    conn = psycopg.connect(dbname="postgres", user=PG_USER, host=PG_HOST, port=PG_PORT)
    conn.autocommit = True
    cur = conn.cursor()

    # Check if database exists, create if missing
    cur.execute("SELECT 1 FROM pg_database WHERE datname=%s;", [PG_DB])

    if not cur.fetchone():
        print(f"Creating database '{PG_DB}' owned by '{PG_USER}'...")

        cur.execute(sql.SQL("CREATE DATABASE {} OWNER {};").format(
            sql.Identifier(PG_DB), sql.Identifier(PG_USER)
        ))

    # Close connections
    cur.close()
    conn.close()


def get_connection():
    """Create database connection.
    
    :returns: Connection to project database.
    :rtype: psycopg.Connection
    :raises psycopg.Error: If connection fails.
    """
    return psycopg.connect(dbname=PG_DB, user=PG_USER, host=PG_HOST, port=PG_PORT)


def start_postgres() -> subprocess.Popen:
    """Start PostgreSQL server process.
    
    Initializes database, starts server, and creates project database.
    
    :returns: PostgreSQL server process.
    :rtype: subprocess.Popen
    :raises SystemExit: If PostgreSQL fails to start within 15 seconds.
    """
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
            conn = psycopg.connect(dbname="postgres", user=PG_USER, host=PG_HOST, port=PG_PORT)
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
