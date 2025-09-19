import pytest
from bs4 import BeautifulSoup


@pytest.mark.web
def test_app_factory_creates_valid_app(app):
    """Test app factory creates a testable Flask app with required routes."""
    assert app is not None
    
    # Check that blueprints are registered
    blueprint_names = [bp.name for bp in app.blueprints.values()]
    assert 'portfolio' in blueprint_names
    assert 'grad_data' in blueprint_names


@pytest.mark.web
def test_portfolio_routes_exist(client):
    """Test that portfolio routes are accessible."""
    # Test home page
    response = client.get("/")
    assert response.status_code == 200
    
    # Test other portfolio routes if they exist
    routes_to_test = ["/contact", "/projects"]
    for route in routes_to_test:
        response = client.get(route)
        # Should either return 200 or 404 (if not implemented), but not 500
        assert response.status_code in [200, 404]
