"""Data models and database interaction for TheGradCafe scraper.

The `AdmissionResult` class serves as the primary model for an admissions record.
"""

import psycopg
import psycopg.rows
import atexit
import re
import json
from datetime import datetime
from dataclasses import asdict, dataclass, is_dataclass
from enum import Enum

from bs4.element import Tag

from llm_hosting.app import _call_llm


# Global connection object to the PostgreSQL database.
conn = psycopg.connect(
    dbname="admissions",
    user="student",
    password="modernsoftwareconcepts",
    host="localhost",
    port=5432,
)


def init_tables(recreate=False):
    """Initialize the postgres tables for storing the admissions scrape data."""
    with conn.cursor() as cur:
        if recreate:
            print("Dropping tables and recreating...")

            cur.execute("""
                DROP TABLE IF EXISTS admissions_info;
            """)

            conn.commit()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS admissions_info (
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
        """)

        conn.commit()


class ApplicantRegion(Enum):
    """Enumeration for the geographical region of an applicant."""

    INTERNATIONAL = "international"
    AMERICAN = "american"


class SchoolSeason(Enum):
    """Enumeration for the term season."""

    FALL = "fall"
    SPRING = "spring"


def _tags_from_soup(tags: set[str]):
    """Unpacks a set of tag values from a admission result entry.

    Parses a set of string tags from the HTML and extracts structured information
    like application year, season, region, and test scores.
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

        if tag in [r.value for r in ApplicantRegion]:
            expanded["applicant_region"] = ApplicantRegion(tag)
            continue

        # -------- Process term --------

        term_match = re.match(r"(?P<season>[a-z]+)\s*?(?P<year>\d{4}|\d{2})", tag)
        if term_match:
            season = term_match.group("season")

            for season_category in SchoolSeason:
                if season_category.value.startswith(season):
                    expanded["season"] = SchoolSeason(season)
                    break

            year = term_match.group("year")

            year = ("20" + year)[-4:]
            expanded["year"] = int(year)

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

    return expanded


class DecisionStatus(Enum):
    """Enumeration for the status of an application decision."""

    ACCEPTED = "accepted"
    INTERVIEW_PENDING = "interview"
    WAIT_LISTED = "wait_listed"
    REJECTED = "rejected"  # :'(
    OTHER = "other"


def _decision_from_soup(decision_str: str, added_on_year: int):
    """Parse a decision string and returns the status and date."""
    match = re.match(
        r"(?P<status>[A-Za-z\s]+?)\s+on\s+(?P<date_str>[0-9]+\s+[A-Za-z]+)$",
        decision_str,
    )

    if not match:
        print(f"Failed to parse decision: {decision_str}")
        return None, None

    status = DecisionStatus(match.group("status").lower().replace(" ", "_"))
    date_part = match.group("date_str")
    
    # Try to parse with the date it was added with
    try:
        parsed_date = datetime.strptime(f"{date_part} {added_on_year}", "%d %b %Y")
    except ValueError:
        print(f"Failed to parse date string: {date_part}")
        return status, None

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


class DegreeType(Enum):
    """Enumeration for the type of degree an applicant is seeking."""

    MASTERS = "masters"
    PHD = "phd"
    EDD = "edd"
    PSYD = "psyd"
    MFA = "mfa"
    MBA = "mba"
    JD = "jd"
    OTHER = "other"


def _build_where_clause(where={}):
    """Given a set of key/value pairs, builds a WHERE clause for a SQL query."""
    params = []
    columns = []

    for key, value in where.items():
        if value is not None:
            columns.append(f"{key}=%s")
            params.append(value)

    if columns:
        return f"\nWHERE {' AND '.join(columns)}", params

    return "", []


@dataclass
class AdmissionResult:
    """Represents a single entry from TheGradCafe."""

    id: int
    school: str
    program_name: str | None
    degree_type: DegreeType | None
    added_on: datetime | None
    decision_status: DecisionStatus | None
    decision_date: datetime | None
    season: SchoolSeason | None
    year: int | None
    applicant_region: ApplicantRegion | None
    gre_general: int | None
    gre_verbal: int | None
    gre_analytical_writing: float | None
    gpa: float | None
    comments: str
    full_info_url: str
    llm_generated_program: str | None
    llm_generated_university: str | None

    @classmethod
    def count(cls, where={}):
        """Return the count of all admission results in the database."""
        where_clause, params = _build_where_clause(where)

        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT COUNT(*) from admissions_info {where_clause};
            """,
                params,
            )

            return cur.fetchone()[0]  # type: ignore

    @classmethod
    def fetch(cls, offset=0, limit=10, where={}):
        """Fetch a paginated list of admission results from the database."""
        where_clause, params = _build_where_clause(where)

        params.extend([offset, limit])

        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT * from admissions_info
                {where_clause}
                OFFSET %s
                LIMIT %s;
            """,
                params,
            )

            return {
                "rows": [cls._from_db_row(r) for r in cur.fetchall()],
                "total": cls.count(where),
            }


    @classmethod
    def execute_raw(cls, query, params):
        """Execute a raw SQL query and returns the results as a list of dictionaries."""
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            return cur.execute(query, params).fetchall()
        
    @classmethod
    def get_latest_id(cls):
        """Retrieve the highest existing admission ID from the database."""
        with conn.cursor() as cur:
            cur.execute("""
                SELECT MAX(p_id) FROM admissions_info;
            """)

            result = cur.fetchone()

            if result:
                return result[0]

            return 0

    @classmethod
    def _from_db_row(cls, row):
        """Construct an AdmissionResult object from a database row."""
        (
            id,
            school,
            program_name,
            _program,
            comments,
            added_on,
            full_info_url,
            decision_status,
            decision_date,
            season,
            year,
            _term,
            applicant_region,
            gpa,
            gre_general,
            gre_verbal,
            gre_analytical_writing,
            degree_type,
            llm_generated_program,
            llm_generated_university,
        ) = row

        # Wrap strings into enums
        decision_status = DecisionStatus(decision_status) if decision_status else None
        applicant_region = ApplicantRegion(applicant_region) if applicant_region else None
        degree_type = DegreeType(degree_type) if degree_type else None
        season = SchoolSeason(season) if season else None

        return AdmissionResult(
            id=id,
            school=school,
            program_name=program_name,
            degree_type=degree_type,
            added_on=added_on,
            decision_status=decision_status,
            decision_date=decision_date,
            season=season,
            year=year,
            applicant_region=applicant_region,
            gre_general=gre_general,
            gre_verbal=gre_verbal,
            gre_analytical_writing=gre_analytical_writing,
            gpa=gpa,
            comments=comments,
            full_info_url=full_info_url,
            llm_generated_program=llm_generated_program,
            llm_generated_university=llm_generated_university,
        )

    @classmethod
    def from_soup(cls, table_row: list[Tag]):
        """Create an AdmissionResult instance from a table row, scraped through BS4.

        This method parses a list of BeautifulSoup `Tag` objects that represent a
        single admission entry in the HTML table and constructs an `AdmissionResult`
        dataclass instance from it.
        """
        table_columns, tags, comments_row, *_ = table_row + [None, None, None]

        # We need at least one element or something is wrong
        assert isinstance(table_columns, Tag)

        tags = _tags_from_soup(
            set(map(lambda tag: tag.text.strip(), tags.find_all(class_="tw-inline-flex")))
            if tags
            else set[str]()
        )

        # Unpack table columns
        school, program, added_on, decision, *_ = map(
            lambda column: column.text.strip(), table_columns.find_all("td")
        )

        added_on = datetime.strptime(added_on, "%B %d, %Y") if added_on else None

        # Process decision values from the appropriate table column.
        try:
            # Do the best we can finding which year to use as the date for the decision.
            decision_year = (added_on.year if added_on else tags["year"]) or datetime.now().year

            decision_status, decision_date = _decision_from_soup(decision, decision_year)
        except ValueError:
            # Sometimes these are missing or have invalid formatting, so we None this field.
            print(f"Failed to process decision: {decision}... skipping")
            decision_status, decision_date = None, None

        comments: str = comments_row.text.strip() if comments_row else ""

        # Program and degree type are separated by an SVG element, which manifests as a set of
        # newlines when BS extracts the text from it.
        program_name, degree_type, *_ = re.split(r"\n{2,}", program) + [None, None]

        if not isinstance(program_name, str):
            program_name = None

        try:
            if not degree_type:
                degree_type = None
            else:
                degree_type = DegreeType(degree_type.lower())
        except ValueError:
            print(f"Failed to process degree type: {degree_type}... skipping")
            degree_type = None

        # Each entry should have a link to the full info page -- we grab that and use it to
        # find the entry's true ID value, which resides in the URL for it.
        full_info_anchor_element = table_columns.find("a", href=re.compile(r"^/result"))
        if not isinstance(full_info_anchor_element, Tag):
            raise RuntimeError("Failed to find result anchor")

        full_info_url = str(full_info_anchor_element["href"])

        # Here, hrefs should always be in the form `/result/{id}`
        id_match = re.search(r".+\/(?P<id>\d+)$", full_info_url)
        if id_match is None:
            raise RuntimeError("anchor href for admission result is unrecognized")

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
    def from_dict(cls, plain: dict):
        """Deserialize an AdmissionResult instance from a JSON-friendly dictionary."""
        degree_type = plain["degree_type"] and DegreeType(plain["degree_type"])

        added_on = plain.get("added_on", None) or None
        if added_on:
            added_on = datetime.fromisoformat(added_on)

        decision_date = plain.get("decision_date", None) or None
        if decision_date:
            decision_date = datetime.fromisoformat(decision_date)

        values = dict(plain)
        values.update(
            degree_type=degree_type,
            added_on=added_on,
            decision_date=decision_date,
        )

        return AdmissionResult(**values)

    @classmethod
    def from_plaintext_rows(cls, filename: str):
        """Load the cleaned admissions data from the given filename.

        The file is expected to contain one JSON object per line.
        """
        with open(filename, "r") as f:
            lines = f.readlines()
            dicts = map(lambda entry: json.loads(entry), lines)
            return map(AdmissionResult.from_dict, dicts)

    def to_json(self):
        """Serialize the AdmissionResult object to a JSON string."""
        return json.dumps(self, default=_json_encoder, indent=2)

    def save_to_db(self):
        """Save the AdmissionResult instance to the database."""
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO admissions_info (
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
                """,
                    (
                        self.id,
                        self.school,
                        self.program_name,
                        # Redundant but the assignment calls for it
                        f"{self.school} {self.program_name}",
                        self.comments,
                        self.added_on,
                        self.full_info_url,
                        self.decision_status.value if self.decision_status else None,
                        self.decision_date,
                        self.season.value if self.season else None,
                        self.year,
                        # Redundant but the assignment calls for it
                        f"{self.season} {self.year}",
                        self.applicant_region.value if self.applicant_region else None,
                        self.gpa,
                        self.gre_general,
                        self.gre_verbal,
                        self.gre_analytical_writing,
                        self.degree_type.value if self.degree_type else None,
                        self.llm_generated_program,
                        self.llm_generated_university,
                    ),
                )

            conn.commit()
        except Exception as e:
            print(f"Failed to save entry with id {self.id}")
            raise e
        
    def clean_and_augment(self):
        """Process the school and program and apply cleaned fields."""
        program_and_school = f"{self.program_name}, {self.school}"

        print(f"Running cleaner on entry {self.id}: {program_and_school}")

        result = _call_llm(program_and_school)

        print(f"Got cleaned fields: {result}")

        self.llm_generated_program = result["standardized_program"]
        self.llm_generated_university = result["standardized_university"]


def _json_encoder(obj):
    """Serialize the types in this module to a JSON-friendly format."""
    if isinstance(obj, Enum):
        return obj.value

    elif isinstance(obj, set):
        return sorted(list(obj))

    elif isinstance(obj, datetime):
        return obj.isoformat()

    elif is_dataclass(obj):
        return asdict(obj)  # type: ignore

    raise TypeError(f"Cannot serialize object of type {type(obj)}")


@atexit.register
def gracefully_close():
    """Close the database connection when the program exits."""
    if conn:
        conn.close()
