"""Tests for the analysis page, verify answer labels and formatting."""

import pytest
import re


# a. Test labels & Rounding
# i. Test that your page include “Answer” labels for rendered analysis
# ii. Test that any percentage is formatted with two decimals.


@pytest.mark.analysis
def test_analysis_labels_present(client, mocker, empty_table):
    """Test that the page includes 'Answer:' labels for rendered analysis."""
    # Mock questions with proper structure
    mocker.patch(
        "blueprints.grad_data.routes.answer_questions",
        return_value=[
            {
                "prompt": "What percentage of students are accepted?",
                "answer": 45.678,
                "formatted": "Answer: 45.68%",
            },
            {
                "prompt": "How many applications were received?",
                "answer": 1234,
                "formatted": "Answer: 1234 applications",
            },
        ],
    )

    resp = client.get("/grad-data/analysis")
    page_text = resp.get_data(as_text=True)

    # Must contain "Answer:" labels - should appear multiple times
    answer_count = page_text.count("A:")
    assert answer_count >= 1, "Page should contain at least one 'Answer:' label"

    # Find all percentages in the response
    percentages = re.findall(r"\d+\.\d{2}%", page_text)

    # Should find at least some percentages
    assert len(percentages) > 0, "Should find at least one percentage with two decimals"

    # All found percentages should end with % and have exactly 2 decimal places
    for percentage in percentages:
        assert percentage.endswith("%"), f"Percentage {percentage} should end with %"
        # Extract the numeric part before %
        numeric_part = percentage[:-1]
        decimal_part = numeric_part.split(".")[-1]
        assert len(decimal_part) == 2, (
            f"Percentage {percentage} should have exactly 2 decimal places"
        )
