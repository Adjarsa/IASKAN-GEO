"""
Test suite for new PostgreSQL-based analysis endpoints
Tests:
1. /api/analyses - List analyses endpoint
2. /api/analysis/{id} - Get analysis detail endpoint
3. /api/analyses/history/{project_id} - Get history chart data
4. Router imports and module structure
"""
import pytest
import requests
import os
import sys
import asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://llm-share-voice.preview.emergentagent.com').rstrip('/')


class TestAnalysesRouterImports:
    """Test that new routers import correctly"""
    
    def test_analyses_router_import(self):
        """Test analyses router imports"""
        from app.routers import analyses
        assert hasattr(analyses, 'router')
        assert analyses.router is not None
    
    def test_analysis_router_import(self):
        """Test analysis router imports"""
        from app.routers import analysis
        assert hasattr(analysis, 'router')
        assert analysis.router is not None
    
    def test_analysis_service_import(self):
        """Test AnalysisService imports from db.services"""
        from app.db.services import AnalysisService
        assert AnalysisService is not None
        assert hasattr(AnalysisService, 'get_by_id')
        assert hasattr(AnalysisService, 'get_by_project')
        assert hasattr(AnalysisService, 'get_by_user')
        assert hasattr(AnalysisService, 'create')
        assert hasattr(AnalysisService, 'update')
        assert hasattr(AnalysisService, 'to_dict')
    
    def test_project_service_import(self):
        """Test ProjectService imports from db.services"""
        from app.db.services import ProjectService
        assert ProjectService is not None
        assert hasattr(ProjectService, 'get_by_id')
        assert hasattr(ProjectService, 'get_by_user')


class TestAnalysesEndpointWithoutAuth:
    """Test analyses endpoint responses without authentication"""
    
    def test_analyses_list_requires_auth(self):
        """Test GET /api/analyses requires authentication"""
        response = requests.get(f"{BASE_URL}/api/analyses", timeout=10)
        # Should return 401 Unauthorized or 403 Forbidden
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
    
    def test_analyses_list_with_project_requires_auth(self):
        """Test GET /api/analyses?project_id=X requires authentication"""
        response = requests.get(f"{BASE_URL}/api/analyses?project_id=test123", timeout=10)
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
    
    def test_analyses_history_requires_auth(self):
        """Test GET /api/analyses/history/{project_id} requires authentication"""
        response = requests.get(f"{BASE_URL}/api/analyses/history/test123", timeout=10)
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
    
    def test_analysis_detail_requires_auth(self):
        """Test GET /api/analysis/{id} requires authentication"""
        response = requests.get(f"{BASE_URL}/api/analysis/test123", timeout=10)
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"


