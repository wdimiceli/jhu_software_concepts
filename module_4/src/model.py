"""Data models and database operations for admission results."""

import os
import psycopg
import psycopg.rows
import re
from datetime import datetime
from dataclasses import dataclass
from bs4.element import Tag
from psycopg import sql

import clean
import postgres_manager


DB_TABLE = "admissions_info"

def get_table() -> str:
    """Get database table name.
    
    :returns: Table name from DB_TABLE env var or default.
    :rtype: str
    """
    return str(os.environ.get("DB_TABLE", DB_TABLE))


def init_tables() -> None:
    """Create admissions table if it doesn't exist.
    
    :raises psycopg.Error: If table creation fails.
    """
    conn = postgres_manager.get_connection()

    with conn.cursor() as cur:
        cur.execute(sql.SQL("""
            CREATE TABLE IF NOT EXISTS {} (
                p_id INTEGER PRIMARY KEY,
                school TEXT,
                program_name TEXT,
                program TEXT,
                comments TEXT,
                date_added DATE,
                url TEXT,
                status TEXT,
                decision_date DATE,
                season TEXT,
                year INTEGER,
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
        """).format(
            sql.Identifier(get_table())
        ))

        conn.commit()


def _tags_from_soup(tags: set[str]) -> dict[str, any]:
    """Parse HTML tags to extract admission data.

    :param tags: Set of tag strings from HTML.
    :type tags: set[str]
    :returns: Dictionary with parsed season, year, region, and test scores.
    :rtype: dict[str, any]
    """
    expanded = {
        "season": None,
        "year": None,
        "applicant_region": False,
        "gre_general": None,
        "gre_verbal": None,
        "gre_analytical_writing": None,
        "gpa": None,
    }

    for tag in tags:
        tag = tag.lower()

        # -------- Process region --------

        if tag in ["international", "american"]:
            expanded["applicant_region"] = tag
            continue

        # -------- Process grades --------

        grade_match = re.match(r"(?P<test>gpa|gre(?:\s+v|\s+aw)?)\s+(?P<score>[\d\.]+)$", tag)
        if grade_match:
            test: str = grade_match.group("test")
            score: str = grade_match.group("score")

            if test == "gpa":
                expanded["gpa"] = float(score)

            elif test == "gre":
                expanded["gre_general"] = int(score)

            elif test == "gre v":
                expanded["gre_verbal"] = int(score)

            elif test == "gre aw":
                expanded["gre_analytical_writing"] = float(score)

            continue

        # -------- Process term --------

        term_match = re.match(r"(?P<season>[a-z]+)\s*?(?P<year>\d{4}|\d{2})", tag)
        if term_match:
            season = term_match.group("season")

            for season_category in ["fall", "winter", "spring", "summer"]:
                if season_category.startswith(season):
                    expanded["season"] = season
                    break

            year = term_match.group("year")

            year = ("20" + year)[-4:]
            expanded["year"] = int(year)

            continue

    return expanded


def _decision_from_soup(decision_str: str, added_on_year: int) -> tuple[str | None, datetime | None]:
    """Parse decision string to extract status and date.

    :param decision_str: Decision string in format "status on DD MMM".
    :type decision_str: str
    :param added_on_year: Year for date inference.
    :type added_on_year: int
    :returns: Tuple of (status, date).
    :rtype: tuple[str | None, datetime | None]
    """
    match = re.match(
        r"(?P<status>[A-Za-z\s]+?)\s+on\s+(?P<date_str>[0-9]+\s+[A-Za-z]+)$",
        decision_str,
    )

    if not match:
        print(f"Failed to parse decision: {decision_str}")
        return None, None

    status = match.group("status").lower().replace(" ", "_")
    date_part = match.group("date_str")

    parsed_date = datetime.strptime(f"{date_part} {added_on_year}", "%d %b %Y")

    today = datetime.now()

    # Since decision dates only include month/day, we pick the most recent past year
    # that makes sense relative to when the entry was added.

    if parsed_date > today:
        # If it is, subtract one year
        year = today.year - 1
    else:
        # Otherwise, use the current year
        year = today.year

    date = parsed_date.replace(year=year)

    return status, date


