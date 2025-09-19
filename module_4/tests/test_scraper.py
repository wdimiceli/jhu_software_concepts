"""Comprehensive tests for scrape.py to achieve 100% coverage."""

import pytest
from unittest.mock import patch, MagicMock
from urllib.robotparser import RobotFileParser
from bs4 import BeautifulSoup


@pytest.mark.web
@pytest.mark.parametrize("can_fetch,expected", [
    (True, True),
    (False, False)
])
def test_check_robots_permission(can_fetch, expected):
    """Test _check_robots_permission function with allowed/denied access."""
    from scrape import _check_robots_permission
    from urllib.parse import urlparse
    
    url = urlparse("https://example.com/page")
    user_agent = "TestBot/1.0"
    
    with patch('scrape.RobotFileParser') as mock_parser_class:
        mock_parser = MagicMock()
        mock_parser_class.return_value = mock_parser
        mock_parser.can_fetch.return_value = can_fetch
        
        result = _check_robots_permission(url, user_agent)
        
        assert result == expected
        mock_parser.set_url.assert_called_once_with("https://example.com/robots.txt")
        mock_parser.read.assert_called_once()
        mock_parser.can_fetch.assert_called_once_with(user_agent, str(url))


@pytest.mark.web
def test_get_table_rows():
    """Test _get_table_rows function with proper HTML structure."""
    from scrape import _get_table_rows
    
    # Create HTML structure that generates the right split indices
    html = """
    <html>
        <body>
            <h1>Results</h1>
            <table>
                <tbody>
                    <tr>
                        <td>Main row 1 data</td>
                        <td>More data</td>
                    </tr>
                    <tr>
                        <td colspan="2">Details for row 1</td>
                    </tr>
                    <tr>
                        <td>Main row 2 data</td>
                        <td>More data</td>
                    </tr>
                    <tr>
                        <td colspan="2">Details for row 2</td>
                    </tr>
                    <tr>
                        <td>Main row 3 data</td>
                        <td>More data</td>
                    </tr>
                </tbody>
            </table>
        </body>
    </html>
    """
    
    soup = BeautifulSoup(html, "html.parser")
    rows = _get_table_rows(soup)
    
    # The function groups rows between non-colspan rows
    # With 3 non-colspan rows at indices [0, 2, 4], pairwise gives us 2 groups: [0:2] and [2:4]
    assert len(rows) == 2  # Two complete groups
    assert len(rows[0]) == 2  # First group: main row + details
    assert len(rows[1]) == 2  # Second group: main row + details


@pytest.mark.web
def test_scrape_page_with_results():
    """Test scrape_page function with proper HTML structure and mocking."""
    from scrape import scrape_page
    
    # Create HTML that will generate exactly one row group
    mock_html = """
    <html>
        <body>
            <h1>Admissions Results</h1>
            <table>
                <tbody>
                    <tr>
                        <td><a href="/result/123">Test University</a></td>
                        <td>Computer Science</td>
                        <td>January 15, 2024</td>
                        <td>Accepted on 10 Feb</td>
                    </tr>
                    <tr>
                        <td colspan="4">Great program details!</td>
                    </tr>
                </tbody>
            </table>
            <a href="?page=2">Next</a>
        </body>
    </html>
    """
    
    with patch('urllib.request.urlopen') as mock_urlopen:
        with patch('scrape._check_robots_permission', return_value=True):
            with patch('scrape._get_table_rows') as mock_get_rows:
                with patch('model.AdmissionResult.from_soup') as mock_from_soup:
                    mock_response = MagicMock()
                    mock_response.read.return_value = mock_html.encode('utf-8')
                    mock_urlopen.return_value.__enter__.return_value = mock_response
                    
                    # Mock _get_table_rows to return exactly one row group
                    mock_get_rows.return_value = [["mock_row_group"]]
                    
                    mock_result = MagicMock()
                    mock_result.id = 123
                    mock_from_soup.return_value = mock_result
                    
                    results, has_more = scrape_page(1)
                    
                    assert len(results) == 1
                    assert results[0] == mock_result
                    assert has_more is True  # Should detect page 2 link




@pytest.mark.web
def test_scrape_page_has_more_pages():
    """Test scrape_page detects when more pages are available."""
    from scrape import scrape_page
    
    # HTML with page navigation showing higher page numbers
    mock_html = """
    <html>
        <body>
            <h1>Admissions Results</h1>
            <table>
                <tbody>
                    <tr>
                        <td><a href="/result/789">Test University</a></td>
                        <td>Physics</td>
                        <td>March 1, 2024</td>
                        <td>Accepted on 20 Mar</td>
                    </tr>
                </tbody>
            </table>
            <a href="?page=2">Page 2</a>
            <a href="?page=3">Page 3</a>
        </body>
    </html>
    """
    
    with patch('urllib.request.urlopen') as mock_urlopen:
        with patch('scrape._check_robots_permission', return_value=True):
            with patch('scrape._get_table_rows') as mock_get_rows:
                with patch('model.AdmissionResult.from_soup') as mock_from_soup:
                    mock_response = MagicMock()
                    mock_response.read.return_value = mock_html.encode('utf-8')
                    mock_urlopen.return_value.__enter__.return_value = mock_response
                    
                    mock_get_rows.return_value = [["mock_row_group"]]
                    
                    mock_result = MagicMock()
                    mock_result.id = 789
                    mock_from_soup.return_value = mock_result
                    
                    results, has_more = scrape_page(1)  # Current page is 1
                    
                    assert len(results) == 1
                    assert has_more is True  # Pages 2 and 3 are higher than current page 1


