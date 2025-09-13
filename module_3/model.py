import psycopg
import psycopg.rows
import atexit
import re
import json
from datetime import datetime
from dataclasses import asdict, dataclass, is_dataclass
from enum import Enum

from bs4.element import Tag


conn = psycopg.connect(
    dbname="admissions",
    user="student",
    password="modernsoftwareconcepts",
    host="localhost",
    port=5432
)


def init_tables(recreate = False):
    """Initializes the postgres tables for storing the admissions scrape data."""
    with conn.cursor() as cur:
        if recreate:
            print("Dropping tables and recreating...")

            cur.execute("""
                DROP TABLE IF EXISTS admissions_info;
            """)

            conn.commit()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS admissions_info (
                p_id SERIAL PRIMARY KEY,
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


class SchoolRegion(Enum):
    INTERNATIONAL = "international"
    AMERICAN = "american"


class SchoolSeason(Enum):
    FALL = "fall"
    SPRING = "spring"


def _tags_from_soup(tags: set[str]):
    """Unpacks a set of tag values from a admission result entry."""
    expanded = {
        "season": None,
        "year": None,
        "school_region": False,
        "gre_general": None,
        "gre_verbal": None,
        "gre_analytical_writing": None,
        "gpa": None,
    }

    for tag in tags:
        tag = tag.lower()

        # -------- Process region --------

        if tag in SchoolRegion:
            expanded["school_region"] = SchoolRegion(tag)
            continue

        # -------- Process term --------

        term_match = re.match(r"(?P<season>[a-z]+)\s*?(?P<year>\d{4}|\d{2})", tag)
        if term_match:
            season = term_match.group("season")

            for season_category in SchoolSeason:
                if season_category.value.startswith(season):
                    expanded["season"] = season
                    break

            year = term_match.group("year")

            year = ("20" + year)[-4:]
            expanded["year"] = int(year)

            continue

        # -------- Process grades --------

        grade_match = re.match(
            r"(?P<test>gpa|gre(?:\s+v|\s+aw)?)\s+(?P<score>[\d\.]+)$", tag
        )
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
    ACCEPTED = "accepted"
    INTERVIEW_PENDING = "interview"
    WAIT_LISTED = "wait_listed"
    REJECTED = "rejected"  # :'(
    OTHER = "other"


def _decision_from_soup(decision_str: str, year: int):
    match = re.match(
        r"(?P<status>[A-Za-z\s]+?)\s+on\s+(?P<date_str>[0-9A-Za-z\s]+)$",
        decision_str,
    )
    if not match:
        print(f"Failed to parse decision: {decision_str}")
        return None, None

    status = DecisionStatus(match.group("status").lower().replace(" ", "_"))

    full_date = match.group("date_str") + f", {year}"
    date = datetime.strptime(full_date, "%d %b, %Y")

    return status, date


class DegreeType(Enum):
    MASTERS = "masters"
    PHD = "phd"
    EDD = "edd"
    PSYD = "psyd"
    MFA = "mfa"
    MBA = "mba"
    JD = "jd"
    OTHER = "other"


def _build_where_clause(where={}):
    params = []
    columns = []

    for key, value in where.items():
        if value is not None:
            columns.append(f"{key}=%s")
            params.append(value)

    if columns:
        return f"\nWHERE {" AND ".join(columns)}", params
    
    return "", []

@dataclass
class AdmissionResult:
    """Represents a single entry from TheGradCafe."""
    id: str
    school: str
    program_name: str | None
    degree_type: DegreeType | None
    added_on: datetime | None
    decision_status: DecisionStatus | None
    decision_date: datetime | None
    season: SchoolSeason | None
    year: int | None
    school_region: SchoolRegion | None
    gre_general: int | None
    gre_verbal: int | None
    gre_analytical_writing: float | None
    gpa: float | None
    comments: str
    full_info_url: str
    llm_generated_program: str | None
    llm_generated_university: str | None

    @classmethod
    def count(cls, where = {}):
        """Returns the count of all admission results in the database."""
        where_clause, params = _build_where_clause(where)

        with conn.cursor() as cur:
            cur.execute(f"""
                SELECT COUNT(*) from admissions_info {where_clause};
            """,
            params)

            return cur.fetchone()[0] # type: ignore
        
    @classmethod
    def fetch(cls, offset = 0, limit = 10, where = {}):
        where_clause, params = _build_where_clause(where)

        params.extend([offset, limit])

        with conn.cursor() as cur:
            cur.execute(f"""
                SELECT * from admissions_info
                {where_clause}
                OFFSET %s
                LIMIT %s;
            """, params)

            return {
                "rows": map(cls._from_db_row, cur.fetchall()),
                "total": cls.count(where)
            }

    @classmethod
    def _from_db_row(cls, row):
        (id,
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
        school_region,
        gpa,
        gre_general,
        gre_verbal,
        gre_analytical_writing,
        degree_type,
        llm_generated_program,
        llm_generated_university) = row

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
            school_region=school_region,
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
        """Creates an AdmissionResult instance from a table row, scraped through BS4."""
        table_columns, tags, comments_row, *_ = table_row + [None, None, None]

        assert isinstance(table_columns, Tag)  # We need at least one element or something is wrong

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
            decision_year = tags["year"] or (
                added_on.year if added_on else datetime.now().year
            )

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

        id: str = id_match.group("id")

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
            school_region=tags["school_region"],
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
        """Deserializes an AdmissionResult instance from JSON."""
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
        """Loads the cleaned admissions data from the given filename."""
        with open(filename, "r") as f:
            lines = f.readlines()
            dicts = map(lambda entry: json.loads(entry), lines)
            return map(AdmissionResult.from_dict, dicts)

    def to_json(self):
        return json.dumps(self, default=_json_encoder, indent=2)
    
    def save_to_db(self):
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
                        program = EXCLUDED.program,
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
                        self.decision_status,
                        self.decision_date,
                        self.season,
                        self.year,

                        # Redundant but the assignment calls for it
                        f"{self.season} {self.year}",

                        self.school_region,
                        self.gpa,
                        self.gre_general,
                        self.gre_verbal,
                        self.gre_analytical_writing,
                        self.degree_type,
                        self.llm_generated_program,
                        self.llm_generated_university,
                    ),
                )
        except Exception as e:
            print(f"Failed to save entry with id {self.id}")
            raise e


def _json_encoder(obj):
    """Cleanly serializes the types in this module to a JSON-friendly format."""
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
    if conn:
        conn.close()
