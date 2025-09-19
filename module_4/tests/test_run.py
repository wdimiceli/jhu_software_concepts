"""Tests for src/run.py to achieve 100% coverage of the start() function."""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock
from io import StringIO

# Add src to path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


@patch('run.start_postgres')
@patch('run.create_app')
@patch.dict(os.environ, {'LOAD_DATA_ON_STARTUP': 'false'})
def test_start_load_data_disabled(mock_create_app, mock_start_postgres):
    """Test start function when LOAD_DATA_ON_STARTUP is false."""
    from run import start
    
    mock_app = MagicMock()
    mock_create_app.return_value = mock_app
    
    start()
    
    # Verify postgres was started
    mock_start_postgres.assert_called_once()
    
    # Verify app was created and run
    mock_create_app.assert_called_once()
    mock_app.run.assert_called_once_with(host='0.0.0.0', port=8080)


@patch('run.start_postgres')
@patch('run.create_app')
@patch('load_data.load_data_if_available')
@patch.dict(os.environ, {'LOAD_DATA_ON_STARTUP': 'true'})
def test_start_load_data_enabled_success(mock_load_data, mock_create_app, mock_start_postgres):
    """Test start function when LOAD_DATA_ON_STARTUP is true and load_data succeeds."""
    from run import start
    
    mock_app = MagicMock()
    mock_create_app.return_value = mock_app
    
    start()
    
    # Verify postgres was started
    mock_start_postgres.assert_called_once()
    
    # Verify load_data was called
    mock_load_data.assert_called_once()
    
    # Verify app was created and run
    mock_create_app.assert_called_once()
    mock_app.run.assert_called_once_with(host='0.0.0.0', port=8080)


@patch('run.start_postgres')
@patch('run.create_app')
@patch.dict(os.environ, {'LOAD_DATA_ON_STARTUP': 'TRUE'})  # Test case insensitive
def test_start_load_data_import_error(mock_create_app, mock_start_postgres):
    """Test start function when load_data import fails."""
    from run import start
    
    mock_app = MagicMock()
    mock_create_app.return_value = mock_app
    
    # Mock the import to raise ImportError
    with patch('builtins.__import__', side_effect=lambda name, *args, **kwargs: 
              ImportError("No module named 'load_data'") if name == 'load_data' else __import__(name, *args, **kwargs)):
        
        captured_output = StringIO()
        with patch('sys.stdout', captured_output):
            start()
        
        # Check that error message was printed
        output = captured_output.getvalue()
        assert "Could not import data loading module" in output
    
    # Verify postgres was started
    mock_start_postgres.assert_called_once()
    
    # Verify app was created and run despite import error
    mock_create_app.assert_called_once()
    mock_app.run.assert_called_once_with(host='0.0.0.0', port=8080)


@patch('run.start_postgres')
@patch('run.create_app')
@patch('load_data.load_data_if_available', side_effect=ValueError("Data loading failed"))
@patch.dict(os.environ, {'LOAD_DATA_ON_STARTUP': 'true'})
def test_start_load_data_general_exception(mock_load_data, mock_create_app, mock_start_postgres):
    """Test start function when load_data raises a general exception."""
    from run import start
    
    mock_app = MagicMock()
    mock_create_app.return_value = mock_app
    
    captured_output = StringIO()
    with patch('sys.stdout', captured_output):
        start()
    
    # Check that error message was printed
    output = captured_output.getvalue()
    assert "Data loading failed during startup" in output
    
    # Verify postgres was started
    mock_start_postgres.assert_called_once()
    
    # Verify load_data was attempted
    mock_load_data.assert_called_once()
    
    # Verify app was created and run despite exception
    mock_create_app.assert_called_once()
    mock_app.run.assert_called_once_with(host='0.0.0.0', port=8080)


@patch('run.start_postgres')
@patch('run.create_app')
@patch.dict(os.environ, {}, clear=True)  # Clear environment to test default
def test_start_default_load_data_setting(mock_create_app, mock_start_postgres):
    """Test start function with default LOAD_DATA_ON_STARTUP setting (should be true)."""
    from run import start
    
    mock_app = MagicMock()
    mock_create_app.return_value = mock_app
    
    # Mock the import to raise ImportError to test the default 'true' behavior
    with patch('builtins.__import__', side_effect=lambda name, *args, **kwargs: 
              ImportError("No module named 'load_data'") if name == 'load_data' else __import__(name, *args, **kwargs)):
        
        captured_output = StringIO()
        with patch('sys.stdout', captured_output):
            start()
        
        # Should attempt to import since default is 'true'
        output = captured_output.getvalue()
        assert "Could not import data loading module" in output
    
    # Verify postgres was started
    mock_start_postgres.assert_called_once()
    
    # Verify app was created and run
    mock_create_app.assert_called_once()
    mock_app.run.assert_called_once_with(host='0.0.0.0', port=8080)


@patch('run.start_postgres')
@patch('run.create_app')
@patch.dict(os.environ, {'LOAD_DATA_ON_STARTUP': 'False'})  # Test mixed case
def test_start_load_data_case_insensitive_false(mock_create_app, mock_start_postgres):
    """Test that LOAD_DATA_ON_STARTUP is case insensitive for 'false'."""
    from run import start
    
    mock_app = MagicMock()
    mock_create_app.return_value = mock_app
    
    start()
    
    # Should not attempt to import load_data since it's false
    mock_start_postgres.assert_called_once()
    mock_create_app.assert_called_once()
    mock_app.run.assert_called_once_with(host='0.0.0.0', port=8080)


if __name__ == '__main__':
    pytest.main([__file__])