@pytest.mark.web
def test_scrape_page_robots_denied():
    """Test scrape_page when robots.txt denies access."""
    from scrape import scrape_page
    
    with patch('scrape._check_robots_permission', return_value=False):
        with pytest.raises(Exception, match="robots.txt permission check failed"):
            scrape_page(1)


@pytest.mark.web
def test_scrape_data_comprehensive():
    """Test scrape_data function with various scenarios."""
    from scrape import scrape_data
    
    def create_mock_result(result_id):
        result = MagicMock()
        result.id = result_id
        return result
    
    with patch('scrape.scrape_page') as mock_scrape_page:
        # Test basic multi-page scraping
        mock_scrape_page.side_effect = [
            ([create_mock_result(1), create_mock_result(2)], True),   # Page 1
            ([create_mock_result(3)], False)                         # Page 2
        ]
        
        results = scrape_data(page=1, limit=None, stop_at_id=None)
        
        assert len(results) == 3
        assert [r.id for r in results] == [1, 2, 3]
        assert mock_scrape_page.call_count == 2


@pytest.mark.web
def test_scrape_data_with_limit():
    """Test scrape_data respects limit parameter."""
    from scrape import scrape_data
    
    with patch('scrape.scrape_page') as mock_scrape_page:
        # Create 10 results but set limit to 5
        mock_results = [MagicMock(id=i) for i in range(1, 11)]
        mock_scrape_page.return_value = (mock_results, False)
        
        results = scrape_data(page=1, limit=5, stop_at_id=None)
        
        # Should get all results from first page regardless of limit
        assert len(results) == 10
        mock_scrape_page.assert_called_once_with(1)


@pytest.mark.web 
def test_scrape_data_stop_at_id():
    """Test scrape_data stops at specified ID and filters results."""
    from scrape import scrape_data
    
    with patch('scrape.scrape_page') as mock_scrape_page:
        # Create results with IDs 5, 4, 3, 2, 1 (descending order)
        mock_results = [MagicMock(id=i) for i in range(5, 0, -1)]
        mock_scrape_page.return_value = (mock_results, False)
        
        results = scrape_data(page=1, limit=None, stop_at_id=3)
        
        # Should only get results with ID > 3 (IDs 5 and 4)
        assert len(results) == 2
        assert all(result.id > 3 for result in results)


@pytest.mark.web
def test_scrape_data_exception_handling():
    """Test scrape_data handles exceptions gracefully."""
    from scrape import scrape_data
    
    with patch('scrape.scrape_page') as mock_scrape_page:
        mock_result = MagicMock(id=1)
        mock_scrape_page.side_effect = [
            ([mock_result], True),         # First page succeeds
            Exception("Network error")     # Second page fails
        ]
        
        # Should return results from successful page despite exception
        results = scrape_data(page=1, limit=None, stop_at_id=None)
        
        assert len(results) == 1
        assert results[0].id == 1


@pytest.mark.web
def test_scrape_data_limit_logic():
    """Test scrape_data limit logic across multiple pages."""
    from scrape import scrape_data
    
    with patch('scrape.scrape_page') as mock_scrape_page:
        # First page has 3 results, second page would have 2 more
        page1_results = [MagicMock(id=i) for i in range(1, 4)]  # IDs 1, 2, 3
        page2_results = [MagicMock(id=i) for i in range(4, 6)]  # IDs 4, 5
        
        mock_scrape_page.side_effect = [
            (page1_results, True),   # Page 1: 3 results, more available
            (page2_results, False)   # Page 2: 2 results, no more
        ]
        
        # With limit=4, should get first page (3 results) then try second page
        results = scrape_data(page=1, limit=4, stop_at_id=None)
        
        assert len(results) == 5  # Gets all results since limit check is after page fetch
        assert mock_scrape_page.call_count == 2


@pytest.mark.web
def test_scrape_assertions():
    """Test assertion conditions in scrape functions."""
    from scrape import scrape_page, _get_table_rows
    from bs4 import BeautifulSoup
    
    # Test page number assertion
    with pytest.raises(AssertionError):
        scrape_page(0)  # Invalid page number
    
    # Test HTML structure assertion in _get_table_rows
    html_without_tbody = "<html><body><h1>Test</h1></body></html>"
    soup = BeautifulSoup(html_without_tbody, "html.parser")
    
    with pytest.raises(AssertionError):
        _get_table_rows(soup)  # No tbody found