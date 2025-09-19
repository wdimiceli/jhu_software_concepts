"""Comprehensive tests for src/llm_hosting/app.py to achieve 100% coverage."""

import json
import os
import sys
import pytest
from unittest.mock import patch, MagicMock, mock_open

# Add src to path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from llm_hosting.app import (
    app, _read_lines, _load_llm, _split_fallback, _best_match,
    _post_normalize_program, _post_normalize_university,
    _call_llm, _normalize_input
)


# Tests for _read_lines function
def test_read_lines_success():
    """Test _read_lines with valid file."""
    test_content = "Line 1\n  Line 2  \n\nLine 3\n  \n"
    with patch('builtins.open', mock_open(read_data=test_content)):
        result = _read_lines('test.txt')
    
    assert result == ['Line 1', 'Line 2', 'Line 3']


def test_read_lines_file_not_found():
    """Test _read_lines when file doesn't exist."""
    with patch('builtins.open', side_effect=FileNotFoundError):
        result = _read_lines('nonexistent.txt')
    
    assert result == []


def test_read_lines_empty_file():
    """Test _read_lines with empty file."""
    with patch('builtins.open', mock_open(read_data="")):
        result = _read_lines('empty.txt')
    
    assert result == []


# Tests for _load_llm function
@patch('llm_hosting.app._LLM', None)
@patch('llm_hosting.app.hf_hub_download')
@patch('llm_hosting.app.Llama')
def test_load_llm_first_time(mock_llama, mock_hf_download):
    """Test _load_llm when loading for the first time."""
    mock_hf_download.return_value = '/path/to/model.gguf'
    mock_llama_instance = MagicMock()
    mock_llama.return_value = mock_llama_instance
    
    result = _load_llm()
    
    # Verify HuggingFace download was called correctly
    mock_hf_download.assert_called_once_with(
        repo_id="TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF",
        filename="tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
        local_dir="models",
        local_dir_use_symlinks=False,
        force_filename="tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
    )
    
    # Verify Llama was initialized correctly
    mock_llama.assert_called_once_with(
        model_path='/path/to/model.gguf',
        n_ctx=2048,
        n_threads=os.cpu_count() or 2,
        n_gpu_layers=0,
        verbose=False,
    )
    
    assert result == mock_llama_instance


@patch('llm_hosting.app._LLM')
def test_load_llm_already_loaded(mock_existing_llm):
    """Test _load_llm when model is already loaded."""
    mock_existing_llm.__bool__ = lambda x: True  # Make it truthy
    
    result = _load_llm()
    
    assert result == mock_existing_llm


# Tests for _split_fallback function
def test_split_fallback_basic():
    """Test basic program, university splitting."""
    result = _split_fallback("Computer Science, Stanford University")
    assert result == ("Computer Science", "Stanford University")


def test_split_fallback_with_at():
    """Test splitting with 'at' separator."""
    result = _split_fallback("Mathematics at MIT")
    assert result == ("Mathematics", "Mit")


def test_split_fallback_mcgill_expansion():
    """Test McGill abbreviation expansion."""
    result = _split_fallback("Computer Science, McG")
    assert result == ("Computer Science", "Mcgill University")
    
    result = _split_fallback("Data Science, mcgill")
    assert result == ("Data Science", "Mcgill University")


def test_split_fallback_ubc_expansion():
    """Test UBC abbreviation expansion."""
    result = _split_fallback("Engineering, UBC")
    assert result == ("Engineering", "University of British Columbia")
    
    result = _split_fallback("Physics, u.b.c.")
    assert result == ("Physics", "University of British Columbia")


def test_split_fallback_single_part():
    """Test with only program, no university."""
    result = _split_fallback("Computer Science")
    assert result == ("Computer Science", "Unknown")


def test_split_fallback_empty_input():
    """Test with empty or None input."""
    result = _split_fallback("")
    assert result == ("", "Unknown")
    
    result = _split_fallback(None)
    assert result == ("", "Unknown")


def test_split_fallback_normalize_of():
    """Test normalization of 'Of' to 'of'."""
    result = _split_fallback("Math, University Of Toronto")
    assert result == ("Math", "University of Toronto")


# Tests for _best_match function
def test_best_match_exact():
    """Test exact match."""
    candidates = ["Computer Science", "Mathematics", "Physics"]
    result = _best_match("Computer Science", candidates)
    assert result == "Computer Science"


def test_best_match_close():
    """Test close match above cutoff."""
    candidates = ["Computer Science", "Mathematics", "Physics"]
    result = _best_match("Computer Sciences", candidates, cutoff=0.8)
    assert result == "Computer Science"


def test_best_match_no_match():
    """Test no match below cutoff."""
    candidates = ["Computer Science", "Mathematics", "Physics"]
    result = _best_match("Biology", candidates, cutoff=0.86)
    assert result is None


def test_best_match_empty_input():
    """Test with empty inputs."""
    assert _best_match("", ["test"]) is None
    assert _best_match("test", []) is None
    assert _best_match(None, ["test"]) is None


