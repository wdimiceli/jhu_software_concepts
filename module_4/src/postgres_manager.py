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
from urllib.parse import urlparse


def parse_database_url(database_url: str) -> dict:
    """Parse DATABASE_URL into connection components.
    
    :param database_url: PostgreSQL connection URL in format postgresql://user:password@host:port/database
    :type database_url: str
    :returns: Dictionary with connection parameters
    :rtype: dict
    """
    parsed = urlparse(database_url)
    return {
        'host': parsed.hostname or 'localhost',
        'port': parsed.port or 5432,
        'user': parsed.username or 'student',
        'password': parsed.password,
        'database': parsed.path.lstrip('/') if parsed.path else 'admissions'
    }


# Configuration using DATABASE_URL or defaults
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://student@localhost:5432/admissions")
db_config = parse_database_url(DATABASE_URL)

PG_HOST = db_config['host']
PG_PORT = int(db_config['port'])
PG_USER = db_config['user']
PG_PASSWORD = db_config['password']
PG_DB = db_config['database']

# Data directory for local PostgreSQL server
DATA_DIR = os.getenv("PG_DATA_DIR", "pgdata")


def get_connection_params(dbname: str | None = None) -> dict:
    """Build PostgreSQL connection parameters.
    
    :param dbname: Database name (defaults to PG_DB)
    :type dbname: str | None
    :returns: Connection parameters dictionary
    :rtype: dict
    """
    return {
        'dbname': dbname or PG_DB,
        'user': PG_USER,
        'host': PG_HOST,
        'port': PG_PORT,
        'password': PG_PASSWORD
    }


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


def setup_db() -> None:
    """Create project database if it doesn't exist.
    
    :raises psycopg.Error: If database connection or creation fails.
    """
    # Connect as default 'postgres' user
    conn = psycopg.connect(**get_connection_params('postgres'))
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
    return psycopg.connect(**get_connection_params())


def test_postgres_connection():
    """Test PostgreSQL server connectivity with retry logic.
    
    Attempts to establish a connection to the PostgreSQL server for up to 15 seconds
    with 1-second intervals between attempts. This function is typically used during
    startup to ensure the database server is ready before proceeding with application
    initialization.
    
    :raises SystemExit: If PostgreSQL server is not accessible after 15 seconds
    """
    # Wait until Postgres is ready to accept connections
    for i in range(15):  # try for up to 15 seconds
        try:
            conn = psycopg.connect(**get_connection_params('postgres'))
            conn.close()
            print("Postgres is ready.")
            break
        except psycopg.OperationalError:
            print("Waiting for Postgres to start...")
            time.sleep(1)
    else:
        print("Error: Postgres did not start after 15 seconds.")
        sys.exit(1)


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

    test_postgres_connection()

    # Ensure project user and database exist
    setup_db()

    return process


def check_and_configure_postgres():
    """Check postgres connection and start local server if needed."""
    return start_postgres() if PG_HOST == 'localhost' else test_postgres_connection()
