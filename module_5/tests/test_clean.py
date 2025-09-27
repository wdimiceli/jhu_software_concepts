"""Tests for src/clean.py."""

import pytest
from unittest.mock import patch, MagicMock

from clean import _load_llm, _split_fallback, _best_match, _normalize_text, call_llm


@pytest.mark.db
@patch("clean._LLM", None)
@patch("clean.hf_hub_download")
@patch("clean.Llama")
def test_load_llm_first_time(mock_llama, mock_hf_download):
    """Test _load_llm when loading for the first time."""
    mock_hf_download.return_value = "/path/to/model.gguf"
    mock_llama_instance = MagicMock()
    mock_llama.return_value = mock_llama_instance

    result = _load_llm()

    # Verify HuggingFace download was called correctly
    mock_hf_download.assert_called_once()

    # Verify Llama was initialized correctly
    mock_llama.assert_called_once()

    assert result == mock_llama_instance


@pytest.mark.db
def test_split_fallback_basic():
    """Test basic program, university splitting."""
    result = _split_fallback("Computer Science, Stanford University")
    assert result == ("Computer Science", "Stanford University")


@pytest.mark.db
def test_split_fallback_with_at():
    """Test splitting with 'at' separator."""
    result = _split_fallback("Mathematics at MIT")
    assert result == ("Mathematics", "Mit")


@pytest.mark.db
def test_split_fallback_mcgill_expansion():
    """Test McGill abbreviation expansion."""
    result = _split_fallback("Computer Science, McG")
    assert result == ("Computer Science", "McGill University")

    result = _split_fallback("Data Science, mcgill")
    assert result == ("Data Science", "McGill University")


@pytest.mark.db
def test_split_fallback_ubc_expansion():
    """Test UBC abbreviation expansion."""
    result = _split_fallback("Engineering, UBC")
    assert result == ("Engineering", "University of British Columbia")

    result = _split_fallback("Physics, u.b.c.")
    assert result == ("Physics", "University of British Columbia")


@pytest.mark.db
def test_split_fallback_single_part():
    """Test with only program, no university."""
    result = _split_fallback("Computer Science")
    assert result == ("Computer Science", "Unknown")


@pytest.mark.db
def test_split_fallback_empty_input():
    """Test with empty or None input."""
    result = _split_fallback("")
    assert result == ("", "Unknown")

    result = _split_fallback(None)
    assert result == ("", "Unknown")


@pytest.mark.db
def test_split_fallback_normalize_of():
    """Test normalization of 'Of' to 'of'."""
    result = _split_fallback("Math, University Of Toronto")
    assert result == ("Math", "University of Toronto")


# Tests for _best_match function
@pytest.mark.db
def test_best_match_exact():
    """Test exact match."""
    candidates = ["Computer Science", "Mathematics", "Physics"]
    result = _best_match("Computer Science", candidates)
    assert result == "Computer Science"


@pytest.mark.db
def test_best_match_close():
    """Test close match above cutoff."""
    candidates = ["Computer Science", "Mathematics", "Physics"]
    result = _best_match("Computer Sciences", candidates, cutoff=0.8)
    assert result == "Computer Science"


@pytest.mark.db
def test_best_match_no_match():
    """Test no match below cutoff."""
    candidates = ["Computer Science", "Mathematics", "Physics"]
    result = _best_match("Biology", candidates, cutoff=0.86)
    assert result is None


@pytest.mark.db
def test_best_match_empty_input():
    """Test with empty inputs."""
    assert _best_match("", ["test"]) is None
    assert _best_match("test", []) is None
    assert _best_match(None, ["test"]) is None


@pytest.mark.db
@patch("clean.NORMALIZATION_RULES")
def test_normalize_text_program_common_fix(mock_rules):
    """Test common program fixes."""
    mock_rules.__getitem__.return_value = {
        "fixes": {"Mathematic": "Mathematics"},
        "canonical": ["Mathematics"],
    }
    result = _normalize_text("Mathematic", "programs")
    assert result == "Mathematics"


@pytest.mark.db
@patch("clean.NORMALIZATION_RULES")
def test_normalize_text_program_canonical(mock_rules):
    """Test program in canonical list."""
    mock_rules.__getitem__.return_value = {"fixes": {}, "canonical": ["Computer Science"]}
    result = _normalize_text("Computer Science", "programs")
    assert result == "Computer Science"


