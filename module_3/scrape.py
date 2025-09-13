import re
import json
import argparse
from datetime import datetime
from dataclasses import dataclass, asdict, is_dataclass
from enum import Enum
from itertools import pairwise

from bs4 import BeautifulSoup
from bs4.element import Tag
from urllib.request import urlopen, Request
from urllib.parse import urlparse, ParseResult as ParsedURL
from urllib.robotparser import RobotFileParser


class SchoolRegion(Enum):
    INTERNATIONAL = "international"
    AMERICAN = "american"


class SchoolSeason(Enum):
    FALL = "fall"
    SPRING = "spring"


@dataclass
class Tags:
    season: SchoolSeason | None
    year: int | None
    school_region: SchoolRegion | None
    gre_general: int | None
    gre_verbal: int | None
    gre_analytical_writing: float | None
    gpa: float | None

    @classmethod
    def _from_soup(cls, tags: set[str]):
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

        return Tags(**expanded)


class DecisionStatus(Enum):
    ACCEPTED = "accepted"
    INTERVIEW_PENDING = "interview"
    WAIT_LISTED = "wait_listed"
    REJECTED = "rejected"  # :'(
    OTHER = "other"


@dataclass
class Decision:
    status: DecisionStatus
    date: datetime

    @classmethod
    def _from_soup(cls, decision_str: str, year: int):
        match = re.match(
            r"(?P<status>[A-Za-z\s]+?)\s+on\s+(?P<date_str>[0-9A-Za-z\s]+)$",
            decision_str,
        )
        if not match:
            print(f"Failed to parse decision: {decision_str}")
            return None

        status = DecisionStatus(match.group("status").lower().replace(" ", "_"))

        full_date = match.group("date_str") + f", {year}"
        date = datetime.strptime(full_date, "%d %b, %Y")

        return Decision(status=status, date=date)


class DegreeType(Enum):
    MASTERS = "masters"
    PHD = "phd"
    EDD = "edd"
    PSYD = "psyd"
    MFA = "mfa"
    MBA = "mba"
    JD = "jd"
    OTHER = "other"


@dataclass
class AdmissionResult:
    """Represents a single entry from TheGradCafe."""
    id: str
    school: str
    program_name: str | None
    degree_type: DegreeType | None
    added_on: datetime | None
    decision: Decision | None
    tags: Tags
    comments: str
    full_info_url: str

    @classmethod
    def _from_soup(cls, table_row: list[Tag]):
        """Creates an AdmissionResult instance from a table row, scraped through BS4."""
        table_columns, tags, comments_row, *_ = table_row + [None, None, None]

        assert isinstance(table_columns, Tag)  # We need at least one element or something is wrong

        tags = Tags._from_soup(
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
            decision_year = tags.year or (
                added_on.year if added_on else datetime.now().year
            )
            decision = Decision._from_soup(decision, decision_year)
        except ValueError:
            # Sometimes these are missing or have invalid formatting, so we None this field.
            print(f"Failed to process decision: {decision}... skipping")
            decision = None

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
            decision=decision,
            tags=tags,
            comments=comments,
            full_info_url=full_info_url,
        )
    
    @classmethod
    def from_json(cls, json: dict):
        """Deserializes an AdmissionResult instance from JSON."""
        degree_type = json["degree_type"] and DegreeType(json["degree_type"])

        added_on = json["added_on"] and datetime.fromisoformat(json["added_on"])

        decision = json["decision"] and Decision(
            status=json["decision"]["status"],
            date=datetime.fromisoformat(json["decision"]["date"]),
        )

        tags = Tags(**json["tags"])

        values = dict(json)
        values.update(
            degree_type=degree_type,
            added_on=added_on,
            decision=decision,
            tags=tags,
        )

        return AdmissionResult(**values)

    def to_json(self):
        return asdict(self)


def _check_robots_permission(url: ParsedURL, user_agent: str) -> bool:
    """Checks that the given user agent has permission to crawl the URL."""
    robots_file_parser = RobotFileParser()

    robots_file_parser.set_url(f"https://{url.hostname}/robots.txt")
    robots_file_parser.read()

    return robots_file_parser.can_fetch(user_agent, str(url))


