"""A data loader for TheGradCafe scraper.

This module provides functionality to load scraped admissions data into a PostgreSQL database.
"""

import json
from model import AdmissionResult, init_tables
import postgres_manager


def load_admissions_results(filename: str):
    """Read admissions data from disk and loads it into the database."""
    init_tables()

    print("Beginning data ingestion...")

    # Read the data from the specified JSON file
    with open(filename, "r") as f:
        entries = json.load(f)

    print(f"Read {len(entries)} entries from JSON file {filename} ...")

    # Save each entry to the database
    conn = postgres_manager.get_connection()
    with conn.cursor() as cursor:
        for entry in entries:
            AdmissionResult.from_dict(entry).save_to_db(cursor)

    conn.commit()

    count = AdmissionResult.count()

    print(f"Loaded {count} entries")