@pytest.mark.db
@patch("clean.NORMALIZATION_RULES")
@patch("clean._best_match")
def test_normalize_text_program_fuzzy_match(mock_best_match, mock_rules):
    """Test fuzzy matching for programs."""
    mock_rules.__getitem__.return_value = {"fixes": {}, "canonical": ["Computer Science"]}
    mock_best_match.return_value = "Computer Science"
    result = _normalize_text("comp sci", "programs")
    assert result == "Computer Science"


@pytest.mark.db
@patch("clean.NORMALIZATION_RULES")
@patch("clean._best_match")
def test_normalize_text_program_no_match(mock_best_match, mock_rules):
    """Test program with no match."""
    mock_rules.__getitem__.return_value = {"fixes": {}, "canonical": []}
    mock_best_match.return_value = None
    result = _normalize_text("Biology", "programs")
    assert result == "Biology"


@pytest.mark.db
def test_normalize_text_university_abbreviation():
    """Test university abbreviation expansion."""
    result = _normalize_text("mcg", "universities")
    assert result == "McGill University"


@pytest.mark.db
@patch("clean.NORMALIZATION_RULES")
def test_normalize_text_university_common_fix(mock_rules):
    """Test common university fixes."""
    mock_rules.__getitem__.return_value = {
        "abbreviations": {},
        "fixes": {"Mcgill University": "McGill University"},
        "canonical": ["McGill University"],
    }
    result = _normalize_text("Mcgill University", "universities")
    assert result == "McGill University"


@pytest.mark.db
@patch("clean.NORMALIZATION_RULES")
def test_normalize_text_university_canonical(mock_rules):
    """Test university in canonical list."""
    mock_rules.__getitem__.return_value = {
        "abbreviations": {},
        "fixes": {},
        "canonical": ["McGill University"],
    }
    result = _normalize_text("McGill University", "universities")
    assert result == "McGill University"


@pytest.mark.db
@patch("clean.NORMALIZATION_RULES")
@patch("clean._best_match")
def test_normalize_text_university_fuzzy_match(mock_best_match, mock_rules):
    """Test fuzzy matching for universities."""
    mock_rules.__getitem__.return_value = {
        "abbreviations": {},
        "fixes": {},
        "canonical": ["Stanford University"],
    }
    mock_best_match.return_value = "Stanford University"
    result = _normalize_text("stanford", "universities")
    assert result == "Stanford University"


@pytest.mark.db
@patch("clean.NORMALIZATION_RULES")
@patch("clean._best_match")
def test_normalize_text_university_no_match(mock_best_match, mock_rules):
    """Test university with no match."""
    mock_rules.__getitem__.return_value = {"abbreviations": {}, "fixes": {}, "canonical": []}
    mock_best_match.return_value = None
    result = _normalize_text("Unknown Uni", "universities")
    assert result == "Unknown Uni"


@pytest.mark.db
def test_normalize_text_university_empty():
    """Test empty university input."""
    result = _normalize_text("", "universities")
    assert result == "Unknown"


@pytest.mark.db
@patch("clean.NORMALIZATION_RULES")
@patch("clean._best_match")
def test_normalize_text_university_normalize_of(mock_best_match, mock_rules):
    """Test normalization of 'Of' to 'of'."""
    mock_rules.__getitem__.return_value = {"abbreviations": {}, "fixes": {}, "canonical": []}
    mock_best_match.return_value = None
    result = _normalize_text("University Of Toronto", "universities")
    assert result == "University of Toronto"


@pytest.mark.db
@patch("clean._load_llm")
@patch("clean._normalize_text")
def test_call_llm_partial_json_extraction(mock_normalize, mock_load_llm):
    """Test LLM call with JSON embedded in text."""
    mock_llm = MagicMock()
    mock_load_llm.return_value = mock_llm
    mock_llm.create_chat_completion.return_value = {
        "choices": [
            {
                "message": {
                    "content": "Here is the result: {"
                    '"standardized_program": "Math",'
                    '"standardized_university": "Stanford"} hope this helps!'
                }
            }
        ]
    }
    mock_normalize.side_effect = lambda text, text_type: {
        ("Math", "programs"): "Mathematics",
        ("Stanford", "universities"): "Stanford University",
    }[(text, text_type)]

    result = call_llm("Math, Stanford")

    assert result == {
        "standardized_program": "Mathematics",
        "standardized_university": "Stanford University",
    }
