"""Tests for the load_data module."""

import pytest
import json
from unittest.mock import patch, MagicMock, mock_open, call
from datetime import datetime
import sys
import os

# Add src to path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from load_data import load_admissions_results, load_data_if_available


@pytest.fixture
def sample_json_data():
    """Sample JSON data for testing."""
    return [
        {'id': 1, 'school': 'Test University', 'program_name': 'Computer Science'},
        {'id': 2, 'school': 'Another University', 'program_name': 'Data Science'}
    ]


@pytest.fixture
def mock_database_connection():
    """Mock database connection and cursor operations."""
    with patch('load_data.get_connection') as mock_get_connection:
        mock_conn = MagicMock()
        mock_get_connection.return_value = mock_conn
        yield mock_conn


@pytest.fixture
def mock_admission_result():
    """Mock AdmissionResult class and its methods."""
    with patch('load_data.AdmissionResult') as mock_ar:
        mock_ar.count.return_value = 2
        yield mock_ar


@pytest.fixture
def mock_init_tables():
    """Mock init_tables function."""
    with patch('load_data.init_tables') as mock_init:
        yield mock_init


@pytest.fixture
def mock_file_operations():
    """Mock file operations (open and json.load)."""
    mock_file_data = {}
    
    def setup_file_mock(filename, data):
        mock_file_data[filename] = data
    
    with patch('builtins.open', mock_open()) as mock_file, \
         patch('load_data.json.load') as mock_json_load:
        
        def json_load_side_effect(f):
            # Get the filename from the mock call
            for call_args in mock_file.call_args_list:
                if call_args[0]:  # if there are positional args
                    filename = call_args[0][0]
                    if filename in mock_file_data:
                        return mock_file_data[filename]
            return []
        
        mock_json_load.side_effect = json_load_side_effect
        
        yield {
            'mock_file': mock_file,
            'mock_json_load': mock_json_load,
            'setup_file_mock': setup_file_mock
        }


@pytest.fixture
def mock_argument_parser():
    """Mock argparse.ArgumentParser for main function tests."""
    with patch('load_data.argparse.ArgumentParser') as mock_parser_class:
        mock_parser = MagicMock()
        mock_parser_class.return_value = mock_parser
        yield {
            'parser_class': mock_parser_class,
            'parser': mock_parser
        }


@pytest.fixture
def mock_start_postgres():
    """Mock start_postgres function."""
    with patch('load_data.start_postgres') as mock_start:
        yield mock_start


def test_load_admissions_results_success(sample_json_data, mock_database_connection,
                                       mock_admission_result, mock_init_tables, mock_file_operations):
    """Test successful loading of admissions results."""
    # Setup file mock with sample data
    mock_file_operations['setup_file_mock']('test_file.json', sample_json_data)
    
    # Setup mock AdmissionResult instances
    mock_result_instance1 = MagicMock()
    mock_result_instance2 = MagicMock()
    mock_admission_result.from_dict.side_effect = [mock_result_instance1, mock_result_instance2]
    
    # Call the function
    load_admissions_results('test_file.json', recreate=False)
    
    # Verify calls
    mock_init_tables.assert_called_once_with(False)
    mock_file_operations['mock_file'].assert_called_once_with('test_file.json', 'r')
    mock_file_operations['mock_json_load'].assert_called_once()
    
    # Verify AdmissionResult operations
    assert mock_admission_result.from_dict.call_count == 2
    mock_admission_result.from_dict.assert_has_calls([
        call(sample_json_data[0]),
        call(sample_json_data[1])
    ])
    
    # Verify save_to_db calls
    mock_result_instance1.save_to_db.assert_called_once()
    mock_result_instance2.save_to_db.assert_called_once()
    
    # Verify database operations
    mock_database_connection.commit.assert_called_once()
    mock_admission_result.count.assert_called_once()


def test_load_admissions_results_with_recreate(mock_database_connection,
                                             mock_admission_result, mock_init_tables, mock_file_operations):
    """Test loading admissions results with recreate=True."""
    # Setup file mock with single entry
    test_data = [{'id': 1, 'school': 'Test University'}]
    mock_file_operations['setup_file_mock']('test_file.json', test_data)
    
    # Setup mock AdmissionResult
    mock_result_instance = MagicMock()
    mock_admission_result.from_dict.return_value = mock_result_instance
    mock_admission_result.count.return_value = 1
    
    # Call the function with recreate=True
    load_admissions_results('test_file.json', recreate=True)
    
    # Verify init_tables called with True
    mock_init_tables.assert_called_once_with(True)


def test_load_admissions_results_empty_file(mock_database_connection,
                                          mock_admission_result, mock_init_tables, mock_file_operations):
    """Test loading from an empty JSON file."""
    # Setup empty file
    mock_file_operations['setup_file_mock']('empty_file.json', [])
    mock_admission_result.count.return_value = 0
    
    # Call the function
    load_admissions_results('empty_file.json')
    
    # Verify no entries were processed
    mock_admission_result.from_dict.assert_not_called()
    mock_database_connection.commit.assert_called_once()
    mock_admission_result.count.assert_called_once()


