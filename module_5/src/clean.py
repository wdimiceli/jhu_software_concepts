# -*- coding: utf-8 -*-
"""Data cleaning and standardization using local LLM.

Standardizes university and program names using TinyLlama model with fuzzy matching
and pattern-based normalization.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import difflib
from typing import Dict, List, Tuple

from huggingface_hub import hf_hub_download
from llama_cpp import Llama


# ---------------- Model configuration ----------------
MODEL_REPO = "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF"
MODEL_FILE = "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
N_THREADS = os.cpu_count() or 2
N_CTX = 2048
N_GPU_LAYERS = 0  # CPU-only


# Canonical data files
CANON_UNIS_PATH = Path(__file__).parent / "canon_universities.txt"
CANON_PROGS_PATH = Path(__file__).parent / "canon_programs.txt"


# JSON pattern matcher
JSON_OBJ_RE = re.compile(r"\{.*?\}", re.DOTALL)


# ---------------- Canonical data loading ----------------
def _read_lines(path: str) -> List[str]:
    """Read non-empty lines from file.
    
    :param path: Path to text file.
    :type path: str
    :returns: List of non-empty lines.
    :rtype: List[str]
    :raises FileNotFoundError: If file doesn't exist.
    :raises IOError: If file can't be read.
    """
    with open(path, "r", encoding="utf-8") as f:
        return [ln.strip() for ln in f if ln.strip()]


CANON_UNIS = _read_lines(str(CANON_UNIS_PATH))
CANON_PROGS = _read_lines(str(CANON_PROGS_PATH))


# Consolidated normalization rules
NORMALIZATION_RULES = {
    "universities": {
        "abbreviations": {
            r"(?i)^mcg(\.|ill)?$": "McGill University",
            r"(?i)^(ubc|u\.?b\.?c\.?)$": "University of British Columbia",
            r"(?i)^uoft$": "University of Toronto",
        },
        "fixes": {
            "McGiill University": "McGill University",
            "Mcgill University": "McGill University",
            "University Of British Columbia": "University of British Columbia",
        },
        "canonical": CANON_UNIS,
    },
    "programs": {
        "fixes": {
            "Mathematic": "Mathematics",
            "Info Studies": "Information Studies",
        },
        "canonical": CANON_PROGS,
    },
}


# ---------------- Simplified prompt ----------------
SYSTEM_PROMPT = (
    "You are a data cleaning assistant. Standardize degree program and university names.\n\n"
    "Rules:\n"
    "- Split input into (program name, university name)\n"
    "- Use Title Case for programs, official capitalization for universities\n"
    "- Expand abbreviations (McG -> McGill University, UBC -> University of British Columbia)\n"
    "- If university unknown, return 'Unknown'\n\n"
    "Return JSON with keys: standardized_program, standardized_university"
)


FEW_SHOTS: List[Tuple[Dict[str, str], Dict[str, str]]] = [
    (
        {"program": "Information Studies, McGill University"},
        {
            "standardized_program": "Information Studies",
            "standardized_university": "McGill University",
        },
    ),
    (
        {"program": "Information, McG"},
        {
            "standardized_program": "Information Studies",
            "standardized_university": "McGill University",
        },
    ),
    (
        {"program": "Mathematics, University Of British Columbia"},
        {
            "standardized_program": "Mathematics",
            "standardized_university": "University of British Columbia",
        },
    ),
]


_LLM: Llama | None = None


def _load_llm() -> Llama:
    """Download and initialize LLM model.
    
    :returns: Initialized LLM model instance.
    :rtype: Llama
    :raises Exception: If model download or initialization fails.
    """
    global _LLM
    if _LLM is None:
        model_path = hf_hub_download(
            repo_id=MODEL_REPO,
            filename=MODEL_FILE,
            local_dir="models",
            local_dir_use_symlinks=False,
            force_filename=MODEL_FILE,
        )

        _LLM = Llama(
            model_path=model_path,
            n_ctx=N_CTX,
            n_threads=N_THREADS,
            n_gpu_layers=N_GPU_LAYERS,
            verbose=False,
        )

    return _LLM


def _split_fallback(text: str) -> Tuple[str, str]:
    """Parse text when LLM returns non-JSON response.
    
    :param text: Input text to parse.
    :type text: str
    :returns: Tuple of (program_name, university_name).
    :rtype: Tuple[str, str]
    """
    s = re.sub(r"\s+", " ", (text or "")).strip().strip(",")
    parts = [p.strip() for p in re.split(r",| at | @ ", s) if p.strip()]
    prog = parts[0] if parts else ""
    uni = parts[1] if len(parts) > 1 else ""

    # Apply university abbreviation expansions first
    expanded = False
    for pattern, expansion in NORMALIZATION_RULES["universities"]["abbreviations"].items():
        if re.fullmatch(pattern, uni or ""):
            uni = expansion
            expanded = True
            break

    # Title-case program
    prog = prog.title()

    # Handle university capitalization
    if uni:
        if not expanded:
            # Only title case if it wasn't already expanded to proper name
            uni = uni.title()
        # Apply common fixes after any title casing
        uni = NORMALIZATION_RULES["universities"]["fixes"].get(uni, uni)
        # Normalize 'Of' -> 'of'
        uni = re.sub(r"\bOf\b", "of", uni)
    else:
        uni = "Unknown"

    return prog, uni


def _best_match(name: str, candidates: List[str], cutoff: float = 0.86) -> str | None:
    """Find best fuzzy match using difflib.
    
    :param name: Name to match.
    :type name: str
    :param candidates: List of canonical names.
    :type candidates: List[str]
    :param cutoff: Minimum similarity threshold.
    :type cutoff: float
    :returns: Best matching name or None.
    :rtype: str | None
    """
    if not name or not candidates:
        return None
    matches = difflib.get_close_matches(name, candidates, n=1, cutoff=cutoff)
    return matches[0] if matches else None


def _normalize_text(text: str, text_type: str) -> str:
    """Normalize text using rules for programs or universities.
    
    :param text: Text to normalize.
    :type text: str
    :param text_type: Type - "programs" or "universities".
    :type text_type: str
    :returns: Normalized text.
    :rtype: str
    """
    rules = NORMALIZATION_RULES[text_type]
    normalized = (text or "").strip()
    expanded = False

    # Apply abbreviation expansions (universities only)
    if "abbreviations" in rules:
        for pattern, expansion in rules["abbreviations"].items():
            if re.fullmatch(pattern, normalized):
                normalized = expansion
                expanded = True
                break

    # Apply capitalization rules
    if text_type == "programs":
        normalized = normalized.title()
        # Apply common fixes after title casing
        normalized = rules["fixes"].get(normalized, normalized)
    else:  # universities
        if normalized:
            if not expanded:
                # Only title case if it wasn't already expanded to proper name
                normalized = normalized.title()
            # Apply common fixes after any title casing
            normalized = rules["fixes"].get(normalized, normalized)
            # Normalize 'Of' -> 'of'
            normalized = re.sub(r"\bOf\b", "of", normalized)

    # Check canonical list or fuzzy match
    canonical = rules["canonical"]
    if normalized in canonical:
        return normalized

    cutoff = 0.84 if text_type == "programs" else 0.86
    match = _best_match(normalized, canonical, cutoff=cutoff)

    if text_type == "universities":
        return match or normalized or "Unknown"
    else:
        return match or normalized


def call_llm(program_text: str) -> Dict[str, str]:
    """Standardize program and university names using LLM.
    
    :param program_text: Input text with program and university.
    :type program_text: str
    :returns: Dictionary with standardized_program and standardized_university keys.
    :rtype: Dict[str, str]
    :raises Exception: If LLM processing fails.
    """
    llm = _load_llm()

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for x_in, x_out in FEW_SHOTS:
        messages.append({"role": "user", "content": json.dumps(x_in, ensure_ascii=False)})
        messages.append({"role": "assistant", "content": json.dumps(x_out, ensure_ascii=False)})
    messages.append(
        {"role": "user", "content": json.dumps({"program": program_text}, ensure_ascii=False)}
    )

    out = llm.create_chat_completion(
        messages=messages,
        temperature=0.0,
        max_tokens=128,
        top_p=1.0,
    )

    text = (out["choices"][0]["message"]["content"] or "").strip()
    try:
        match = JSON_OBJ_RE.search(text)
        obj = json.loads(match.group(0) if match else text)
        std_prog = str(obj.get("standardized_program", "")).strip()
        std_uni = str(obj.get("standardized_university", "")).strip()
    except Exception:
        std_prog, std_uni = _split_fallback(program_text)

    std_prog = _normalize_text(std_prog, "programs")
    std_uni = _normalize_text(std_uni, "universities")

    return {
        "standardized_program": std_prog,
        "standardized_university": std_uni,
    }
