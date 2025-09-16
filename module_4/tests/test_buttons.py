# a. Test POST /pull-data (or whatever you named the path posting the pull data request)
# i. Returns 200
# ii. Triggers the loader with the rows from the scraper (should be faked / mocked)
# b. Test POST /update-analysis (or whatever you named the path posting the update analysis
# request)
# i. Returns 200 when not busy
# c. Test busy gating
# i. When a pull is “in progress”
# , POST /update-analysis returns 409 (and performs
# no update).
# ii. When busy, POST /pull-data returns 409