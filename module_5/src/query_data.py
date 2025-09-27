"""Predefined database queries for admissions data analysis."""

from model import AdmissionResult, get_table
from psycopg import sql
import postgres_manager


def safe_format(value, fmt: str = "{:.2f}") -> str:
    """Format value safely, returning 'N/A' for None.

    :param value: Value to format.
    :param fmt: Format string.
    :type fmt: str
    :returns: Formatted string or 'N/A'.
    :rtype: str
    """
    if value is None:
        return "N/A"
    return fmt.format(value)


def answer_questions() -> list[dict]:
    """Execute predefined queries and return formatted results.

    :returns: List of dictionaries with prompt, answer, and formatted fields.
    :rtype: list[dict]
    :raises psycopg.Error: If database query fails.
    """
    queries = [
        {
            "prompt": "How many entries do you have in your database who have applied for Fall 2025?",

            "statement": sql.SQL(
                "SELECT COUNT(*) as count FROM {} WHERE year=%s AND season=%s LIMIT {};"
            ).format(sql.Identifier(get_table()), sql.Literal(postgres_manager.QUERY_LIMIT)),

            "parameters": (2025, "fall"),

            "answer": lambda statement, parameters: AdmissionResult.execute_raw(
                statement, parameters
            )[0]["count"],

            "formatted": lambda result: f"Applicant count: {str(result)}",
        },
        {
            "prompt": "What percentage of entries are from international students?",

            "statement": sql.SQL(
                """
                SELECT intl_student_count * 100.0 / NULLIF(total, 0) as pct
                FROM (
                    SELECT
                        COUNT(*) AS total,
                        COUNT(*) FILTER (WHERE us_or_international=%s) as intl_student_count
                    FROM {}
                ) AS intl_students
                LIMIT {};
                """
            ).format(sql.Identifier(get_table()), sql.Literal(postgres_manager.QUERY_LIMIT)),

            "parameters": ("international",),

            "answer": lambda statement, parameters: AdmissionResult.execute_raw(
                statement, parameters
            )[0]["pct"],

            "formatted": lambda result: f"Percent international: {safe_format(result)}%",
        },
        {
            "prompt": "What is the average GPA, GRE, GRE V, GRE AW of applicants who provide these metrics?",

            "statement": sql.SQL(
                """
                SELECT
                    AVG(gpa) as avg_gpa,
                    AVG(gre) as avg_gre,
                    AVG(gre_v) as avg_gre_v,
                    AVG(gre_aw) as avg_gre_aw
                FROM {}
                LIMIT {};
                """
            ).format(sql.Identifier(get_table()), sql.Literal(postgres_manager.QUERY_LIMIT)),

            "parameters": (),

            "answer": lambda statement, parameters: AdmissionResult.execute_raw(
                statement, parameters
            )[0],

            "formatted": lambda result: ", ".join(
                [
                    f"GPA: {safe_format(result['avg_gpa'])}",
                    f"GRE: {safe_format(result['avg_gre'])}",
                    f"GRE Verbal: {safe_format(result['avg_gre_v'])}",
                    f"GRE AW: {safe_format(result['avg_gre_aw'])}",
                ]
            ),
        },
        {
            "prompt": "What is the average GPA of American students in Fall 2025?",

            "statement": sql.SQL(
                """
                SELECT AVG(gpa) as avg_gpa
                FROM {}
                WHERE year=%s AND season=%s AND us_or_international != %s
                LIMIT {};
                """
            ).format(sql.Identifier(get_table()), sql.Literal(postgres_manager.QUERY_LIMIT)),

            "parameters": (2025, "fall", "international"),

            "answer": lambda statement, parameters: AdmissionResult.execute_raw(
                statement, parameters
            )[0]["avg_gpa"],

            "formatted": lambda result: f"Average GPA: {safe_format(result)}",
        },
        {
            "prompt": "What percent of entries for Fall 2025 are Acceptances?",

            "statement": sql.SQL(
                """
                SELECT accepted * 100.0 / NULLIF(total, 0) as pct
                FROM (
                    SELECT COUNT(*) AS total,
                        COUNT(*) FILTER (WHERE status=%s) as accepted
                    FROM {}
                    WHERE year=%s AND season=%s
                ) AS fall_2025_students
                LIMIT {};
                """
            ).format(sql.Identifier(get_table()), sql.Literal(postgres_manager.QUERY_LIMIT)),

            "parameters": ("accepted", 2025, "fall"),

            "answer": lambda statement, parameters: AdmissionResult.execute_raw(
                statement, parameters
            )[0]["pct"],

            "formatted": lambda result: f"Percent accepted: {safe_format(result)}%",
        },
        {
            "prompt": "What is the average GPA of applicants who applied for Fall 2025 who are Acceptances?",

            "statement": sql.SQL(
                """
                SELECT AVG(gpa) as avg_gpa
                FROM {}
                WHERE status=%s AND year=%s AND season=%s
                LIMIT {};
                """
            ).format(sql.Identifier(get_table()), sql.Literal(postgres_manager.QUERY_LIMIT)),

            "parameters": ("accepted", 2025, "fall"),

            "answer": lambda statement, parameters: AdmissionResult.execute_raw(
                statement, parameters
            )[0]["avg_gpa"],

            "formatted": lambda result: f"Average GPA: {safe_format(result)}",
        },
        {
            "prompt": "How many entries are from applicants who applied to JHU for a masters degrees in Computer Science?",

            "statement": sql.SQL(
                """
                SELECT COUNT(*) as count
                FROM {}
                WHERE degree=%s AND llm_generated_university=%s AND llm_generated_program=%s
                LIMIT {};
                """
            ).format(sql.Identifier(get_table()), sql.Literal(postgres_manager.QUERY_LIMIT)),

            "parameters": ("masters", "Johns Hopkins University", "Computer Science"),

            "answer": lambda statement, parameters: AdmissionResult.execute_raw(
                statement, parameters
            )[0]["count"],

            "formatted": lambda result: f"Applicant count: {str(result)}",
        },
        {
            "prompt": "How many entries from 2025 are acceptances from applicants who applied to Georgetown University for a PhD in Computer Science?",

            "statement": sql.SQL(
                """
                SELECT COUNT(*) as count
                FROM {}
                WHERE degree=%s AND llm_generated_university=%s AND llm_generated_program=%s
                    AND year=%s AND status=%s
                LIMIT {};
                """
            ).format(sql.Identifier(get_table()), sql.Literal(postgres_manager.QUERY_LIMIT)),

            "parameters": ("phd", "George Town University", "Computer Science", 2025, "accepted"),

            "answer": lambda statement, parameters: AdmissionResult.execute_raw(
                statement, parameters
            )[0]["count"],

            "formatted": lambda result: f"Applicant count: {str(result)}",
        },
        {
            "prompt": "What is the average GPA for students accepted to UCLA vs USC?",

            "statement": sql.SQL(
                """
                SELECT
                    AVG(gpa) FILTER (WHERE llm_generated_university=%s) as avg_gpa_ucla,
                    AVG(gpa) FILTER (WHERE llm_generated_university=%s) as avg_gpa_usc
                FROM {}
                WHERE status=%s
                LIMIT {};
                """
            ).format(sql.Identifier(get_table()), sql.Literal(postgres_manager.QUERY_LIMIT)),

            "parameters": (
                "University of California, Los Angeles (Ucla)",
                "University of Southern California",
                "accepted",
            ),

            "answer": lambda statement, parameters: AdmissionResult.execute_raw(
                statement, parameters
            )[0],

            "formatted": lambda result: ", ".join(
                [
                    f"UCLA average GPA: {safe_format(result['avg_gpa_ucla'])}",
                    f"USC average GPA: {safe_format(result['avg_gpa_usc'])}",
                ]
            ),
        },
        {
            "prompt": "What is the average GRE for students in the past 4 years?",

            "statement": sql.SQL(
                """
                SELECT
                    AVG(gre) FILTER (WHERE year=%s) as avg_gre_2021,
                    AVG(gre) FILTER (WHERE year=%s) as avg_gre_2022,
                    AVG(gre) FILTER (WHERE year=%s) as avg_gre_2023,
                    AVG(gre) FILTER (WHERE year=%s) as avg_gre_2024
                FROM {}
                LIMIT {};
                """
            ).format(sql.Identifier(get_table()), sql.Literal(postgres_manager.QUERY_LIMIT)),

            "parameters": (2021, 2022, 2023, 2024),

            "answer": lambda statement, parameters: AdmissionResult.execute_raw(
                statement, parameters
            )[0],

            "formatted": lambda result: ", ".join(
                [
                    f"2021 average GRE: {safe_format(result['avg_gre_2021'])}",
                    f"2022 average GRE: {safe_format(result['avg_gre_2022'])}",
                    f"2023 average GRE: {safe_format(result['avg_gre_2023'])}",
                    f"2024 average GRE: {safe_format(result['avg_gre_2024'])}",
                ]
            ),
        },
    ]

    for question in queries:
        result = question["answer"](question["statement"], question.get("parameters", ()))
        question["answer"] = result
        question["formatted"] = question["formatted"](result)

    return queries
