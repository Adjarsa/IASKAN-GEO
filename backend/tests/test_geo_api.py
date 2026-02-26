"""
Test suite for GEO features API endpoints
Tests /api/visibility/{project_id} and /api/content-audit/{project_id}
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://brand-ai-lens.preview.emergentagent.com').rstrip('/')

# Test session and project created earlier
TEST_SESSION_TOKEN = 'test_session_1772018666518'
TEST_PROJECT_ID = 'proj_test_1772018666518'


@pytest.fixture
def authenticated_client():
    """Requests session with auth header"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {TEST_SESSION_TOKEN}"
    })
    return session


class TestVisibilityAPI:
    """Tests for /api/visibility/{project_id} endpoint"""
    
    def test_visibility_endpoint_returns_200(self, authenticated_client):
        """Test that visibility endpoint returns 200 for authenticated user"""
        response = authenticated_client.get(f"{BASE_URL}/api/visibility/{TEST_PROJECT_ID}")
        assert response.status_code == 200
    
    def test_visibility_endpoint_returns_correct_structure(self, authenticated_client):
        """Test that visibility endpoint returns expected data structure"""
        response = authenticated_client.get(f"{BASE_URL}/api/visibility/{TEST_PROJECT_ID}")
        assert response.status_code == 200
        
        data = response.json()
        
        # Check required fields
        assert "global_visibility_score" in data
        assert "ai_engines" in data
        assert "position_distribution" in data
        assert "thematic_visibility" in data
        assert "recent_queries" in data
        assert "has_data" in data
    
    def test_visibility_endpoint_position_distribution_structure(self, authenticated_client):
        """Test that position distribution has correct structure"""
        response = authenticated_client.get(f"{BASE_URL}/api/visibility/{TEST_PROJECT_ID}")
        data = response.json()
        
        pos_dist = data.get("position_distribution", {})
        assert "first" in pos_dist
        assert "second" in pos_dist
        assert "third" in pos_dist
        assert "other" in pos_dist
        assert "absent" in pos_dist
    
    def test_visibility_endpoint_returns_401_without_auth(self):
        """Test that visibility endpoint returns 401 without authentication"""
        response = requests.get(f"{BASE_URL}/api/visibility/{TEST_PROJECT_ID}")
        assert response.status_code == 401
    
    def test_visibility_endpoint_returns_404_for_invalid_project(self, authenticated_client):
        """Test that visibility endpoint returns 404 for non-existent project"""
        response = authenticated_client.get(f"{BASE_URL}/api/visibility/invalid_project_id_123")
        assert response.status_code == 404


class TestContentAuditAPI:
    """Tests for /api/content-audit/{project_id} endpoint"""
    
    def test_content_audit_endpoint_returns_200(self, authenticated_client):
        """Test that content-audit endpoint returns 200 for authenticated user"""
        response = authenticated_client.get(f"{BASE_URL}/api/content-audit/{TEST_PROJECT_ID}")
        assert response.status_code == 200
    
    def test_content_audit_endpoint_returns_correct_structure(self, authenticated_client):
        """Test that content-audit endpoint returns expected data structure"""
        response = authenticated_client.get(f"{BASE_URL}/api/content-audit/{TEST_PROJECT_ID}")
        assert response.status_code == 200
        
        data = response.json()
        
        # Check required fields
        assert "global_citability_score" in data
        assert "pages_analyzed" in data
        assert "structure_score" in data
        assert "content_gaps" in data
        assert "schema_coverage" in data
        assert "pages" in data
        assert "gaps" in data
        assert "structure_recommendations" in data
        assert "has_data" in data
    
    def test_content_audit_endpoint_returns_401_without_auth(self):
        """Test that content-audit endpoint returns 401 without authentication"""
        response = requests.get(f"{BASE_URL}/api/content-audit/{TEST_PROJECT_ID}")
        assert response.status_code == 401
    
    def test_content_audit_endpoint_returns_404_for_invalid_project(self, authenticated_client):
        """Test that content-audit endpoint returns 404 for non-existent project"""
        response = authenticated_client.get(f"{BASE_URL}/api/content-audit/invalid_project_id_123")
        assert response.status_code == 404


class TestHealthEndpoint:
    """Basic health check tests"""
    
    def test_health_endpoint_returns_200(self):
        """Test that health endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
    
    def test_health_endpoint_returns_healthy_status(self):
        """Test that health endpoint returns healthy status"""
        response = requests.get(f"{BASE_URL}/api/health")
        data = response.json()
        assert data.get("status") == "healthy"


class TestSubscriptionPlansEndpoint:
    """Tests for subscription plans endpoint"""
    
    def test_subscription_plans_returns_200(self):
        """Test that subscription plans endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/subscription/plans")
        assert response.status_code == 200
    
    def test_subscription_plans_contains_required_plans(self):
        """Test that subscription plans contains starter, pro, business"""
        response = requests.get(f"{BASE_URL}/api/subscription/plans")
        data = response.json()
        
        plans = data.get("plans", {})
        assert "starter" in plans
        assert "pro" in plans
        assert "business" in plans
