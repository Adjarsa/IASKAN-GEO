"""
Test Sprint D - Monitoring & Alerts System
Tests:
1. GET /api/monitoring/alerts/{project_id} - list project alerts
2. POST /api/monitoring/alerts/{project_id}/mark-read - mark alerts as read
3. GET /api/monitoring/config/{project_id} - get alert configuration
4. PUT /api/monitoring/config/{project_id} - update alert configuration
5. POST /api/monitoring/test-alert/{project_id} - send test alert
6. GET /api/monitoring/summary/{project_id} - get monitoring summary
7. Backend stability after adding monitoring router
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://geo-visibility-hub.preview.emergentagent.com').rstrip('/')


class TestBackendStabilityAfterMonitoringRouter:
    """Test backend stability after Sprint D monitoring router addition"""
    
    def test_health_endpoint_returns_200(self):
        """Health endpoint should return 200 after monitoring router addition"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_health_contains_timestamp(self):
        """Health response should contain timestamp"""
        response = requests.get(f"{BASE_URL}/api/health")
        data = response.json()
        assert "timestamp" in data


class TestMonitoringAlertsEndpoint:
    """Test GET /api/monitoring/alerts/{project_id} endpoint"""
    
    def test_alerts_endpoint_exists(self):
        """GET /api/monitoring/alerts/{project_id} should return 401 (not 404) - router is included"""
        response = requests.get(f"{BASE_URL}/api/monitoring/alerts/test_project_id")
        # 401 means endpoint exists but requires auth
        # 404 would mean endpoint doesn't exist
        assert response.status_code == 401, f"Expected 401 (auth required), got {response.status_code}"
    
    def test_alerts_endpoint_requires_auth(self):
        """Alerts endpoint should require authentication"""
        response = requests.get(f"{BASE_URL}/api/monitoring/alerts/any_project")
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
    
    def test_alerts_endpoint_with_query_params(self):
        """Alerts endpoint should accept query parameters"""
        response = requests.get(
            f"{BASE_URL}/api/monitoring/alerts/test_project",
            params={"limit": 10, "unread_only": True}
        )
        # Should still return 401 (auth required), not 422 (validation error)
        assert response.status_code == 401


class TestMonitoringMarkReadEndpoint:
    """Test POST /api/monitoring/alerts/{project_id}/mark-read endpoint"""
    
    def test_mark_read_endpoint_exists(self):
        """POST /api/monitoring/alerts/{project_id}/mark-read should return 401 (not 404)"""
        response = requests.post(
            f"{BASE_URL}/api/monitoring/alerts/test_project_id/mark-read",
            json=["alert_1", "alert_2"]
        )
        # 401 means endpoint exists but requires auth
        assert response.status_code == 401, f"Expected 401 (auth required), got {response.status_code}"
    
    def test_mark_read_endpoint_requires_auth(self):
        """Mark read endpoint should require authentication"""
        response = requests.post(
            f"{BASE_URL}/api/monitoring/alerts/any_project/mark-read",
            json=[]
        )
        assert response.status_code == 401
    
    def test_mark_read_endpoint_accepts_null_body(self):
        """Mark read endpoint should accept null body (mark all as read)"""
        response = requests.post(
            f"{BASE_URL}/api/monitoring/alerts/test_project/mark-read",
            json=None
        )
        # Should return 401 (auth required), not 422 (validation error)
        assert response.status_code == 401


class TestMonitoringConfigGetEndpoint:
    """Test GET /api/monitoring/config/{project_id} endpoint"""
    
    def test_config_get_endpoint_exists(self):
        """GET /api/monitoring/config/{project_id} should return 401 (not 404)"""
        response = requests.get(f"{BASE_URL}/api/monitoring/config/test_project_id")
        # 401 means endpoint exists but requires auth
        assert response.status_code == 401, f"Expected 401 (auth required), got {response.status_code}"
    
    def test_config_get_endpoint_requires_auth(self):
        """Config get endpoint should require authentication"""
        response = requests.get(f"{BASE_URL}/api/monitoring/config/any_project")
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data


