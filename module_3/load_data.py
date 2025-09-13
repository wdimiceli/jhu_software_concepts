import psycopg
import json

connection = psycopg.connect(
    dbname="admissions",
    user="student",
    password="modernsoftwareconcepts",
    host="localhost",
    port=5432
)

with open("llm_extend_applicant_data.json", "r") as f:
    entries = f.readlines()

with connection.cursor() as cur:
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
            gre_v FLOAT
        );
    """)

    for entry in entries:
        entry = json.loads(entry)
        
        cur.execute(
            """
            INSERT INTO admissions_info (
                p_id, program, comments, date_added, url,
                status, term, us_or_international, gpa, gre, gre_v
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
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
                gre_v = EXCLUDED.gre_v;
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
            ),
        )