@dataclass
class AdmissionResult:
    """Admission result data model with application details and test scores."""

    id: int
    school: str
    program_name: str | None
    degree_type: str | None
    added_on: datetime | None
    decision_status: str | None
    decision_date: datetime | None
    season: str | None
    year: int | None
    applicant_region: str | None
    gre_general: int | None
    gre_verbal: int | None
    gre_analytical_writing: float | None
    gpa: float | None
    comments: str
    full_info_url: str
    llm_generated_program: str | None
    llm_generated_university: str | None

    @classmethod
    def count(cls) -> int:
        """Count admission results in database.
        
        :returns: Total record count.
        :rtype: int
        :raises psycopg.Error: If query fails.
        """
        with postgres_manager.get_connection().cursor() as cur:
            query = sql.SQL("SELECT COUNT(*) FROM {};").format(
                sql.Identifier(get_table())
            )

            cur.execute(query)

            return cur.fetchone()[0]  # type: ignore


    @classmethod
    def execute_raw(cls, query: str, params: list) -> list[dict]:
        """Execute raw SQL query.
        
        :param query: SQL query string.
        :type query: str
        :param params: Query parameters.
        :type params: list
        :returns: Query results as dictionaries.
        :rtype: list[dict]
        :raises psycopg.Error: If query fails.
        """
        with postgres_manager.get_connection().cursor(row_factory=psycopg.rows.dict_row) as cur:
            return cur.execute(query, params).fetchall()

    @classmethod
    def get_latest_id(cls) -> int | None:
        """Get highest admission ID from database.
        
        :returns: Highest ID or None.
        :rtype: int | None
        :raises psycopg.Error: If query fails.
        """
        with postgres_manager.get_connection().cursor() as cur:
            query = sql.SQL("SELECT MAX(p_id) FROM {};").format(
                sql.Identifier(get_table()),
            )

            cur.execute(query)

            result = cur.fetchone()

            return result[0] if result else None


    @classmethod
    def from_soup(cls, table_row: list[Tag]) -> 'AdmissionResult':
        """Create AdmissionResult from HTML table rows.

        :param table_row: List of BeautifulSoup Tag objects.
        :type table_row: list[Tag]
        :returns: New instance with extracted data.
        :rtype: AdmissionResult
        :raises ValueError: If HTML elements missing or malformed.
        :raises AttributeError: If HTML structure unexpected.
        """
        table_columns = table_row[0] if len(table_row) > 0 else None
        tags = table_row[1] if len(table_row) > 1 else None
        comments_row = table_row[2] if len(table_row) > 2 else None

        tags = _tags_from_soup(
            set(map(lambda tag: tag.text.strip(), tags.find_all(class_="tw-inline-flex")))
            if tags
            else set[str]()
        )

        # Unpack table columns
        tds = table_columns.find_all("td")
        school = tds[0].text.strip() if len(tds) > 0 else ''
        program = tds[1].text.strip() if len(tds) > 1 else ''
        added_on = tds[2].text.strip() if len(tds) > 2 else ''
        decision = tds[3].text.strip() if len(tds) > 3 else ''

        added_on = datetime.strptime(added_on, "%B %d, %Y") if added_on else None

        # Do the best we can finding which year to use as the date for the decision.
        decision_year = (added_on.year if added_on else tags["year"]) or datetime.now().year

        decision_status, decision_date = _decision_from_soup(decision, decision_year)

        comments: str = comments_row.text.strip() if comments_row else ""

        # Program and degree type are separated by an SVG element, which manifests as a set of
        # newlines when BS extracts the text from it.
        program_name, degree_type, *_ = re.split(r"\n{2,}", program) + [None, None]
        degree_type = degree_type.lower()

        # Each entry should have a link to the full info page -- we grab that and use it to
        # find the entry's true ID value, which resides in the URL for it.
        full_info_anchor_element = table_columns.find("a", href=re.compile(r"^/result"))
        full_info_url = str(full_info_anchor_element["href"])

        # Here, hrefs should always be in the form `/result/{id}`
        id_match = re.search(r".+\/(?P<id>\d+)$", full_info_url)

        id: int = int(id_match.group("id"))

        return AdmissionResult(
            id=id,
            school=school,
            program_name=program_name,
            degree_type=degree_type,
            added_on=added_on,
            decision_status=decision_status,
            decision_date=decision_date,
            season=tags["season"],
            year=tags["year"],
            applicant_region=tags["applicant_region"],
            gre_general=tags["gre_general"],
            gre_verbal=tags["gre_verbal"],
            gre_analytical_writing=tags["gre_analytical_writing"],
            gpa=tags["gpa"],
            comments=comments,
            full_info_url=full_info_url,
            llm_generated_program=None,
            llm_generated_university=None,
        )

    @classmethod
    def from_dict(cls, plain: dict) -> 'AdmissionResult':
        """Create AdmissionResult from dictionary.

        :param plain: Dictionary with admission data.
        :type plain: dict
        :returns: New instance with converted datetime fields.
        :rtype: AdmissionResult
        """
        added_on = plain.get("added_on", None) or None
        if added_on:
            added_on = datetime.fromisoformat(added_on)

        decision_date = plain.get("decision_date", None) or None
        if decision_date:
            decision_date = datetime.fromisoformat(decision_date)

        values = dict(plain)
        values.update(
            added_on=added_on,
            decision_date=decision_date,
        )

        return AdmissionResult(**values)


    def save_to_db(self, cursor) -> None:
        """Save admission result to database using UPSERT.

        :param cursor: Database cursor.
        :raises psycopg.Error: If database operation fails.
        """
        cursor.execute(sql.SQL("""
            INSERT INTO {} (
                p_id, school, program_name, program, comments, date_added, url,
                status, decision_date, season, year, term, us_or_international,
                gpa, gre, gre_v, gre_aw, degree,
                llm_generated_program, llm_generated_university
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s,%s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (p_id) DO UPDATE SET
                school = EXCLUDED.school,
                program_name = EXCLUDED.program_name,
                comments = EXCLUDED.comments,
                date_added = EXCLUDED.date_added,
                url = EXCLUDED.url,
                status = EXCLUDED.status,
                decision_date = EXCLUDED.decision_date,
                season = EXCLUDED.season,
                year = EXCLUDED.year,
                term = EXCLUDED.term,
                us_or_international = EXCLUDED.us_or_international,
                gpa = EXCLUDED.gpa,
                gre = EXCLUDED.gre,
                gre_v = EXCLUDED.gre_v,
                gre_aw = EXCLUDED.gre_aw,
                degree = EXCLUDED.degree,
                llm_generated_program = EXCLUDED.llm_generated_program,
                llm_generated_university = EXCLUDED.llm_generated_university;
        """).format(
            sql.Identifier(get_table())
        ), (
            self.id,
            self.school,
            self.program_name,
            # Redundant but the assignment calls for it
            f"{self.school} {self.program_name}",
            self.comments,
            self.added_on,
            self.full_info_url,
            self.decision_status,
            self.decision_date,
            self.season,
            self.year,
            # Redundant but the assignment calls for it
            f"{self.season} {self.year}",
            self.applicant_region,
            self.gpa,
            self.gre_general,
            self.gre_verbal,
            self.gre_analytical_writing,
            self.degree_type,
            self.llm_generated_program,
            self.llm_generated_university,
        ))

    def clean_and_augment(self) -> None:
        """Apply LLM-based data cleaning.

        :raises Exception: If LLM processing fails.
        """
        program_and_school = f"{self.program_name}, {self.school}"

        print(f"Running cleaner on entry {self.id}: {program_and_school}")

        result = clean.call_llm(program_and_school)

        print(f"Got cleaned fields: {result}")

        self.llm_generated_program = result["standardized_program"]
        self.llm_generated_university = result["standardized_university"]