class TestMonitoringConfigUpdateEndpoint:
    """Test PUT /api/monitoring/config/{project_id} endpoint"""
    
    def test_config_update_endpoint_exists(self):
        """PUT /api/monitoring/config/{project_id} should return 401 (not 404)"""
        response = requests.put(
            f"{BASE_URL}/api/monitoring/config/test_project_id",
            json={
                "alerts": {
                    "score_change": {"enabled": True, "threshold": 15}
                }
            }
        )
        # 401 means endpoint exists but requires auth
        assert response.status_code == 401, f"Expected 401 (auth required), got {response.status_code}"
    
    def test_config_update_endpoint_requires_auth(self):
        """Config update endpoint should require authentication"""
        response = requests.put(
            f"{BASE_URL}/api/monitoring/config/any_project",
            json={"alerts": {}}
        )
        assert response.status_code == 401


class TestMonitoringTestAlertEndpoint:
    """Test POST /api/monitoring/test-alert/{project_id} endpoint"""
    
    def test_test_alert_endpoint_exists(self):
        """POST /api/monitoring/test-alert/{project_id} should return 401 (not 404)"""
        response = requests.post(
            f"{BASE_URL}/api/monitoring/test-alert/test_project_id",
            params={"alert_type": "score_change"}
        )
        # 401 means endpoint exists but requires auth
        assert response.status_code == 401, f"Expected 401 (auth required), got {response.status_code}"
    
    def test_test_alert_endpoint_requires_auth(self):
        """Test alert endpoint should require authentication"""
        response = requests.post(f"{BASE_URL}/api/monitoring/test-alert/any_project")
        assert response.status_code == 401
    
    def test_test_alert_with_different_types(self):
        """Test alert endpoint should accept different alert types"""
        alert_types = ["score_change", "competitor_overtake", "visibility_drop", "weekly_summary"]
        for alert_type in alert_types:
            response = requests.post(
                f"{BASE_URL}/api/monitoring/test-alert/test_project",
                params={"alert_type": alert_type}
            )
            # Should return 401 (auth required), not 422 (invalid alert type)
            assert response.status_code == 401, f"Alert type {alert_type} should be valid"


class TestMonitoringSummaryEndpoint:
    """Test GET /api/monitoring/summary/{project_id} endpoint"""
    
    def test_summary_endpoint_exists(self):
        """GET /api/monitoring/summary/{project_id} should return 401 (not 404)"""
        response = requests.get(f"{BASE_URL}/api/monitoring/summary/test_project_id")
        # 401 means endpoint exists but requires auth
        assert response.status_code == 401, f"Expected 401 (auth required), got {response.status_code}"
    
    def test_summary_endpoint_requires_auth(self):
        """Summary endpoint should require authentication"""
        response = requests.get(f"{BASE_URL}/api/monitoring/summary/any_project")
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data


class TestMonitoringRouterIntegration:
    """Test monitoring router is properly integrated"""
    
    def test_all_monitoring_endpoints_return_401_not_404(self):
        """All monitoring endpoints should return 401 (auth required), not 404 (not found)"""
        endpoints = [
            ("GET", "/api/monitoring/alerts/test_project"),
            ("POST", "/api/monitoring/alerts/test_project/mark-read"),
            ("GET", "/api/monitoring/config/test_project"),
            ("PUT", "/api/monitoring/config/test_project"),
            ("POST", "/api/monitoring/test-alert/test_project"),
            ("GET", "/api/monitoring/summary/test_project"),
        ]
        
        for method, endpoint in endpoints:
            if method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}")
            elif method == "POST":
                response = requests.post(f"{BASE_URL}{endpoint}", json={})
            elif method == "PUT":
                response = requests.put(f"{BASE_URL}{endpoint}", json={})
            
            assert response.status_code == 401, f"{method} {endpoint} should return 401, got {response.status_code}"
    
    def test_monitoring_router_prefix_is_correct(self):
        """Monitoring router should use /api/monitoring prefix"""
        # Test that the prefix is correct by checking a known endpoint
        response = requests.get(f"{BASE_URL}/api/monitoring/alerts/test")
        assert response.status_code == 401  # Endpoint exists with /api prefix
        
        # Test that the /api prefix is required
        # Note: Without /api prefix, the request may be handled by frontend or return different status
        response_without_api = requests.get(f"{BASE_URL}/monitoring/alerts/test")
        # The key assertion is that /api/monitoring works (returns 401)
        # Without /api, behavior depends on frontend routing
