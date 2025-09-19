"""A data loader for TheGradCafe scraper.

This module provides functionality to load scraped admissions data into a PostgreSQL database.
"""

import json
from model import AdmissionResult, init_tables
from postgres_manager import get_connection


def load_admissions_results(filename: str, recreate=False):
    """Read admissions data from disk and loads it into the database."""
    init_tables(recreate)

    print("Beginning data ingestion...")

    # Read the data from the specified JSON file
    with open(filename, "r") as f:
        entries = json.load(f)

    print(f"Read {len(entries)} entries from JSON file {filename} ...")

    try:
        # Save each entry to the database
        for entry in entries:
            AdmissionResult.from_dict(entry).save_to_db()

        get_connection().commit()

        count = AdmissionResult.count()

        print(f"Loaded {count} entries")
    except Exception as e:
        print("Exception was raised, aborting ...")
        # Re-raise the exception to indicate a failure
        raise e


def load_data_if_available(filename="admissions_info.json", recreate=False):
    """Load data from file if it exists, with graceful error handling for startup use."""
    import os
    
    if not os.path.exists(filename):
        print(f"Data file '{filename}' not found, skipping data load")
        return False
    
    try:
        load_admissions_results(filename, recreate)
        return True
    except Exception as e:
        print(f"Failed to load data from '{filename}': {e}")
        return False




