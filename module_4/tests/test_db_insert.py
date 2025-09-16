# a. Test insert on pull
# i. Before: target table empty
# ii. After POST/pull-data new rows exist with required (non-null) fields
# b. Test idempotency / constraints
# i. Duplicate rows do not create duplicates in database (accidentally pulling the
# same data should not result in the database acquiring duplicated rows).
# c. Test simple query function
# i. You should be able to query your data to return a dict with our expected keys
# (the required data fields within M3).