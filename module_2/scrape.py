import re
import json
import argparse
from time import sleep
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
    year: str | None
    school_region: SchoolRegion | None
    gre_general: int | None
    gre_verbal: int | None
    gre_analytical_writing: float | None
    gpa: float | None

    @classmethod
    def from_soup(cls, tags: set[str]):
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
            # -------- Process region --------

            if tag in SchoolRegion:
                expanded["school_region"] = SchoolRegion(tag)
                continue

            # -------- Process term --------

            term_match = re.match(r"(?P<season>[A-Za-z])\s*?(?P<year>\d{2}|\d{4})", tag)
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
                r"(?P<test>GPA|GRE(?:\s+V|\s+AW)?)\s+(?P<score>[\d\.]+)$", tag
            )
            if grade_match:
                test: str = grade_match.group("test").lower()
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
    def from_soup(cls, decision_str: str):
        match = re.match(
            r"(?P<status>[A-Za-z\s]+?)\s+on\s+(?P<date_str>[0-9A-Za-z\s]+)$",
            decision_str,
        )
        if not match:
            raise ValueError("Could not parse decision string from soup")

        status = DecisionStatus(match.group("status").lower().replace(" ", "_"))
        date = datetime.strptime(match.group("date_str"), "%d %b")

        return Decision(status=status, date=date)


class DegreeType(Enum):
    MASTERS = "masters"
    PHD = "phd"
    EDD = "edd"
    PSYD = "psyd"
    MFA = "mfa"
    MBA = "mba"
    OTHER = "other"


@dataclass
class AdmissionResult:
    id: str
    school: str
    program_name: str | None
    degree_type: DegreeType | None
    added_on: datetime | None
    decision: Decision
    tags: Tags
    comments: str
    full_info_url: str

    @classmethod
    def from_soup(cls, table_row: list[Tag]):
        table_columns, tags, comments_row, *_ = table_row + [None, None]
        assert isinstance(
            table_columns, Tag
        )  # We need at least one tag or else something is wrong

        school, program, added_on, decision, *_ = map(
            lambda column: column.text.strip(), table_columns.find_all("td")
        )

        added_on = datetime.strptime(added_on, "%B %d, %Y") if added_on else None

        decision = Decision.from_soup(decision)

        tags = Tags.from_soup(
            set(
                map(
                    lambda tag: tag.text.strip(), tags.find_all(class_="tw-inline-flex")
                )
            )
            if tags
            else set[str]()
        )

        comments: str = comments_row.text.strip() if comments_row else ""

        program_name, degree_type, *_ = re.split(r"\n{2,}", program) + [None, None]
        if not isinstance(program_name, str):
            program_name = None

        degree_type = (
            DegreeType(degree_type.lower()) if isinstance(degree_type, str) else None
        )

        full_info_anchor_element = table_columns.find("a", href=re.compile(r"^/result"))
        if not isinstance(full_info_anchor_element, Tag):
            raise RuntimeError("Failed to find result anchor")

        full_info_url = str(full_info_anchor_element["href"])

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


def check_robots_permission(url: ParsedURL, user_agent: str) -> bool:
    robots_file_parser = RobotFileParser()

    robots_file_parser.set_url(f"https://{url.hostname}/robots.txt")
    robots_file_parser.read()

    return robots_file_parser.can_fetch(user_agent, str(url))


def get_table_rows(soup: BeautifulSoup):
    h1 = soup.find("h1")
    tbody = h1 and h1.find_next("tbody")

    assert isinstance(tbody, Tag)

    rows = [child for child in tbody.children if isinstance(child, Tag)]

    split_indices = [
        index
        for (index, row) in enumerate(rows)
        if not row.find("td", attrs={"colspan": True})
    ]

    return [rows[i:j] for i, j in pairwise(split_indices)]


def scrape_page(page: int):
    assert page > 0

    user_agent = "WesBot/1.0"
    url = urlparse("https://www.thegradcafe.com/survey/?page=" + str(page))
    request = Request(url.geturl(), headers={"User-Agent": user_agent})

    if not check_robots_permission(url, user_agent):
        raise Exception(
            f"robots.txt permission check failed with user agent [{user_agent}] and url: [{str(url)}]"
        )

    with urlopen(request) as response:
        html = response.read().decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")

        admission_results: list[AdmissionResult] = [
            AdmissionResult.from_soup(row) for row in get_table_rows(soup)
        ]

        page_links = [
            int(str(anchor["href"]).split("=")[1])
            for anchor in soup.find_all("a", href=re.compile(r".*\?page=\d+$"))
            if isinstance(anchor, Tag)
        ]

        return admission_results, bool(page_links) and max(page_links) > page


def json_encoder(obj):
    if isinstance(obj, Enum):
        return obj.value

    elif isinstance(obj, datetime):
        return obj.isoformat()

    elif is_dataclass(obj):
        return asdict(obj)  # type: ignore

    raise TypeError(f"Cannot serialize object of type {type(obj)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scraper for TheGradCafe.")
    parser.add_argument(
        "--out",
        type=str,
        required=False,
        help="The output filename to save results to.",
        default="results.json",
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

    pages_crawled = 0
    more_pages = True

    admission_results: list[AdmissionResult] = []

    while more_pages and not (args.limit and pages_crawled < args.limit):
        page_number = args.page + pages_crawled
        print(f"Scraping page #{page_number}")

        page_results, more_pages = scrape_page(page_number)
        admission_results.extend(page_results)

        print(f"Success... found {len(page_results)} items; total = {len(admission_results)}")

        pages_crawled += 1

        sleep(0.5) # Be polite

    print(f"Got {len(admission_results)} results")

    with open(args.out, "w") as out_file:
        json.dump(admission_results, out_file, default=json_encoder, indent=2)
        print(f"Saved results to '{args.out}'")
