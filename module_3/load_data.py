"""A data loader for TheGradCafe scraper.

This module provides functionality to load scraped admissions data into a PostgreSQL database.
"""

import argparse
from model import AdmissionResult, init_tables, conn


def load_admissions_results(recreate=False):
    """Read admissions data from disk and loads it into the database."""
    init_tables(recreate)

    # Read the data from the specified JSON file
    entries = AdmissionResult.from_plaintext_rows("llm_extend_applicant_data.json")

    try:
        # Save each entry to the database
        for entry in entries:
            entry.save_to_db()

        conn.commit()

        count = AdmissionResult.count()

        print(f"Loaded {count} entries")
    except Exception as e:
        print("Exception was raised, aborting ...")
        # Re-raise the exception to indicate a failure
        raise e


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Data loader for TheGradCafe scraper PSQL database."
    )

    parser.add_argument(
        "--recreate-tables",
        type=bool,
        required=False,
        help="Wipes all tables and recreates them.",
        default=False,
    )

    args = parser.parse_args()

    load_admissions_results(args.recreate_tables)
