"""Comprehensive tests for src/clean.py to achieve 100% coverage."""

import json
import os
import sys
import pytest
from unittest.mock import patch, MagicMock, mock_open

# Add src to path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from clean import (
    _read_lines, _load_llm, _split_fallback, _best_match,
    _normalize_text, call_llm, NORMALIZATION_RULES
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
@patch('clean._LLM', None)
@patch('clean.hf_hub_download')
@patch('clean.Llama')
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


@patch('clean._LLM')
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
    assert result == ("Computer Science", "McGill University")
    
    result = _split_fallback("Data Science, mcgill")
    assert result == ("Data Science", "McGill University")


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


# Tests for _normalize_text function
@patch('clean.NORMALIZATION_RULES')
def test_normalize_text_program_common_fix(mock_rules):
    """Test common program fixes."""
    mock_rules.__getitem__.return_value = {
        'fixes': {'Mathematic': 'Mathematics'},
        'canonical': ['Mathematics']
    }
    result = _normalize_text('Mathematic', 'programs')
    assert result == 'Mathematics'


@patch('clean.NORMALIZATION_RULES')
def test_normalize_text_program_canonical(mock_rules):
    """Test program in canonical list."""
    mock_rules.__getitem__.return_value = {
        'fixes': {},
        'canonical': ['Computer Science']
    }
    result = _normalize_text('Computer Science', 'programs')
    assert result == 'Computer Science'


@patch('clean.NORMALIZATION_RULES')
@patch('clean._best_match')
def test_normalize_text_program_fuzzy_match(mock_best_match, mock_rules):
    """Test fuzzy matching for programs."""
    mock_rules.__getitem__.return_value = {
        'fixes': {},
        'canonical': ['Computer Science']
    }
    mock_best_match.return_value = 'Computer Science'
    result = _normalize_text('comp sci', 'programs')
    assert result == 'Computer Science'


@patch('clean.NORMALIZATION_RULES')
@patch('clean._best_match')
def test_normalize_text_program_no_match(mock_best_match, mock_rules):
    """Test program with no match."""
    mock_rules.__getitem__.return_value = {
        'fixes': {},
        'canonical': []
    }
    mock_best_match.return_value = None
    result = _normalize_text('Biology', 'programs')
    assert result == 'Biology'


def test_normalize_text_university_abbreviation():
    """Test university abbreviation expansion."""
    result = _normalize_text('mcg', 'universities')
    assert result == 'McGill University'


@patch('clean.NORMALIZATION_RULES')
def test_normalize_text_university_common_fix(mock_rules):
    """Test common university fixes."""
    mock_rules.__getitem__.return_value = {
        'abbreviations': {},
        'fixes': {'Mcgill University': 'McGill University'},
        'canonical': ['McGill University']
    }
    result = _normalize_text('Mcgill University', 'universities')
    assert result == 'McGill University'


@patch('clean.NORMALIZATION_RULES')
def test_normalize_text_university_canonical(mock_rules):
    """Test university in canonical list."""
    mock_rules.__getitem__.return_value = {
        'abbreviations': {},
        'fixes': {},
        'canonical': ['McGill University']
    }
    result = _normalize_text('McGill University', 'universities')
    assert result == 'McGill University'


@patch('clean.NORMALIZATION_RULES')
@patch('clean._best_match')
def test_normalize_text_university_fuzzy_match(mock_best_match, mock_rules):
    """Test fuzzy matching for universities."""
    mock_rules.__getitem__.return_value = {
        'abbreviations': {},
        'fixes': {},
        'canonical': ['Stanford University']
    }
    mock_best_match.return_value = 'Stanford University'
    result = _normalize_text('stanford', 'universities')
    assert result == 'Stanford University'


@patch('clean.NORMALIZATION_RULES')
@patch('clean._best_match')
def test_normalize_text_university_no_match(mock_best_match, mock_rules):
    """Test university with no match."""
    mock_rules.__getitem__.return_value = {
        'abbreviations': {},
        'fixes': {},
        'canonical': []
    }
    mock_best_match.return_value = None
    result = _normalize_text('Unknown Uni', 'universities')
    assert result == 'Unknown Uni'


def test_normalize_text_university_empty():
    """Test empty university input."""
    result = _normalize_text('', 'universities')
    assert result == 'Unknown'


@patch('clean.NORMALIZATION_RULES')
@patch('clean._best_match')
def test_normalize_text_university_normalize_of(mock_best_match, mock_rules):
    """Test normalization of 'Of' to 'of'."""
    mock_rules.__getitem__.return_value = {
        'abbreviations': {},
        'fixes': {},
        'canonical': []
    }
    mock_best_match.return_value = None
    result = _normalize_text('University Of Toronto', 'universities')
    assert result == 'University of Toronto'


# Tests for call_llm function
@patch('clean._load_llm')
@patch('clean._normalize_text')
def test_call_llm_success(mock_normalize, mock_load_llm):
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
    mock_normalize.side_effect = lambda text, text_type: {
        ('Computer Science', 'programs'): 'Computer Science',
        ('MIT', 'universities'): 'Massachusetts Institute of Technology'
    }[(text, text_type)]
    
    result = call_llm("CS, MIT")
    
    assert result == {
        "standardized_program": "Computer Science",
        "standardized_university": "Massachusetts Institute of Technology"
    }
    assert mock_normalize.call_count == 2


@patch('clean._load_llm')
@patch('clean._split_fallback')
@patch('clean._normalize_text')
def test_call_llm_invalid_json_fallback(mock_normalize, mock_fallback, mock_load_llm):
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
    mock_normalize.side_effect = lambda text, text_type: {
        ('Computer Science', 'programs'): 'Computer Science',
        ('MIT', 'universities'): 'Massachusetts Institute of Technology'
    }[(text, text_type)]
    
    result = call_llm("CS, MIT")
    
    mock_fallback.assert_called_once_with("CS, MIT")
    assert result == {
        "standardized_program": "Computer Science",
        "standardized_university": "Massachusetts Institute of Technology"
    }


@patch('clean._load_llm')
@patch('clean._normalize_text')
def test_call_llm_partial_json_extraction(mock_normalize, mock_load_llm):
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
    mock_normalize.side_effect = lambda text, text_type: {
        ('Math', 'programs'): 'Mathematics',
        ('Stanford', 'universities'): 'Stanford University'
    }[(text, text_type)]
    
    result = call_llm("Math, Stanford")
    
    assert result == {
        "standardized_program": "Mathematics",
        "standardized_university": "Stanford University"
    }


@patch('clean._load_llm')
@patch('clean._normalize_text')
def test_call_llm_empty_content(mock_normalize, mock_load_llm):
    """Test LLM call with empty or None content."""
    mock_llm = MagicMock()
    mock_load_llm.return_value = mock_llm
    mock_llm.create_chat_completion.return_value = {
        'choices': [{
            'message': {
                'content': None
            }
        }]
    }
    
    with patch('clean._split_fallback') as mock_fallback:
        mock_fallback.return_value = ("", "Unknown")
        mock_normalize.side_effect = lambda text, text_type: {
            ('', 'programs'): '',
            ('Unknown', 'universities'): 'Unknown'
        }[(text, text_type)]
        
        result = call_llm("")
        
        mock_fallback.assert_called_once_with("")
        assert result == {
            "standardized_program": "",
            "standardized_university": "Unknown"
        }


if __name__ == '__main__':
    pytest.main([__file__])