def _get_table_rows(soup: BeautifulSoup):
    """Parses the HTML soup and returns a list of table entries corresponding to admission results."""
    # Skip down to the first h1, which gets us roughly over the target.
    h1 = soup.find("h1")
    tbody = h1 and h1.find_next("tbody")

    assert isinstance(tbody, Tag)

    # Collect up the table rows.
    rows = [child for child in tbody.children if isinstance(child, Tag)]

    # Each admission result consumes 1 or more table rows in the HTML.
    # Here we group them
    split_indices = [
        index
        for (index, row) in enumerate(rows)
        if not row.find("td", attrs={"colspan": True})
    ]

    return [rows[i:j] for i, j in pairwise(split_indices)]


def scrape_page(page: int):
    """Scrapes a single page on TheGradCafe.com"""
    assert page > 0  # Sanity check

    user_agent = "WesBot/1.0"
    url = urlparse("https://www.thegradcafe.com/survey/?page=" + str(page))
    request = Request(url.geturl(), headers={"User-Agent": user_agent})

    # Check to ensure we have permission before continuing.
    if not _check_robots_permission(url, user_agent):
        raise Exception(
            f"robots.txt permission check failed with user agent [{user_agent}] and url: [{str(url)}]"
        )

    # Get the HTML response and process it with BS.
    with urlopen(request) as response:
        html = response.read().decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")

        admission_results: list[AdmissionResult] = [
            AdmissionResult._from_soup(row) for row in _get_table_rows(soup)
        ]

        # Get all the anchor tags that point to other pages and parse out the page number.
        page_links = [
            int(str(anchor["href"]).split("=")[1])
            # Finds <a/> elements with href="?page=123"
            for anchor in soup.find_all("a", href=re.compile(r".*\?page=\d+$"))
            if isinstance(anchor, Tag)
        ]

        # If we have links and one of them is a higher page number, then we have more to parse.
        has_more_pages = bool(page_links) and max(page_links) > page

        return admission_results, has_more_pages


def scrape_data(page: int, limit: int):
    """Iteratively scrapes data from TheGradCafe, starting with the given page, up to the maximum"""
    pages_crawled = 0
    more_pages = True

    admission_results: list[AdmissionResult] = []

    try:
        # Start with the first page and iterate up to the limit or no more pages.
        while more_pages and not (limit and pages_crawled >= limit):
            page_number = page + pages_crawled

            print(f"Scraping page #{page_number}")

            page_results, more_pages = scrape_page(page_number)
            admission_results.extend(page_results)

            print(f"Success... found {len(page_results)} items; total = {len(admission_results)}")

            pages_crawled += 1

        print(f"Got {len(admission_results)} results")
    except Exception as e:
        # Stop the crawl here, report the error, and return what we have.
        print("Error during scrape: ", e)

    return admission_results


def generate_admissions_metadata(admission_results: list[AdmissionResult]):
    """Computes a set of metadata about the scrape data, giving totals and de-duped values."""
    schools = set(map(lambda result: result.school, admission_results))
    programs = set(map(lambda result: result.program_name, admission_results))

    return {
        "total": len(admission_results),
        "schools": schools,
        "programs": programs,
    }


def _json_encoder(obj):
    """Cleanly serializes the types in this module to a JSON-friendly format."""
    if isinstance(obj, Enum):
        return obj.value
    
    elif isinstance(obj, set):
        return sorted(list(obj))

    elif isinstance(obj, datetime):
        return obj.isoformat()

    elif hasattr(obj, "to_json"):
        return obj.to_json()

    elif is_dataclass(obj):
        return asdict(obj)  # type: ignore

    raise TypeError(f"Cannot serialize object of type {type(obj)}")


def save_scrape_results(data: list[AdmissionResult] | dict, filename: str):
    """Saves the scrape results as JSON into the given filename."""
    with open(filename, "w") as out_file:
        json.dump(data, out_file, default=_json_encoder, indent=2)
        print(f"Saved results to '{filename}'")


def load_scrape_results(filename: str) -> list[AdmissionResult]:
    """Loads the scrape data from the given filename and deserializes it."""
    with open(filename, "r") as f:
        serialized = json.load(f)
        return list(map(AdmissionResult.from_json, serialized))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scraper for TheGradCafe.")

    parser.add_argument(
        "--out",
        type=str,
        required=False,
        help="The output filename to save results to.",
        default="applicant_data.json",
    )

    parser.add_argument(
        "--page",
        type=int,
        required=False,
        help="The page on which start crawling.",
        default=1,
    )

    parser.add_argument(
        "--limit",
        type=int,
        required=False,
        help="The maximum number of pages to crawl.",
    )

    args = parser.parse_args()

    admission_results = scrape_data(args.page, args.limit)
    save_scrape_results(admission_results, args.out)
