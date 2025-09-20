"""Integration tests for end-to-end flows.

This module tests complete workflows from data pull through analysis update
to final rendering, ensuring the entire system works together correctly.
"""

import pytest
import re
from model import AdmissionResult, get_table


# a. End-to-end (pull -> update -> Render)
# i. Inject a fake scraper that returns multiple records
# ii. POST /pull-data succeeds and rows are in DB
# iii. POST /update-analysis succeeds (when not busy)
# iv. GET /analysis shows updated analysis with correctly formatted values


@pytest.mark.integration
def test_end_to_end_pull_update_render(client, mock_scrape):
    """Test complete end-to-end flow: pull -> update -> render with correctly formatted values."""
    resp = client.get("/grad-data/analysis")
    page_text = resp.get_data(as_text=True)

    assert page_text.count("Percent accepted: N/A") > 0

    client.post("/grad-data/analysis")

    resp = client.get("/grad-data/analysis?refresh")
    page_text = resp.get_data(as_text=True)

    assert page_text.count("Percent accepted: N/A") == 0

    # # Must contain "Answer:" labels - should appear multiple times
    # answer_count = page_text.count("A:")
    # assert answer_count >= 1, "Page should contain at least one 'Answer:' label"

    # # Find all percentages in the response
    percentages = re.findall(r"\d+\.\d{2}%", page_text)

    # # Should find at least some percentages
    assert len(percentages) > 0, "Should find at least one percentage with two decimals"


# b. Multiple pulls
# i. Running POST /pull-data twice with overlapping data remains consistent with
# uniqueness policy.


@pytest.mark.integration
def test_multiple_pulls_idempotency(client, mock_scrape):
    """Test that running POST /analysis twice with overlapping data remains consistent."""
    client.post("/grad-data/analysis")

    # Fetch the first row and get its ID
    row = AdmissionResult.execute_raw(f"SELECT * FROM {get_table()} LIMIT 1;", [])[0]
    first_row_id = row["p_id"]

    client.post("/grad-data/analysis")

    # Check that there is exactly 1 row with that ID
    row_count_with_id = AdmissionResult.execute_raw(
        f"SELECT COUNT(*) AS count FROM {get_table()} WHERE p_id = %s;", [first_row_id]
    )
    assert row_count_with_id[0]["count"] == 1
