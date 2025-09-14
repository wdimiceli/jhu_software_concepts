"""A collection of predefined database queries for the admissions data."""

from model import AdmissionResult


table_name = "admissions_info"


def answer_questions():
    """Return a list of questions and their corresponding SQL-based answers."""
    queries = [
        {
            "prompt":
                "How many entries do you have in your database who have applied for Fall 2025?",

            "answer": AdmissionResult.execute_raw(
                f"""
                SELECT COUNT(*) as count FROM {table_name}
                WHERE year=%s AND season=%s;
            """,
                (2025, "fall"),
            )[0]["count"],

            "formatted": lambda result: f"Applicant count: {str(result)}",
        },

        {
            "prompt":
                "What percentage of entries are from international students?",

            "answer": AdmissionResult.execute_raw(
                f"""
                SELECT
                    intl_student_count * 100.0 / total as pct
                FROM (
                    SELECT
                        COUNT(*) AS total,
                        COUNT(*) FILTER (WHERE us_or_international=%s) as intl_student_count
                    FROM {table_name}
                );
            """,
                ["international"],
            )[0]["pct"],

            "formatted": lambda result: f"Percent international: {result:.2f}%",
        },

        {
            "prompt":
                """What is the average GPA, GRE, GRE V, GRE AW of applicants who provide these
                   metrics?""",

            "answer": AdmissionResult.execute_raw(
                f"""
                SELECT
                    AVG(gpa) as avg_gpa,
                    AVG(gre) as avg_gre,
                    AVG(gre_v) as avg_gre_v,
                    AVG(gre_aw) as avg_gre_aw
                FROM {table_name};
            """,
                [],
            )[0],

            "formatted": lambda result: ', '.join([
                f"GPA: {result["avg_gpa"]:.2f}",
                f"GRE: {result["avg_gre"]:.2f}",
                f"GRE Verbal: {result["avg_gre_v"]:.2f}",
                f"GRE AW: {result["avg_gre_aw"]:.2f}",
            ]),
        },

        {
            "prompt":
                "What is the average GPA of American students in Fall 2025?",

            "answer": AdmissionResult.execute_raw(
                f"""
                SELECT
                    AVG(gpa) as avg_gpa
                FROM {table_name}
                WHERE year=%s AND season=%s;;
            """,
                [2025, "fall"],
            )[0]["avg_gpa"],

            "formatted": lambda result: f"Average GPA: {result:.2f}",
        },

        {
            "prompt":
                "What percent of entries for Fall 2025 are Acceptances?",

            "answer": AdmissionResult.execute_raw(
                f"""
                SELECT
                    accepted * 100.0 / total as pct
                FROM (
                    SELECT
                        COUNT(*) AS total,
                        COUNT(*) FILTER (WHERE status=%s) as accepted
                    FROM {table_name}
                    WHERE year=%s AND season=%s
                );
            """,
                ["accepted", 2025, "fall"],
            )[0]["pct"],

            "formatted": lambda result: f"Percent accepted: {result:.2f}%",
        },

        {
            "prompt":
                """What is the average GPA of applicants who applied for Fall 2025 who are
                   Acceptances?""",

            "answer": AdmissionResult.execute_raw(
                f"""
                SELECT
                    AVG(gpa) as avg_gpa
                FROM {table_name}
                WHERE status=%s AND year=%s AND season=%s;
            """,
                ["accepted", 2025, "fall"],
            )[0]["avg_gpa"],

            "formatted": lambda result: f"Average GPA: {result:.2f}",
        },

        {
            "prompt":
                """How many entries are from applicants who applied to JHU for a masters degrees in
                   Computer Science?""",

            "answer": AdmissionResult.execute_raw(
                f"""
                SELECT
                    COUNT(*)
                FROM {table_name}
                WHERE degree=%s AND llm_generated_university=%s and llm_generated_program=%s;
            """,
                ["masters", "Johns Hopkins University", "Computer Science"],
            )[0]["count"],

            "formatted": lambda result: f"Applicant count: {str(result)}",
        },

        {
            "prompt":
                """How many entries from 2025 are acceptances from applicants who applied to
                   Georgetown University for a PhD in Computer Science?""",

            "answer": AdmissionResult.execute_raw(
                f"""
                SELECT
                    COUNT(*)
                FROM {table_name}
                WHERE
                    degree=%s
                    AND llm_generated_university=%s
                    AND llm_generated_program=%s
                    AND year=%s
                    AND status=%s;
            """,
                ["phd", "George Town University", "Computer Science", 2025, "accepted"],
            )[0]["count"],

            "formatted": lambda result: f"Applicant count: {str(result)}",
        },
    ]

    for question in queries:
        question["formatted"] = question["formatted"](question["answer"])

    return queries
