# a. End-to-end (pull -> update -> Render)
# i. Inject a fake scraper that returns multiple records
# ii. POST /pull-data succeeds and rows are in DB
# iii. POST /update-analysis succeeds (when not busy)
# iv. GET /analysis shows updated analysis with correctly formatted values
# b. Multiple pulls
# i. Running POST /pull-data twice with overlapping data remains consistent with
# uniqueness policy.