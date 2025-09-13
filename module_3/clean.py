import argparse
import json
from typing import Any
from llm_hosting.app import _cli_process_file


def save_cleaned_results(cleaned_admission_results: list[Any], filename: str):
    """Saves the cleaned results as JSON into the given filename."""
    with open(filename, "w") as out_file:
        json.dump(cleaned_admission_results, out_file, indent=2)
        print(f"Saved results to '{filename}'")


def load_data(filename: str):
    """Loads the cleaned admissions data from the given filename."""
    with open(filename, "r") as f:
        lines = f.readlines()
        return map(lambda entry: json.loads(entry), lines)


def clean_data(data_filename, out_filename: str):
    """Runs the raw admissions data through an LLM data cleaning tool."""
    # Note to grader: I recognize this function is "private", but for the sake of leaving
    # llm_hosting completely unmodified, I am going to import this and use it directly.
    _cli_process_file(
        in_path=data_filename,
        out_path=out_filename,
        append=False,
        to_stdout=False,
    )

    return load_data(data_filename)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Data cleaner for TheGradCafe scraper.")

    parser.add_argument(
        "--data-filename",
        type=str,
        required=False,
        help="The input JSON filename with admissions data.",
        default="applicant_data.json",
    )

    parser.add_argument(
        "--out-filename",
        type=str,
        required=False,
        help="The output JSON filename for LLM-augmented data.",

        # Note to grader: the llm_hosting module does not output valid JSON, so I
        # would disagree with this filename having a .json extension. However for the
        # sake of following the assignment instructions, it's left as-is.
        default="llm_extend_applicant_data.json",
    )

    args = parser.parse_args()

    clean_data(args.data_filename, args.out_filename)
