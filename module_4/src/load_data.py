"""Load admissions data from JSON files into PostgreSQL database."""

import json
from model import AdmissionResult, init_tables
import postgres_manager


def load_admissions_results(filename: str) -> None:
    """Load admissions data from JSON file into database.
    
    :param filename: Path to JSON file with admission result data.
    :type filename: str
    :raises FileNotFoundError: If JSON file doesn't exist.
    :raises json.JSONDecodeError: If file contains invalid JSON.
    :raises psycopg.Error: If database operations fail.
    """
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

