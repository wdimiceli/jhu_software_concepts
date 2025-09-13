import psycopg
import psycopg.rows
import atexit


conn = psycopg.connect(
    dbname="admissions",
    user="student",
    password="modernsoftwareconcepts",
    host="localhost",
    port=5432
)


class AdmissionsEntry:
    @classmethod
    def count(cls):
        """"""
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) from admissions_info;
            """)

            return cur.fetchone()[0] # type: ignore
        
    @classmethod
    def fetch(cls, offset = 0, limit = 10):
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute("""
                SELECT * from admissions_info
                    OFFSET %s
                    LIMIT %s;
            """,
            (offset, limit))

            return list(cur.fetchall())


@atexit.register
def gracefully_close():
    if conn:
        conn.close()
