"""Additional tests for postgres_manager.py to achieve 100% coverage."""

import pytest
from unittest.mock import patch, MagicMock
import subprocess
import os


@pytest.mark.db
def test_check_postgres_installed_success():
    """Test check_postgres_installed when binaries are available."""
    from postgres_manager import check_postgres_installed
    
    with patch('shutil.which') as mock_which:
        mock_which.side_effect = lambda binary: f"/usr/bin/{binary}" if binary in ["postgres", "initdb"] else None
        
        # Should not raise any exception
        check_postgres_installed()
        
        assert mock_which.call_count == 2
        mock_which.assert_any_call("postgres")
        mock_which.assert_any_call("initdb")


@pytest.mark.db
def test_check_postgres_installed_missing():
    """Test check_postgres_installed when binaries are missing."""
    from postgres_manager import check_postgres_installed
    
    with patch('shutil.which', return_value=None):
        with patch('sys.exit') as mock_exit:
            check_postgres_installed()
            mock_exit.assert_called_once_with(1)


@pytest.mark.db
def test_init_db_already_exists():
    """Test init_db when data directory already exists."""
    from postgres_manager import init_db
    
    with patch('os.path.exists', return_value=True):
        with patch('subprocess.run') as mock_run:
            init_db()
            # Should not call initdb if directory exists
            mock_run.assert_not_called()


@pytest.mark.db
def test_init_db_create_new():
    """Test init_db when creating new data directory."""
    from postgres_manager import init_db, DATA_DIR, PG_USER
    
    with patch('os.path.exists', return_value=False):
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            
            init_db()
            
            mock_run.assert_called_once_with(["initdb", "-D", DATA_DIR, "-U", PG_USER])


@pytest.mark.db
def test_init_db_failure():
    """Test init_db when initdb command fails."""
    from postgres_manager import init_db
    
    with patch('os.path.exists', return_value=False):
        with patch('subprocess.run') as mock_run:
            with patch('sys.exit') as mock_exit:
                mock_run.return_value.returncode = 1
                
                init_db()
                
                mock_exit.assert_called_once_with(1)


@pytest.mark.db
def test_stop_postgres():
    """Test stop_postgres function."""
    from postgres_manager import stop_postgres
    
    mock_process = MagicMock()
    mock_connection = MagicMock()
    
    with patch('postgres_manager.connection', mock_connection):
        stop_postgres(mock_process)
        
        mock_connection.close.assert_called_once()
        mock_process.terminate.assert_called_once()
        mock_process.wait.assert_called_once()


@pytest.mark.db
def test_stop_postgres_no_connection():
    """Test stop_postgres when no connection exists."""
    from postgres_manager import stop_postgres
    
    mock_process = MagicMock()
    
    with patch('postgres_manager.connection', None):
        stop_postgres(mock_process)
        
        # Should not crash when connection is None
        mock_process.terminate.assert_called_once()
        mock_process.wait.assert_called_once()


@pytest.mark.db
def test_setup_user_and_db_create_new():
    """Test setup_user_and_db when database doesn't exist."""
    from postgres_manager import setup_user_and_db, PG_USER, PG_DB
    
    with patch('psycopg.connect') as mock_connect:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None  # Database doesn't exist
        
        setup_user_and_db()
        
        # Should check if database exists
        mock_cursor.execute.assert_any_call("SELECT 1 FROM pg_database WHERE datname=%s;", [PG_DB])
        # Should create database
        mock_cursor.execute.assert_any_call(f"CREATE DATABASE {PG_DB} OWNER {PG_USER};")


@pytest.mark.db
def test_setup_user_and_db_already_exists():
    """Test setup_user_and_db when database already exists."""
    from postgres_manager import setup_user_and_db, PG_DB
    
    with patch('psycopg.connect') as mock_connect:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = [1]  # Database exists
        
        setup_user_and_db()
        
        # Should check if database exists
        mock_cursor.execute.assert_any_call("SELECT 1 FROM pg_database WHERE datname=%s;", [PG_DB])
        # Should NOT create database since it exists
        create_calls = [call for call in mock_cursor.execute.call_args_list 
                       if "CREATE DATABASE" in str(call)]
        assert len(create_calls) == 0