def test_load_admissions_results_exception_during_processing(mock_database_connection,
                                                           mock_admission_result, mock_init_tables, mock_file_operations):
    """Test exception handling during data processing."""
    # Setup file mock
    test_data = [{'id': 1, 'school': 'Test University'}]
    mock_file_operations['setup_file_mock']('test_file.json', test_data)
    
    # Setup mock to raise exception during save_to_db
    mock_result_instance = MagicMock()
    mock_result_instance.save_to_db.side_effect = Exception("Database error")
    mock_admission_result.from_dict.return_value = mock_result_instance
    
    # Call the function and expect exception to be re-raised
    with pytest.raises(Exception, match="Database error"):
        load_admissions_results('test_file.json')
    
    # Verify init_tables was called
    mock_init_tables.assert_called_once_with(False)
    # Verify commit was not called due to exception
    mock_database_connection.commit.assert_not_called()


def test_load_admissions_results_exception_during_from_dict(mock_database_connection,
                                                          mock_admission_result, mock_init_tables, mock_file_operations):
    """Test exception handling during AdmissionResult.from_dict."""
    # Setup file mock
    test_data = [{'id': 1, 'school': 'Test University'}]
    mock_file_operations['setup_file_mock']('test_file.json', test_data)
    
    # Setup mock to raise exception during from_dict
    mock_admission_result.from_dict.side_effect = Exception("Invalid data format")
    
    # Call the function and expect exception to be re-raised
    with pytest.raises(Exception, match="Invalid data format"):
        load_admissions_results('test_file.json')
    
    # Verify init_tables was called
    mock_init_tables.assert_called_once_with(False)
    # Verify commit was not called due to exception
    mock_database_connection.commit.assert_not_called()


def test_load_admissions_results_file_not_found(mock_init_tables):
    """Test handling of file not found error."""
    with patch('builtins.open', side_effect=FileNotFoundError("File not found")):
        # Call the function and expect FileNotFoundError to be raised
        with pytest.raises(FileNotFoundError, match="File not found"):
            load_admissions_results('nonexistent_file.json')
        
        # Verify init_tables was called before the file error
        mock_init_tables.assert_called_once_with(False)


def test_load_admissions_results_invalid_json(mock_init_tables):
    """Test handling of invalid JSON file."""
    with patch('builtins.open', mock_open()), \
         patch('load_data.json.load', side_effect=json.JSONDecodeError("Invalid JSON", "doc", 1)):
        # Call the function and expect JSONDecodeError to be raised
        with pytest.raises(json.JSONDecodeError):
            load_admissions_results('invalid.json')
        
        # Verify init_tables was called before the JSON error
        mock_init_tables.assert_called_once_with(False)


class TestLoadDataIfAvailable:
    """Tests for the load_data_if_available function."""
    
    @patch('os.path.exists')
    def test_load_data_if_available_file_not_found(self, mock_exists):
        """Test load_data_if_available when file doesn't exist."""
        mock_exists.return_value = False
        
        # Capture print output
        with patch('builtins.print') as mock_print:
            result = load_data_if_available('nonexistent.json')
        
        # Verify return value and print message
        assert result is False
        mock_exists.assert_called_once_with('nonexistent.json')
        mock_print.assert_called_once_with("Data file 'nonexistent.json' not found, skipping data load")
    
    @patch('os.path.exists')
    @patch('load_data.load_admissions_results')
    def test_load_data_if_available_success(self, mock_load_results, mock_exists):
        """Test load_data_if_available when file exists and loading succeeds."""
        mock_exists.return_value = True
        mock_load_results.return_value = None  # Successful execution
        
        result = load_data_if_available('test.json', recreate=True)
        
        # Verify return value and function calls
        assert result is True
        mock_exists.assert_called_once_with('test.json')
        mock_load_results.assert_called_once_with('test.json', True)
    
    @patch('os.path.exists')
    @patch('load_data.load_admissions_results')
    def test_load_data_if_available_load_exception(self, mock_load_results, mock_exists):
        """Test load_data_if_available when loading raises an exception."""
        mock_exists.return_value = True
        mock_load_results.side_effect = Exception("Database connection failed")
        
        # Capture print output
        with patch('builtins.print') as mock_print:
            result = load_data_if_available('test.json')
        
        # Verify return value and error handling
        assert result is False
        mock_exists.assert_called_once_with('test.json')
        mock_load_results.assert_called_once_with('test.json', False)
        mock_print.assert_called_once_with("Failed to load data from 'test.json': Database connection failed")
    
    @patch('os.path.exists')
    @patch('load_data.load_admissions_results')
    def test_load_data_if_available_default_parameters(self, mock_load_results, mock_exists):
        """Test load_data_if_available with default parameters."""
        mock_exists.return_value = True
        mock_load_results.return_value = None
        
        result = load_data_if_available()
        
        # Verify default filename and recreate=False
        assert result is True
        mock_exists.assert_called_once_with('admissions_info.json')
        mock_load_results.assert_called_once_with('admissions_info.json', False)
