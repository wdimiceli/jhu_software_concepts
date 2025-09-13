import argparse
import psycopg
from clean import load_data as load_data_from_json


def load_admissions_results(recreate = False):
    """Reads admissions data from disk and loads into the database."""
    connection = psycopg.connect(
        dbname="admissions",
        user="student",
        password="modernsoftwareconcepts",
        host="localhost",
        port=5432
    )

    entries = load_data_from_json("llm_extend_applicant_data.json")

    with connection.cursor() as cur:
        if recreate:
            print("Dropping tables and recreating...")

            cur.execute("""
                DROP TABLE admissions_info;
            """)

            connection.commit()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS admissions_info (
                p_id SERIAL PRIMARY KEY,
                program TEXT,
                comments TEXT,
                date_added DATE,
                url TEXT,
                status TEXT,
                term TEXT,
                us_or_international TEXT,
                gpa FLOAT,
                gre FLOAT,
                gre_v FLOAT,
                gre_aw FLOAT,
                degree TEXT,
                llm_generated_program TEXT,
                llm_generated_university TEXT
            );
        """)

        for entry in entries:
            cur.execute(
                """
                INSERT INTO admissions_info (
                    p_id, program, comments, date_added, url,
                    status, term, us_or_international, gpa, gre, gre_v,
                    gre_aw, degree, llm_generated_program, llm_generated_university
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (p_id) DO UPDATE SET
                    program = EXCLUDED.program,
                    comments = EXCLUDED.comments,
                    date_added = EXCLUDED.date_added,
                    url = EXCLUDED.url,
                    status = EXCLUDED.status,
                    term = EXCLUDED.term,
                    us_or_international = EXCLUDED.us_or_international,
                    gpa = EXCLUDED.gpa,
                    gre = EXCLUDED.gre,
                    gre_v = EXCLUDED.gre_v,
                    gre_aw = EXCLUDED.gre_aw,
                    degree = EXCLUDED.degree,
                    llm_generated_program = EXCLUDED.llm_generated_program,
                    llm_generated_university = EXCLUDED.llm_generated_university;
            """,
                (
                    entry["id"],
                    f"{entry["school"]} {entry["program_name"]}",
                    entry["comments"],
                    entry["added_on"],
                    entry["full_info_url"],
                    entry["decision"]["status"] if entry.get("decision") else None,
                    f"{entry["tags"]["season"]} {entry["tags"]["year"]}",
                    entry["tags"]["school_region"],
                    entry["tags"]["gpa"],
                    entry["tags"]["gre_general"],
                    entry["tags"]["gre_verbal"],
                    entry["tags"]["gre_analytical_writing"],
                    entry["degree_type"],
                    entry["llm-generated-program"],
                    entry["llm-generated-university"],
                ),
            )
    
        connection.commit()
        
        cur.execute("""
            SELECT COUNT(*) from admissions_info;
        """)

        row_count = cur.fetchone()[0] # type: ignore

        print(f"Loaded {row_count} entries")

    connection.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Data loader for TheGradCafe scraper PSQL database.")

    parser.add_argument(
        "--recreate-tables",
        type=bool,
        required=False,
        help="Wipes all tables and recreates them.",
        default=False,
    )

    args = parser.parse_args()

    load_admissions_results(args.recreate_tables)
