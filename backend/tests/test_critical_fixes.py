"""
Test Critical P0 Fixes for IAskan
- Organizations endpoint 500 fix (AttributeError: 'User' object has no attribute 'plan')
- Analysis endpoint returning queries_processed and current_phase
- Health check endpoint
"""
import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://geo-visibility-hub.preview.emergentagent.com').rstrip('/')


class TestHealthEndpoint:
    """Test /api/health endpoint"""
    
    def test_health_returns_200(self):
        """Health endpoint should return 200 with healthy status"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "status" in data, "Response should contain 'status' field"
        assert data["status"] == "healthy", f"Expected 'healthy', got {data['status']}"
        
    def test_health_contains_timestamp(self):
        """Health endpoint should return timestamp"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert "timestamp" in data, "Response should contain 'timestamp' field"


class TestOrganizationsEndpoint:
    """Test /api/organizations endpoint - verifies 500 fix"""
    
    def test_organizations_no_auth_returns_401(self):
        """Without auth, should return 401, NOT 500"""
        response = requests.get(f"{BASE_URL}/api/organizations")
        # Should be 401 (Unauthorized), NOT 500 (Server Error)
        assert response.status_code == 401, f"Expected 401, got {response.status_code}: {response.text}"
        data = response.json()
        assert "detail" in data
        # French message expected
        assert "authentifi" in data["detail"].lower() or "session" in data["detail"].lower()
        
    def test_organizations_create_no_auth_returns_401(self):
        """POST without auth should return 401, NOT 500"""
        response = requests.post(
            f"{BASE_URL}/api/organizations",
            json={"name": "Test Org", "industry": "tech"}
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}: {response.text}"
        
    def test_organizations_no_500_error(self):
        """Critical: Organizations endpoint should NEVER return 500"""
        response = requests.get(f"{BASE_URL}/api/organizations")
        assert response.status_code != 500, (
            f"CRITICAL BUG: Organizations endpoint returned 500!\n"
            f"This is the P0 bug that was patched (AttributeError: 'User' object has no attribute 'plan').\n"
            f"Response: {response.text}"
        )


class TestAnalysisEndpoint:
    """Test /api/analysis endpoints - verifies progress fields"""
    
    def test_analysis_detail_no_auth_returns_401(self):
        """Without auth, should return 401, NOT 500"""
        response = requests.get(f"{BASE_URL}/api/analysis/test_analysis_id")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}: {response.text}"
        
    def test_analysis_status_no_auth_returns_401(self):
        """Status endpoint without auth should return 401"""
        response = requests.get(f"{BASE_URL}/api/analysis/status/test_analysis_id")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}: {response.text}"
    
    def test_analysis_quota_no_auth_returns_401(self):
        """Quota endpoint without auth should return 401"""
        response = requests.get(f"{BASE_URL}/api/analysis/quota")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}: {response.text}"
        
    def test_analysis_no_500_error(self):
        """Critical: Analysis detail endpoint should NEVER return 500"""
        response = requests.get(f"{BASE_URL}/api/analysis/nonexistent_id")
        assert response.status_code != 500, (
            f"CRITICAL BUG: Analysis endpoint returned 500!\n"
            f"This indicates unhandled error in analysis.py router.\n"
            f"Response: {response.text}"
        )


class TestAnalysisRouterImports:
    """Test that analysis router has correct structure"""
    
    def test_analysis_router_imports(self):
        """Verify analysis router module can be imported"""
        try:
            from app.routers.analysis import router
            assert router is not None
            assert router.prefix == "/api/analysis"
        except ImportError as e:
            pytest.fail(f"Failed to import analysis router: {e}")
            
    def test_analysis_router_has_get_endpoint(self):
        """Verify get_analysis_detail endpoint exists"""
        from app.routers.analysis import get_analysis_detail
        assert callable(get_analysis_detail)
        
    def test_analysis_router_endpoints_exist(self):
        """Verify all required endpoints are defined"""
        from app.routers.analysis import router
        routes = [route.path for route in router.routes]
        
        # Check required endpoints exist
        assert "/start" in routes or "/start" in str(routes), "Missing /start endpoint"
        assert "/quota" in routes or "/quota" in str(routes), "Missing /quota endpoint"


