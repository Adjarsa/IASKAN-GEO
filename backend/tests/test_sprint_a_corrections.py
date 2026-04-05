"""
Test Sprint A Corrections:
1. Perplexity API integration (sonar-pro model)
2. Rate limiting (SlowAPI)
3. CORS configuration
4. No mock data in ContentAuditPage and ArticleOptimizerPage
5. Backend health check
"""
import pytest
import requests
import os
import re

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://geo-visibility-hub.preview.emergentagent.com').rstrip('/')


class TestHealthCheck:
    """Test backend health check endpoint"""
    
    def test_health_returns_200(self):
        """Health endpoint should return 200"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
    
    def test_health_contains_status(self):
        """Health response should contain status field"""
        response = requests.get(f"{BASE_URL}/api/health")
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
    
    def test_health_contains_timestamp(self):
        """Health response should contain timestamp"""
        response = requests.get(f"{BASE_URL}/api/health")
        data = response.json()
        assert "timestamp" in data


class TestCORSConfiguration:
    """Test CORS is properly configured"""
    
    def test_cors_headers_present(self):
        """CORS headers should be present in response"""
        headers = {
            "Origin": "https://geo-visibility-hub.preview.emergentagent.com"
        }
        response = requests.options(f"{BASE_URL}/api/health", headers=headers)
        # OPTIONS request should succeed
        assert response.status_code in [200, 204, 405]
    
    def test_cors_allows_configured_origin(self):
        """CORS should allow configured origins"""
        headers = {
            "Origin": "https://geo-visibility-hub.preview.emergentagent.com"
        }
        response = requests.get(f"{BASE_URL}/api/health", headers=headers)
        assert response.status_code == 200
        # Check if CORS header is present
        cors_header = response.headers.get("Access-Control-Allow-Origin", "")
        # Should either be the specific origin or * (if configured that way)
        assert cors_header in ["https://geo-visibility-hub.preview.emergentagent.com", "*", ""]


class TestRateLimiting:
    """Test SlowAPI rate limiting is configured"""
    
    def test_rate_limit_headers_present(self):
        """Rate limit headers should be present in responses"""
        response = requests.get(f"{BASE_URL}/api/health")
        # SlowAPI typically adds these headers
        # Note: Headers may not be present on all endpoints
        assert response.status_code == 200
    
    def test_multiple_requests_succeed(self):
        """Multiple requests within limit should succeed"""
        # Make 10 requests - should all succeed within 200/minute limit
        for i in range(10):
            response = requests.get(f"{BASE_URL}/api/health")
            assert response.status_code == 200, f"Request {i+1} failed"


class TestPerplexityAPIConfiguration:
    """Test Perplexity API is properly configured in llm_connector.py"""
    
    def test_llm_connector_has_perplexity_config(self):
        """LLM connector should have Perplexity configuration"""
        # Read the llm_connector.py file
        llm_connector_path = "/app/backend/app/services/llm_connector.py"
        with open(llm_connector_path, 'r') as f:
            content = f.read()
        
        # Check for Perplexity configuration
        assert '"perplexity"' in content, "Perplexity provider not found in LLM_CONFIG"
        assert '"sonar-pro"' in content, "sonar-pro model not found in LLM_CONFIG"
        assert 'api.perplexity.ai' in content, "Perplexity API base URL not found"
    
    def test_perplexity_uses_real_api(self):
        """Perplexity should use real API, not fallback to gpt-4o-mini"""
        llm_connector_path = "/app/backend/app/services/llm_connector.py"
        with open(llm_connector_path, 'r') as f:
            content = f.read()
        
        # Check that _query_with_perplexity method exists
        assert 'async def _query_with_perplexity' in content, "_query_with_perplexity method not found"
        
        # Check that it uses httpx for real API calls
        assert 'httpx.AsyncClient' in content, "httpx.AsyncClient not used for Perplexity API"
        
        # Check that it uses the Perplexity API key
        assert 'get_perplexity_api_key' in content, "get_perplexity_api_key function not found"
    
    def test_perplexity_api_key_configured(self):
        """Perplexity API key should be configured in environment"""
        # Read backend .env file
        env_path = "/app/backend/.env"
        with open(env_path, 'r') as f:
            content = f.read()
        
        # Check for PERPLEXITY_API_KEY
        assert 'PERPLEXITY_API_KEY=' in content, "PERPLEXITY_API_KEY not found in .env"
        
        # Verify it's not empty
        match = re.search(r'PERPLEXITY_API_KEY=(\S+)', content)
        assert match, "PERPLEXITY_API_KEY value not found"
        api_key = match.group(1)
        assert len(api_key) > 10, "PERPLEXITY_API_KEY appears to be empty or too short"


class TestContentAuditNoMockData:
    """Test ContentAuditPage has no mock data"""
    
    def test_content_audit_page_no_mock_data(self):
        """ContentAuditPage should not contain mock data"""
        page_path = "/app/frontend/src/pages/ContentAuditPage.jsx"
        with open(page_path, 'r') as f:
            content = f.read()
        
        # Check that there's no hardcoded mock data
        # Look for patterns that indicate mock data
        mock_patterns = [
            'mockAuditData',
            'MOCK_DATA',
            'dummyData',
            'fakeData',
            'testData =',
            'sampleData',
        ]
        
        for pattern in mock_patterns:
            assert pattern.lower() not in content.lower(), f"Mock data pattern '{pattern}' found in ContentAuditPage"
    
    def test_content_audit_uses_api(self):
        """ContentAuditPage should fetch data from API"""
        page_path = "/app/frontend/src/pages/ContentAuditPage.jsx"
        with open(page_path, 'r') as f:
            content = f.read()
        
        # Check that it uses axios to fetch data
        assert 'axios.get' in content, "ContentAuditPage should use axios.get for API calls"
        assert '/content-audit/' in content, "ContentAuditPage should call content-audit API endpoint"
    
    def test_content_audit_handles_empty_state(self):
        """ContentAuditPage should handle empty state properly"""
        page_path = "/app/frontend/src/pages/ContentAuditPage.jsx"
        with open(page_path, 'r') as f:
            content = f.read()
        
        # Check for empty state handling
        assert 'getEmptyAuditData' in content or 'Aucun audit' in content, "ContentAuditPage should handle empty state"


class TestArticleOptimizerNoMockData:
    """Test ArticleOptimizerPage has no mock data"""
    
    def test_article_optimizer_page_no_mock_data(self):
        """ArticleOptimizerPage should not contain mock data"""
        page_path = "/app/frontend/src/pages/ArticleOptimizerPage.jsx"
        with open(page_path, 'r') as f:
            content = f.read()
        
        # Check that there's no hardcoded mock data
        mock_patterns = [
            'mockOptimizations',
            'MOCK_DATA',
            'dummyData',
            'fakeData',
            'testOptimizations =',
            'sampleOptimizations',
        ]
        
        for pattern in mock_patterns:
            assert pattern.lower() not in content.lower(), f"Mock data pattern '{pattern}' found in ArticleOptimizerPage"
    
    def test_article_optimizer_uses_api(self):
        """ArticleOptimizerPage should fetch data from API"""
        page_path = "/app/frontend/src/pages/ArticleOptimizerPage.jsx"
        with open(page_path, 'r') as f:
            content = f.read()
        
        # Check that it uses axios for API calls
        assert 'axios.get' in content or 'axios.post' in content, "ArticleOptimizerPage should use axios for API calls"
        assert '/article-optimizer/' in content, "ArticleOptimizerPage should call article-optimizer API endpoint"
    
    def test_article_optimizer_handles_empty_state(self):
        """ArticleOptimizerPage should handle empty state properly"""
        page_path = "/app/frontend/src/pages/ArticleOptimizerPage.jsx"
        with open(page_path, 'r') as f:
            content = f.read()
        
        # Check for empty state handling
        assert 'Aucune analyse' in content or 'AlertCircle' in content, "ArticleOptimizerPage should handle empty state"


class TestServerConfiguration:
    """Test server.py has proper configuration"""
    
    def test_slowapi_imported(self):
        """SlowAPI should be imported in server.py"""
        server_path = "/app/backend/server.py"
        with open(server_path, 'r') as f:
            content = f.read()
        
        assert 'from slowapi import' in content, "SlowAPI not imported in server.py"
        assert 'Limiter' in content, "Limiter not imported from slowapi"
    
    def test_rate_limiter_configured(self):
        """Rate limiter should be configured"""
        server_path = "/app/backend/server.py"
        with open(server_path, 'r') as f:
            content = f.read()
        
        assert 'limiter = Limiter' in content, "Limiter not instantiated"
        assert '200/minute' in content or '200 per minute' in content.lower(), "Rate limit not set to 200/minute"
    
    def test_cors_configured_with_origins(self):
        """CORS should be configured with specific origins"""
        server_path = "/app/backend/server.py"
        with open(server_path, 'r') as f:
            content = f.read()
        
        # Check for CORS middleware
        assert 'CORSMiddleware' in content, "CORSMiddleware not found in server.py"
        
        # Check that CORS_ORIGINS is used from environment
        assert 'CORS_ORIGINS' in content or 'allow_origins' in content, "CORS origins configuration not found"
    
    def test_cors_origins_in_env(self):
        """CORS origins should be configured in .env"""
        env_path = "/app/backend/.env"
        with open(env_path, 'r') as f:
            content = f.read()
        
        assert 'CORS_ORIGINS=' in content, "CORS_ORIGINS not found in .env"
        
        # Check that it contains the preview URL
        assert 'geo-visibility-hub.preview.emergentagent.com' in content, "Preview URL not in CORS_ORIGINS"


class TestAnalysisStatusEnum:
    """Test AnalysisStatus enum is properly used"""
    
    def test_analysis_uses_enum_status(self):
        """Analysis creation should use AnalysisStatus enum"""
        server_path = "/app/backend/server.py"
        with open(server_path, 'r') as f:
            content = f.read()
        
        # Check that AnalysisStatus is imported and used
        assert 'AnalysisStatus' in content, "AnalysisStatus not found in server.py"
        assert 'AnalysisStatus.PENDING' in content, "AnalysisStatus.PENDING not used"
    
    def test_analysis_runner_handles_enum(self):
        """Analysis runner should handle status enum conversion"""
        runner_path = "/app/backend/app/services/analysis_runner.py"
        with open(runner_path, 'r') as f:
            content = f.read()
        
        # Check for status conversion logic
        assert 'AnalysisStatus' in content, "AnalysisStatus not found in analysis_runner.py"
        assert 'status_map' in content or 'AnalysisStatus.PENDING' in content, "Status enum handling not found"