@pytest.mark.db
def test_get_connection_new():
    """Test get_connection creating new connection."""
    from postgres_manager import get_connection, PG_DB, PG_USER, PG_PORT
    
    # Reset global connection
    import postgres_manager
    postgres_manager.connection = None
    
    with patch('psycopg.connect') as mock_connect:
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        
        result = get_connection()
        
        assert result == mock_conn
        mock_connect.assert_called_once_with(dbname=PG_DB, user=PG_USER, host="localhost", port=PG_PORT)


@pytest.mark.db
def test_get_connection_reuse_existing():
    """Test get_connection reusing existing connection."""
    from postgres_manager import get_connection
    
    mock_existing_conn = MagicMock()
    
    # Set existing connection
    import postgres_manager
    postgres_manager.connection = mock_existing_conn
    
    with patch('psycopg.connect') as mock_connect:
        result = get_connection()
        
        assert result == mock_existing_conn
        # Should not create new connection
        mock_connect.assert_not_called()


@pytest.mark.db
def test_start_postgres_success():
    """Test start_postgres successful startup."""
    from postgres_manager import start_postgres, DATA_DIR, PG_PORT
    
    with patch('postgres_manager.check_postgres_installed'):
        with patch('postgres_manager.init_db'):
            with patch('subprocess.Popen') as mock_popen:
                with patch('postgres_manager.setup_user_and_db'):
                    with patch('atexit.register'):
                        with patch('psycopg.connect') as mock_connect:
                            mock_process = MagicMock()
                            mock_popen.return_value = mock_process
                            
                            # Mock successful connection attempt
                            mock_conn = MagicMock()
                            mock_connect.return_value = mock_conn
                            
                            result = start_postgres()
                            
                            assert result == mock_process
                            mock_popen.assert_called_once_with(["postgres", "-D", DATA_DIR, "-p", str(PG_PORT)])


@pytest.mark.db
def test_start_postgres_connection_timeout():
    """Test start_postgres when connection times out."""
    from postgres_manager import start_postgres
    import psycopg
    
    with patch('postgres_manager.check_postgres_installed'):
        with patch('postgres_manager.init_db'):
            with patch('subprocess.Popen') as mock_popen:
                with patch('postgres_manager.setup_user_and_db'):
                    with patch('atexit.register'):
                        with patch('psycopg.connect') as mock_connect:
                            with patch('sys.exit') as mock_exit:
                                with patch('time.sleep'):
                                    mock_process = MagicMock()
                                    mock_popen.return_value = mock_process
                                    
                                    # Mock connection always failing
                                    mock_connect.side_effect = psycopg.OperationalError("Connection failed")
                                    
                                    start_postgres()
                                    
                                    mock_exit.assert_called_once_with(1)
                                    mock_process.terminate.assert_called_once()


@pytest.mark.db
def test_start_postgres_eventual_success():
    """Test start_postgres succeeding after initial failures."""
    from postgres_manager import start_postgres
    import psycopg
    
    with patch('postgres_manager.check_postgres_installed'):
        with patch('postgres_manager.init_db'):
            with patch('subprocess.Popen') as mock_popen:
                with patch('postgres_manager.setup_user_and_db'):
                    with patch('atexit.register'):
                        with patch('psycopg.connect') as mock_connect:
                            with patch('time.sleep'):
                                mock_process = MagicMock()
                                mock_popen.return_value = mock_process
                                
                                # First 2 attempts fail, 3rd succeeds
                                mock_conn = MagicMock()
                                mock_connect.side_effect = [
                                    psycopg.OperationalError("Not ready"),
                                    psycopg.OperationalError("Still not ready"),
                                    mock_conn  # Success on 3rd attempt
                                ]
                                
                                result = start_postgres()
                                
                                assert result == mock_process
                                assert mock_connect.call_count == 3