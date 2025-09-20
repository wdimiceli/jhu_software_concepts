"""A collection of predefined database queries for the admissions data."""

from model import AdmissionResult, get_table


def safe_format(value, fmt="{:.2f}"):
    """Format a value safely, returning 'N/A' for None."""
    if value is None:
        return "N/A"
    return fmt.format(value)


def answer_questions():
    """Return a list of questions and their corresponding SQL-based answers."""
    queries = [
        {
            "prompt": "How many entries do you have in your database who have applied for Fall 2025?",
            "answer": AdmissionResult.execute_raw(
                f"SELECT COUNT(*) as count FROM {get_table()} WHERE year=%s AND season=%s;",
                (2025, "fall"),
            )[0]["count"],
            "formatted": lambda result: f"Applicant count: {str(result)}",
        },
        {
            "prompt": "What percentage of entries are from international students?",
            "answer": AdmissionResult.execute_raw(
                f"""
                SELECT intl_student_count * 100.0 / NULLIF(total, 0) as pct
                FROM (
                    SELECT
                        COUNT(*) AS total,
                        COUNT(*) FILTER (WHERE us_or_international=%s) as intl_student_count
                    FROM {get_table()}
                ) AS intl_students;
            """,
                ["international"],
            )[0]["pct"],
            "formatted": lambda result: f"Percent international: {safe_format(result)}%",
        },
        {
            "prompt": """What is the average GPA, GRE, GRE V, GRE AW of applicants who provide these metrics?""",
            "answer": AdmissionResult.execute_raw(
                f"""
                SELECT
                    AVG(gpa) as avg_gpa,
                    AVG(gre) as avg_gre,
                    AVG(gre_v) as avg_gre_v,
                    AVG(gre_aw) as avg_gre_aw
                FROM {get_table()};
            """,
                [],
            )[0],
            "formatted": lambda result: ', '.join([
                f"GPA: {safe_format(result['avg_gpa'])}",
                f"GRE: {safe_format(result['avg_gre'])}",
                f"GRE Verbal: {safe_format(result['avg_gre_v'])}",
                f"GRE AW: {safe_format(result['avg_gre_aw'])}",
            ]),
        },
        {
            "prompt": "What is the average GPA of American students in Fall 2025?",
            "answer": AdmissionResult.execute_raw(
                f"""
                SELECT AVG(gpa) as avg_gpa
                FROM {get_table()}
                WHERE year=%s AND season=%s AND us_or_international != %s;
            """,
                [2025, "fall", "international"],
            )[0]["avg_gpa"],
            "formatted": lambda result: f"Average GPA: {safe_format(result)}",
        },
        {
            "prompt": "What percent of entries for Fall 2025 are Acceptances?",
            "answer": AdmissionResult.execute_raw(
                f"""
                SELECT accepted * 100.0 / NULLIF(total, 0) as pct
                FROM (
                    SELECT COUNT(*) AS total,
                           COUNT(*) FILTER (WHERE status=%s) as accepted
                    FROM {get_table()}
                    WHERE year=%s AND season=%s
                ) AS fall_2025_students;
            """,
                ["accepted", 2025, "fall"],
            )[0]["pct"],
            "formatted": lambda result: f"Percent accepted: {safe_format(result)}%",
        },
        {
            "prompt": "What is the average GPA of applicants who applied for Fall 2025 who are Acceptances?",
            "answer": AdmissionResult.execute_raw(
                f"""
                SELECT AVG(gpa) as avg_gpa
                FROM {get_table()}
                WHERE status=%s AND year=%s AND season=%s;
            """,
                ["accepted", 2025, "fall"],
            )[0]["avg_gpa"],
            "formatted": lambda result: f"Average GPA: {safe_format(result)}",
        },
        {
            "prompt": "How many entries are from applicants who applied to JHU for a masters degrees in Computer Science?",
            "answer": AdmissionResult.execute_raw(
                f"""
                SELECT COUNT(*) as count
                FROM {get_table()}
                WHERE degree=%s AND llm_generated_university=%s AND llm_generated_program=%s;
            """,
                ["masters", "Johns Hopkins University", "Computer Science"],
            )[0]["count"],
            "formatted": lambda result: f"Applicant count: {str(result)}",
        },
        {
            "prompt": "How many entries from 2025 are acceptances from applicants who applied to Georgetown University for a PhD in Computer Science?",
            "answer": AdmissionResult.execute_raw(
                f"""
                SELECT COUNT(*) as count
                FROM {get_table()}
                WHERE degree=%s AND llm_generated_university=%s AND llm_generated_program=%s
                      AND year=%s AND status=%s;
            """,
                ["phd", "George Town University", "Computer Science", 2025, "accepted"],
            )[0]["count"],
            "formatted": lambda result: f"Applicant count: {str(result)}",
        },
        {
            "prompt": "What is the average GPA for students accepted to UCLA vs USC?",
            "answer": AdmissionResult.execute_raw(
                f"""
                SELECT
                    AVG(gpa) FILTER (WHERE llm_generated_university=%s) as avg_gpa_ucla,
                    AVG(gpa) FILTER (WHERE llm_generated_university=%s) as avg_gpa_usc
                FROM {get_table()}
                WHERE status=%s;
            """,
                ["University of California, Los Angeles (Ucla)", "University of Southern California", "accepted"],
            )[0],
            "formatted": lambda result: ', '.join([
                f"UCLA average GPA: {safe_format(result['avg_gpa_ucla'])}",
                f"USC average GPA: {safe_format(result['avg_gpa_usc'])}",
            ]),
        },
        {
            "prompt": "What is the average GRE for students in the past 4 years?",
            "answer": AdmissionResult.execute_raw(
                f"""
                SELECT
                    AVG(gre) FILTER (WHERE year=%s) as avg_gre_2021,
                    AVG(gre) FILTER (WHERE year=%s) as avg_gre_2022,
                    AVG(gre) FILTER (WHERE year=%s) as avg_gre_2023,
                    AVG(gre) FILTER (WHERE year=%s) as avg_gre_2024
                FROM {get_table()};
            """,
                [2021, 2022, 2023, 2024],
            )[0],
            "formatted": lambda result: ', '.join([
                f"2021 average GRE: {safe_format(result['avg_gre_2021'])}",
                f"2022 average GRE: {safe_format(result['avg_gre_2022'])}",
                f"2023 average GRE: {safe_format(result['avg_gre_2023'])}",
                f"2024 average GRE: {safe_format(result['avg_gre_2024'])}",
            ]),
        },
    ]

    for question in queries:
        question["formatted"] = question["formatted"](question["answer"])

    return queries