# Tests for _post_normalize_program function
@patch('llm_hosting.app.CANON_PROGS', ['Computer Science', 'Mathematics'])
@patch('llm_hosting.app.COMMON_PROG_FIXES', {'Mathematic': 'Mathematics'})
def test_post_normalize_program_common_fix():
    """Test common program fixes."""
    result = _post_normalize_program('Mathematic')
    assert result == 'Mathematics'


@patch('llm_hosting.app.CANON_PROGS', ['Computer Science', 'Mathematics'])
def test_post_normalize_program_canonical():
    """Test program in canonical list."""
    result = _post_normalize_program('computer science')
    assert result == 'Computer Science'


@patch('llm_hosting.app.CANON_PROGS', ['Computer Science', 'Mathematics'])
def test_post_normalize_program_fuzzy_match():
    """Test fuzzy matching for programs."""
    with patch('llm_hosting.app._best_match', return_value='Computer Science'):
        result = _post_normalize_program('comp sci')
        assert result == 'Computer Science'


@patch('llm_hosting.app.CANON_PROGS', ['Computer Science', 'Mathematics'])
def test_post_normalize_program_no_match():
    """Test program with no match."""
    with patch('llm_hosting.app._best_match', return_value=None):
        result = _post_normalize_program('Biology')
        assert result == 'Biology'


# Tests for _post_normalize_university function
@patch('llm_hosting.app.CANON_UNIS', ['McGill University', 'Stanford University'])
@patch('llm_hosting.app.ABBREV_UNI', {r'(?i)^mcg(\.|ill)?$': 'McGill University'})
@patch('llm_hosting.app.COMMON_UNI_FIXES', {'Mcgill University': 'McGill University'})
def test_post_normalize_university_abbreviation():
    """Test university abbreviation expansion."""
    result = _post_normalize_university('mcg')
    assert result == 'McGill University'


@patch('llm_hosting.app.CANON_UNIS', ['McGill University', 'Stanford University'])  
@patch('llm_hosting.app.COMMON_UNI_FIXES', {'Mcgill University': 'McGill University'})
def test_post_normalize_university_common_fix():
    """Test common university fixes."""
    result = _post_normalize_university('Mcgill University')
    assert result == 'McGill University'


@patch('llm_hosting.app.CANON_UNIS', ['McGill University', 'Stanford University'])
def test_post_normalize_university_canonical():
    """Test university in canonical list."""
    result = _post_normalize_university('McGill University')
    assert result == 'McGill University'


@patch('llm_hosting.app.CANON_UNIS', ['McGill University', 'Stanford University'])
def test_post_normalize_university_canonical_exact_match():
    """Test university exact match in canonical list - covers line 202."""
    # This specifically tests the "if u in CANON_UNIS: return u" path
    result = _post_normalize_university('Stanford University')
    assert result == 'Stanford University'


@patch('llm_hosting.app.CANON_UNIS', ['McGill University', 'Stanford University'])
def test_post_normalize_university_fuzzy_match():
    """Test fuzzy matching for universities."""
    with patch('llm_hosting.app._best_match', return_value='Stanford University'):
        result = _post_normalize_university('stanford')
        assert result == 'Stanford University'


@patch('llm_hosting.app.CANON_UNIS', ['McGill University', 'Stanford University'])
def test_post_normalize_university_no_match():
    """Test university with no match."""
    with patch('llm_hosting.app._best_match', return_value=None):
        result = _post_normalize_university('Unknown Uni')
        assert result == 'Unknown Uni'


def test_post_normalize_university_empty():
    """Test empty university input."""
    result = _post_normalize_university('')
    assert result == 'Unknown'


def test_post_normalize_university_normalize_of():
    """Test normalization of 'Of' to 'of'."""
    with patch('llm_hosting.app.CANON_UNIS', []):
        with patch('llm_hosting.app._best_match', return_value=None):
            result = _post_normalize_university('University Of Toronto')
            assert result == 'University of Toronto'


# Tests for _call_llm function
@patch('llm_hosting.app._load_llm')
@patch('llm_hosting.app._post_normalize_program')
@patch('llm_hosting.app._post_normalize_university')
def test_call_llm_success(mock_post_uni, mock_post_prog, mock_load_llm):
    """Test successful LLM call with valid JSON response."""
    mock_llm = MagicMock()
    mock_load_llm.return_value = mock_llm
    mock_llm.create_chat_completion.return_value = {
        'choices': [{
            'message': {
                'content': '{"standardized_program": "Computer Science", "standardized_university": "MIT"}'
            }
        }]
    }
    mock_post_prog.return_value = "Computer Science"
    mock_post_uni.return_value = "Massachusetts Institute of Technology"
    
    result = _call_llm("CS, MIT")
    
    assert result == {
        "standardized_program": "Computer Science",
        "standardized_university": "Massachusetts Institute of Technology"
    }
    mock_post_prog.assert_called_once_with("Computer Science")
    mock_post_uni.assert_called_once_with("MIT")


