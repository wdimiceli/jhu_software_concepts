"""A web scraper for TheGradCafe.com, designed to extract and parse admissions data.

This module provides functions to crawl the "Admissions Results" section of TheGradCafe.com.

The main components:

- `scrape_data`: The primary function that orchestrates the scraping process.
- `scrape_page`: A helper function that handles the scraping of a single page.
"""

import re
import urllib3
from itertools import pairwise
from urllib.parse import ParseResult as ParsedURL
from urllib.parse import urlparse
import urllib.robotparser

from bs4 import BeautifulSoup
from bs4.element import Tag
from model import AdmissionResult


def _check_robots_permission(url: ParsedURL, user_agent: str) -> bool:
    """Check that the given user agent has permission to crawl the URL."""
    robots_file_parser = urllib.robotparser.RobotFileParser()

    robots_file_parser.set_url(f"https://{url.hostname}/robots.txt")
    robots_file_parser.read()

    return robots_file_parser.can_fetch(user_agent, str(url))


def _get_table_rows(soup: BeautifulSoup):
    """Parse HTML soup and return a list of table entries corresponding to admission results."""
    # Skip down to the first h1, which gets us roughly over the target.
    h1 = soup.find("h1")
    tbody = h1 and h1.find_next("tbody")

    assert isinstance(tbody, Tag)

    # Collect up the table rows.
    rows = [child for child in tbody.children if isinstance(child, Tag)]

    # Each admission result consumes 1 or more table rows in the HTML.
    # Here we group them
    split_indices = [
        index for (index, row) in enumerate(rows) if not row.find("td", attrs={"colspan": True})
    ]

    return [rows[i:j] for i, j in pairwise(split_indices)]


def scrape_page(page: int):
    """Scrape a single page on TheGradCafe.com."""
    assert page > 0  # Sanity check

    user_agent = "WesBot/1.0"
    # Construct the URL for the specific page
    url = urlparse("https://www.thegradcafe.com/survey/?page=" + str(page))

    # Check to ensure we have permission before continuing.
    if not _check_robots_permission(url, user_agent):
        raise Exception(
            f"robots.txt permission check failed with user agent [{user_agent}] and url: [{url!s}]",
        )

    # Get the HTML response and process it with BS.
    http = urllib3.PoolManager()
    response = http.request(
        "GET",
        url.geturl(),
        headers={"User-Agent": user_agent},
    )
    html = response.data.decode("utf-8")
    soup = BeautifulSoup(html, "html.parser")

    # Parse each group of rows into an AdmissionResult object
    admission_results: list[AdmissionResult] = []

    for row in _get_table_rows(soup):
        try:
            admission_results.append(AdmissionResult.from_soup(row) )
        except Exception as e:
            print("Error parsing row:", e)

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


def scrape_data(page: int, limit: int | None = None, stop_at_id: int | None = None):
    """Scrape iteratively from TheGradCafe, starting with the given page, up to the maximum."""
    pages_crawled = 0
    more_pages = True

    admission_results: list[AdmissionResult] = []

    try:
        # Start with the first page and iterate up to the limit or no more pages.
        while more_pages and not (limit and len(admission_results) >= limit):
            page_number = page + pages_crawled

            print(f"Scraping page #{page_number}")

            page_results, more_pages = scrape_page(page_number)

            print(f"Success... found {len(page_results)} items")

            pages_crawled += 1

            if stop_at_id in [entry.id for entry in page_results]:
                print(f"Found id {stop_at_id} in results, stopping...")
                page_results = filter(lambda result: result.id > stop_at_id, page_results)
                more_pages = False

            admission_results.extend(page_results)

        print(f"Got {len(admission_results)} results")
    except Exception as e:
        # Stop the crawl here, report the error, and return what we have.
        print("Error during scrape: ", e)

    return admission_results