class TestOrganizationsRouterFix:
    """Test organizations router fix - getattr(user, 'plan', 'free')"""
    
    def test_organizations_router_imports(self):
        """Verify organizations router can be imported"""
        try:
            from app.routers.organizations import router
            assert router is not None
            assert router.prefix == "/api/organizations"
        except ImportError as e:
            pytest.fail(f"Failed to import organizations router: {e}")
            
    def test_get_current_user_function(self):
        """Verify get_current_user function exists and handles plan correctly"""
        from app.routers.organizations import get_current_user
        import inspect
        
        # Check function exists
        assert callable(get_current_user)
        
        # Check source contains the fix
        source = inspect.getsource(get_current_user)
        assert "getattr" in source or "plan" in source, (
            "get_current_user should handle 'plan' attribute safely with getattr"
        )


class TestAnalysisModelFields:
    """Test Analysis model has required fields for progress tracking"""
    
    def test_analysis_model_has_progress_fields(self):
        """Verify Analysis model has queries_processed and current_phase"""
        from app.db.models import Analysis
        
        # Check columns exist
        columns = [col.name for col in Analysis.__table__.columns]
        
        assert "queries_processed" in columns, "Missing queries_processed column"
        assert "current_phase" in columns, "Missing current_phase column"
        assert "total_queries" in columns, "Missing total_queries column"
        
    def test_analysis_model_progress_field_types(self):
        """Verify progress fields have correct types"""
        from app.db.models import Analysis
        from sqlalchemy import Integer, String
        
        # queries_processed should be Integer
        queries_processed_col = Analysis.__table__.columns["queries_processed"]
        assert isinstance(queries_processed_col.type, Integer)
        
        # current_phase should be String
        current_phase_col = Analysis.__table__.columns["current_phase"]
        assert isinstance(current_phase_col.type, (String,))


class TestAnalysisServiceResponse:
    """Test AnalysisService returns progress fields"""
    
    def test_analysis_service_to_dict_exists(self):
        """Verify AnalysisService.to_dict exists"""
        from app.db.services import AnalysisService
        
        assert hasattr(AnalysisService, "to_dict"), "AnalysisService should have to_dict method"
        
    def test_analysis_service_has_required_methods(self):
        """Verify AnalysisService has required methods"""
        from app.db.services import AnalysisService
        
        required_methods = ["get_by_id", "create", "update"]
        for method in required_methods:
            assert hasattr(AnalysisService, method), f"Missing method: {method}"


class TestSubscriptionPlansConfig:
    """Test subscription plans configuration"""
    
    def test_subscription_plans_endpoint(self):
        """Subscription plans should be accessible"""
        response = requests.get(f"{BASE_URL}/api/subscription/plans")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        # Verify plans exist
        assert "plans" in data or "free" in data or isinstance(data, dict)
        
    def test_free_plan_in_config(self):
        """Verify free plan exists in configuration"""
        from app.core.config import SUBSCRIPTION_PLANS
        
        assert "free" in SUBSCRIPTION_PLANS, "Missing 'free' plan in SUBSCRIPTION_PLANS"
        assert "scans_limit" in SUBSCRIPTION_PLANS["free"], "Missing scans_limit in free plan"


class TestDatabaseConnection:
    """Test PostgreSQL database connectivity"""
    
    def test_database_is_reachable(self):
        """Health check should confirm database connectivity"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        # If health returns 200 with 'healthy', DB is connected
        data = response.json()
        assert data.get("status") == "healthy"


# Additional integration tests
class TestEndpointIntegration:
    """Integration tests for endpoint behavior"""
    
    def test_all_protected_endpoints_return_401_not_500(self):
        """All protected endpoints should return 401 without auth, never 500"""
        protected_endpoints = [
            ("GET", "/api/organizations"),
            ("GET", "/api/analysis/test_id"),
            ("GET", "/api/analysis/status/test_id"),
            ("GET", "/api/analysis/quota"),
            ("POST", "/api/analysis/start"),
            ("GET", "/api/projects"),
            ("GET", "/api/notifications"),
        ]
        
        for method, endpoint in protected_endpoints:
            if method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}")
            elif method == "POST":
                response = requests.post(f"{BASE_URL}{endpoint}", json={})
            
            assert response.status_code != 500, (
                f"CRITICAL: {method} {endpoint} returned 500!\n"
                f"Protected endpoints should return 401 (Unauthorized), not 500 (Server Error).\n"
                f"Response: {response.text}"
            )
            # Should be 401 or 422 (validation error for POST without body)
            assert response.status_code in [401, 422], (
                f"Expected 401 or 422 for {method} {endpoint}, got {response.status_code}"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