@patch('llm_hosting.app._load_llm')
@patch('llm_hosting.app._split_fallback')
@patch('llm_hosting.app._post_normalize_program')
@patch('llm_hosting.app._post_normalize_university')
def test_call_llm_invalid_json_fallback(mock_post_uni, mock_post_prog, mock_fallback, mock_load_llm):
    """Test LLM call with invalid JSON response using fallback."""
    mock_llm = MagicMock()
    mock_load_llm.return_value = mock_llm
    mock_llm.create_chat_completion.return_value = {
        'choices': [{
            'message': {
                'content': 'This is not valid JSON'
            }
        }]
    }
    mock_fallback.return_value = ("Computer Science", "MIT")
    mock_post_prog.return_value = "Computer Science"
    mock_post_uni.return_value = "Massachusetts Institute of Technology"
    
    result = _call_llm("CS, MIT")
    
    mock_fallback.assert_called_once_with("CS, MIT")
    assert result == {
        "standardized_program": "Computer Science",
        "standardized_university": "Massachusetts Institute of Technology"
    }


@patch('llm_hosting.app._load_llm')
@patch('llm_hosting.app._post_normalize_program')
@patch('llm_hosting.app._post_normalize_university')
def test_call_llm_partial_json_extraction(mock_post_uni, mock_post_prog, mock_load_llm):
    """Test LLM call with JSON embedded in text."""
    mock_llm = MagicMock()
    mock_load_llm.return_value = mock_llm
    mock_llm.create_chat_completion.return_value = {
        'choices': [{
            'message': {
                'content': 'Here is the result: {"standardized_program": "Math", "standardized_university": "Stanford"} hope this helps!'
            }
        }]
    }
    mock_post_prog.return_value = "Mathematics"
    mock_post_uni.return_value = "Stanford University"
    
    result = _call_llm("Math, Stanford")
    
    assert result == {
        "standardized_program": "Mathematics",
        "standardized_university": "Stanford University"
    }


# Tests for _normalize_input function
def test_normalize_input_list():
    """Test with direct list input."""
    input_data = [{"program": "CS"}, {"program": "Math"}]
    result = _normalize_input(input_data)
    assert result == input_data


def test_normalize_input_dict_with_rows():
    """Test with dict containing rows key."""
    input_data = {"rows": [{"program": "CS"}, {"program": "Math"}]}
    result = _normalize_input(input_data)
    assert result == [{"program": "CS"}, {"program": "Math"}]


def test_normalize_input_invalid():
    """Test with invalid input formats."""
    assert _normalize_input("string") == []
    assert _normalize_input(123) == []
    assert _normalize_input({"no_rows": []}) == []
    assert _normalize_input({"rows": "not_a_list"}) == []


# Tests for Flask routes
def test_health_route():
    """Test the health check route."""
    with app.test_client() as client:
        response = client.get('/')
        assert response.status_code == 200
        data = response.get_json()
        assert data == {"ok": True}


@patch('llm_hosting.app._call_llm')
def test_standardize_route_success(mock_call_llm):
    """Test the standardize route with valid input."""
    mock_call_llm.return_value = {
        "standardized_program": "Computer Science",
        "standardized_university": "MIT"
    }
    
    test_data = [{"program": "CS, MIT", "id": 1}]
    
    with app.test_client() as client:
        response = client.post('/standardize', 
                             json=test_data,
                             content_type='application/json')
        
        assert response.status_code == 200
        data = response.get_json()
        
        expected = {
            "rows": [{
                "program": "CS, MIT",
                "id": 1,
                "llm-generated-program": "Computer Science",
                "llm-generated-university": "MIT"
            }]
        }
        assert data == expected


@patch('llm_hosting.app._call_llm')
def test_standardize_route_with_rows_wrapper(mock_call_llm):
    """Test the standardize route with rows wrapper."""
    mock_call_llm.return_value = {
        "standardized_program": "Mathematics",
        "standardized_university": "Stanford"
    }
    
    test_data = {"rows": [{"program": "Math, Stanford"}]}
    
    with app.test_client() as client:
        response = client.post('/standardize',
                             json=test_data,
                             content_type='application/json')
        
        assert response.status_code == 200
        data = response.get_json()
        
        expected = {
            "rows": [{
                "program": "Math, Stanford",
                "llm-generated-program": "Mathematics",
                "llm-generated-university": "Stanford"
            }]
        }
        assert data == expected


@patch('llm_hosting.app._call_llm')
def test_standardize_route_empty_program(mock_call_llm):
    """Test the standardize route with empty program."""
    mock_call_llm.return_value = {
        "standardized_program": "",
        "standardized_university": "Unknown"
    }
    
    test_data = [{"other_field": "value"}]
    
    with app.test_client() as client:
        response = client.post('/standardize',
                             json=test_data,
                             content_type='application/json')
        
        assert response.status_code == 200
        mock_call_llm.assert_called_once_with("")


if __name__ == '__main__':
    pytest.main([__file__])