class TestAnalysisEndpointWithoutAuth:
    """Test analysis endpoint responses without authentication"""
    
    def test_analysis_start_requires_auth(self):
        """Test POST /api/analysis/start requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/analysis/start",
            json={"project_id": "test123"},
            timeout=10
        )
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
    
    def test_analysis_status_requires_auth(self):
        """Test GET /api/analysis/status/{id} requires authentication"""
        response = requests.get(f"{BASE_URL}/api/analysis/status/test123", timeout=10)
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
    
    def test_analysis_results_requires_auth(self):
        """Test GET /api/analysis/results/{id} requires authentication"""
        response = requests.get(f"{BASE_URL}/api/analysis/results/test123", timeout=10)
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
    
    def test_analysis_cancel_requires_auth(self):
        """Test POST /api/analysis/cancel/{id} requires authentication"""
        response = requests.post(f"{BASE_URL}/api/analysis/cancel/test123", timeout=10)
        assert response.status_code in [401, 403, 405], f"Expected 401/403/405, got {response.status_code}"
    
    def test_analysis_quota_requires_auth(self):
        """Test GET /api/analysis/quota requires authentication"""
        response = requests.get(f"{BASE_URL}/api/analysis/quota", timeout=10)
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"


class TestAnalysisServiceMethods:
    """Test AnalysisService database methods"""
    
    def test_analysis_service_get_by_id_async(self):
        """Test AnalysisService.get_by_id is async and callable"""
        from app.db.services import AnalysisService
        import inspect
        assert inspect.iscoroutinefunction(AnalysisService.get_by_id)
    
    def test_analysis_service_get_by_project_async(self):
        """Test AnalysisService.get_by_project is async and callable"""
        from app.db.services import AnalysisService
        import inspect
        assert inspect.iscoroutinefunction(AnalysisService.get_by_project)
    
    def test_analysis_service_get_by_user_async(self):
        """Test AnalysisService.get_by_user is async and callable"""
        from app.db.services import AnalysisService
        import inspect
        assert inspect.iscoroutinefunction(AnalysisService.get_by_user)
    
    def test_analysis_service_create_async(self):
        """Test AnalysisService.create is async and callable"""
        from app.db.services import AnalysisService
        import inspect
        assert inspect.iscoroutinefunction(AnalysisService.create)
    
    def test_analysis_service_update_async(self):
        """Test AnalysisService.update is async and callable"""
        from app.db.services import AnalysisService
        import inspect
        assert inspect.iscoroutinefunction(AnalysisService.update)
    
    def test_analysis_service_to_dict_static(self):
        """Test AnalysisService.to_dict is callable"""
        from app.db.services import AnalysisService
        assert callable(AnalysisService.to_dict)


class TestAnalysisModelsImport:
    """Test Analysis-related models import correctly"""
    
    def test_analysis_model_import(self):
        """Test Analysis model imports"""
        from app.db.models import Analysis
        assert Analysis is not None
    
    def test_analysis_status_enum_import(self):
        """Test AnalysisStatus enum imports"""
        from app.db.models import AnalysisStatus
        assert AnalysisStatus is not None
        assert hasattr(AnalysisStatus, 'PENDING')
        assert hasattr(AnalysisStatus, 'RUNNING')
        assert hasattr(AnalysisStatus, 'COMPLETED')
        assert hasattr(AnalysisStatus, 'FAILED')
    
    def test_analysis_model_has_required_fields(self):
        """Test Analysis model has required fields"""
        from app.db.models import Analysis
        import inspect
        
        # Check __table__ columns
        if hasattr(Analysis, '__table__'):
            columns = [c.name for c in Analysis.__table__.columns]
            expected_columns = [
                'analysis_id', 'project_id', 'user_id', 'status',
                'global_score', 'grade', 'ai_scores', 'rate_scores',
                'created_at'
            ]
            for col in expected_columns:
                assert col in columns, f"Expected column '{col}' not found in Analysis model"


class TestRouterEndpointsRegistration:
    """Test that router endpoints are properly registered in the app"""
    
    def test_analyses_routes_available(self):
        """Test /api/analyses routes are registered"""
        # Test endpoint exists by checking response type (not 404 Not Found)
        response = requests.get(f"{BASE_URL}/api/analyses", timeout=10)
        # 401/403 means endpoint exists but requires auth
        # 404 means endpoint doesn't exist
        assert response.status_code != 404, "GET /api/analyses endpoint not found"
    
    def test_analyses_history_route_available(self):
        """Test /api/analyses/history route is registered"""
        response = requests.get(f"{BASE_URL}/api/analyses/history/test_proj", timeout=10)
        assert response.status_code != 404, "GET /api/analyses/history/{project_id} endpoint not found"
    
    def test_analysis_detail_route_available(self):
        """Test /api/analysis/{id} route is registered"""
        response = requests.get(f"{BASE_URL}/api/analysis/test123", timeout=10)
        assert response.status_code != 404, "GET /api/analysis/{id} endpoint not found"
    
    def test_analysis_start_route_available(self):
        """Test POST /api/analysis/start route is registered"""
        response = requests.post(
            f"{BASE_URL}/api/analysis/start",
            json={"project_id": "test123"},
            timeout=10
        )
        assert response.status_code != 404, "POST /api/analysis/start endpoint not found"
    
    def test_analysis_quota_route_available(self):
        """Test GET /api/analysis/quota route is registered"""
        response = requests.get(f"{BASE_URL}/api/analysis/quota", timeout=10)
        assert response.status_code != 404, "GET /api/analysis/quota endpoint not found"


class TestDatabaseAsyncOperations:
    """Test async database operations work correctly"""
    
    def test_session_maker_context_manager(self):
        """Test async_session_maker works as context manager"""
        from app.db.database import async_session_maker
        
        async def test_session():
            async with async_session_maker() as session:
                return session is not None
        
        result = asyncio.run(test_session())
        assert result is True
    
    def test_analysis_query_returns_list(self):
        """Test querying analyses returns a list (empty or with data)"""
        from app.db.database import async_session_maker
        from app.db.services import AnalysisService
        
        async def query_analyses():
            async with async_session_maker() as db:
                # Using a non-existent user_id should return empty list
                analyses = await AnalysisService.get_by_user(db, "non_existent_user_xyz")
                return isinstance(analyses, list)
        
        result = asyncio.run(query_analyses())
        assert result is True, "AnalysisService.get_by_user should return a list"
    
    def test_analysis_get_by_id_returns_none_for_nonexistent(self):
        """Test get_by_id returns None for non-existent analysis"""
        from app.db.database import async_session_maker
        from app.db.services import AnalysisService
        
        async def query_analysis():
            async with async_session_maker() as db:
                analysis = await AnalysisService.get_by_id(db, "non_existent_analysis_xyz")
                return analysis
        
        result = asyncio.run(query_analysis())
        assert result is None, "Non-existent analysis should return None"


class TestHealthEndpoint:
    """Test health endpoint still works after changes"""
    
    def test_health_endpoint_returns_healthy(self):
        """Test /api/health returns healthy status"""
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
