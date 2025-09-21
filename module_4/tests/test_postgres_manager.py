"""Tests for PostgreSQL database management functionality."""

import pytest
from unittest.mock import MagicMock
import psycopg


# ------------------------
# check_postgres_installed
# ------------------------
@pytest.mark.db
def test_check_postgres_installed(mocker):
    """Test successful PostgreSQL binary detection."""
    mocker.patch("shutil.which", return_value="/usr/bin/postgres")
    from postgres_manager import check_postgres_installed

    check_postgres_installed()


@pytest.mark.db
def test_check_postgres_installed_missing(mocker):
    """Test handling of missing PostgreSQL binaries."""
    mocker.patch("shutil.which", return_value=None)
    mocker.patch("sys.exit")
    mocker.patch("builtins.print")
    from postgres_manager import check_postgres_installed

    check_postgres_installed()


# ------------------------
# init_db
# ------------------------
@pytest.mark.db
def test_init_db(mocker):
    """Test database initialization when data directory exists."""
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("subprocess.run")
    from postgres_manager import init_db

    init_db()


@pytest.mark.db
def test_init_db_create(mocker):
    """Test database initialization with directory creation."""
    mocker.patch("os.path.exists", return_value=False)
    mocker.patch("subprocess.run", return_value=MagicMock(returncode=0))
    mocker.patch("builtins.print")
    from postgres_manager import init_db

    init_db()


# ------------------------
# stop_postgres
# ------------------------
@pytest.mark.db
def test_stop_postgres(mocker):
    """Test PostgreSQL server process termination."""
    mock_process = MagicMock()
    mocker.patch("builtins.print")
    from postgres_manager import stop_postgres

    stop_postgres(mock_process)


# ------------------------
# setup_user_and_db
# ------------------------
@pytest.mark.db
def test_setup_user_and_db(mocker):
    """Test database and user creation when database doesn't exist."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None
    mocker.patch("psycopg.connect", return_value=mock_conn)
    mocker.patch("builtins.print")
    from postgres_manager import setup_user_and_db

    setup_user_and_db()


# ------------------------
# get_connection
# ------------------------
@pytest.mark.db
def test_get_connection(mocker):
    """Test database connection creation."""
    mocker.patch("psycopg.connect", return_value=MagicMock())
    from postgres_manager import get_connection

    get_connection()


# ------------------------
# start_postgres
# ------------------------
@pytest.mark.db
def test_start_postgres_timeout(mocker):
    """Test PostgreSQL startup timeout handling."""
    mocker.patch("postgres_manager.check_postgres_installed")
    mocker.patch("postgres_manager.init_db")
    mock_process = MagicMock()
    mocker.patch("subprocess.Popen", return_value=mock_process)
    mocker.patch("atexit.register")
    mocker.patch("postgres_manager.setup_user_and_db")  # fully mock to prevent real DB calls
    mocker.patch("psycopg.connect", side_effect=psycopg.OperationalError())
    mocker.patch("time.sleep", lambda x: None)
    mocker.patch("sys.exit")
    mocker.patch("builtins.print")
    from postgres_manager import start_postgres

    start_postgres()


@pytest.mark.db
def test_start_postgres_eventual_success(mocker):
    """Test successful PostgreSQL startup after initial connection failures."""
    mocker.patch("postgres_manager.check_postgres_installed")
    mocker.patch("postgres_manager.init_db")
    mock_process = MagicMock()
    mocker.patch("subprocess.Popen", return_value=mock_process)
    mocker.patch("atexit.register")
    mocker.patch("postgres_manager.setup_user_and_db")
    mocker.patch("builtins.print")
    mocker.patch("time.sleep", lambda x: None)
    side_effects = [psycopg.OperationalError(), psycopg.OperationalError(), MagicMock()]
    mocker.patch("psycopg.connect", side_effect=side_effects)
    from postgres_manager import start_postgres

    start_postgres()
