# Module 2: Web Scraper

<small>Course: EN.605.256.8VL.FA25</small>
<br/>
<small>Module due: 09/07/2025 11:59PM EST</small>

This module contains a basic web scraper for https://www.thegradcafe.com/survey/, in addition to some data cleaning scripts.

## Requirements

* Python 3.10+

<small>_The codebase was developed on OSX 15.6.1.  Compatible systems should work, however the setup instructions may differ for Windows._</small>

## Getting started

To run the app, first set up your environment and install the package dependencies:

```sh
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Running the scraper:

Execute the `scrape.py` script:

```sh
python scrape.py
```

Once scraping is complete, the data will be saved to disk.

### CLI Options:

#### --out <filename>

Updates the filename where the final scrape data is saved.  Defaults to `applicant_data.json`.

_Example:_
```sh
python scrape.py --out dataset.json
```

#### --page <number>

Begins the scrape at the given page number.  Defaults to 1.

_Example:_
```sh
python scrape.py --page 35
```

#### --limit <number>

Limits the scrape to the given number of pages.  By default, all pages will be crawled.

_Example:_
```sh
python scrape.py --limit 10
```

## Running the cleaner:

Execute the `clean.py` script:

```sh
python clean.py
```

## About the Project

Hey there, I'm **Wes DiMiceli**.  My JHED ID is _wdimice1_.

### Approach:

This is a straightforward scraper using the BeautifulSoup library.

On startup, we check args then pass control over to the `scrape_data` function. This will enter a loop, repeatedly calling `scrape_page` with incrementing page numbers, only exiting when we hit the user-defined limit or the last scrape reported that no further pages were discovered.  The results of each page are appended to the final list, which is then saved to disk.

The scrape page function always checks the `robots.txt` file to ensure we have permission to get data for the particular URL we are interested in.  Our bot is given a unique user agent (`WesBot/1.0`) to identify ourselves to the sites we crawl.  Once we have verified we're OK to continue, we grab the page's HTML response and load it into BeautifulSoup.  Once we're done scraping this page, we find all anchor elements that point to other pages and look for any that have a bigger page number. If so, we report back that there is more data to scrape.

The architecture involved a few classes to assist and structure our pipeline.

`AdmissionResult`: Represents a single data entry that we are interested in scraping.  This class contains methods for parsing and manipulating data that we scrape.

`Decision`: Represents an admission decision, or the status of an application and its date.

`Tags`: Represents all of the miscellaneous data points that are also presented with a single entry, namely academic test scores and the term applied for.  These data points are presented on the website as a tag cloud, therefore its code representation is aligned to that for easier processing.

The classes follow a uniform pattern: each is instantiated from a `_from_soup` class method, which receives an object from BeautifulSoup that can be crawled for the data each class is interested in.  This way, we can achieve a clean separation of concerns, where different facets of the scrape data can be handled by self contained units.

### Known Issues:

The code fails to parse admit decisions that display a date but no "status".  They appear on the site as "on {month}, {day}" instead of "Accepted on {month}, {day}".  These cases are rare, so my code assumes a decision and the date always come as a pair.  Technically, we are dropping data points on occasion, so this aspect could be made more robust.  The changes would likely be straightforward: allowing the decision status to be None and then updating the regex to account for possibly missing strings.

### robots.txt

The site's robots.txt file was checked.  Only a handful of user agents are disallowed.  For the remainder:

```
User-agent: *
Disallow: /cgi-bin/
Disallow: /index-ad-test.php
```

## Citations

“Check If a Class Is a Dataclass in Python.” 2019. Stack Overflow. May 14, 2019. https://stackoverflow.com/questions/56106116/check-if-a-class-is-a-dataclass-in-python.

“Issues Within Code Around Leap Year Using Datetime (Beginner Help).” 2020. Stack Overflow. May 14, 2020. https://stackoverflow.com/questions/61795172/issues-within-code-around-leap-year-using-datetime-beginner-help.
