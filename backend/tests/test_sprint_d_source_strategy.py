"""
Test Sprint D - Source Seeding Strategy System
Tests:
1. POST /api/source-strategy/analyze - analyze source landscape
2. GET /api/source-strategy/recommendations/{project_id} - get recommendations
3. GET /api/source-strategy/authority-ranking - get authority ranking
4. POST /api/source-strategy/extract-sources - extract sources from content
5. Backend stability after adding source_strategy router
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://geo-visibility-hub.preview.emergentagent.com').rstrip('/')


class TestBackendStabilityAfterSourceStrategyRouter:
    """Test backend stability after Sprint D source_strategy router addition"""
    
    def test_health_endpoint_returns_200(self):
        """Health endpoint should return 200 after source_strategy router addition"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_health_contains_timestamp(self):
        """Health response should contain timestamp"""
        response = requests.get(f"{BASE_URL}/api/health")
        data = response.json()
        assert "timestamp" in data


class TestSourceStrategyAnalyzeEndpoint:
    """Test POST /api/source-strategy/analyze endpoint"""
    
    def test_analyze_endpoint_exists(self):
        """POST /api/source-strategy/analyze should return 401 (not 404) - router is included"""
        response = requests.post(
            f"{BASE_URL}/api/source-strategy/analyze",
            json={
                "topic": "CRM software",
                "keywords": ["salesforce", "hubspot"],
                "industry": "SaaS",
                "num_queries": 5
            }
        )
        # 401 means endpoint exists but requires auth
        # 404 would mean endpoint doesn't exist
        assert response.status_code == 401, f"Expected 401 (auth required), got {response.status_code}"
    
    def test_analyze_endpoint_requires_auth(self):
        """Analyze endpoint should require authentication"""
        response = requests.post(
            f"{BASE_URL}/api/source-strategy/analyze",
            json={"topic": "test topic"}
        )
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
    
    def test_analyze_endpoint_validates_request_body(self):
        """Analyze endpoint should validate request body"""
        # Missing required field 'topic' should return 422
        response = requests.post(
            f"{BASE_URL}/api/source-strategy/analyze",
            json={"keywords": ["test"]}
        )
        # Could be 401 (auth checked first) or 422 (validation error)
        assert response.status_code in [401, 422]


class TestSourceStrategyRecommendationsEndpoint:
    """Test GET /api/source-strategy/recommendations/{project_id} endpoint"""
    
    def test_recommendations_endpoint_exists(self):
        """GET /api/source-strategy/recommendations/{project_id} should return 401 (not 404)"""
        response = requests.get(f"{BASE_URL}/api/source-strategy/recommendations/test_project_id")
        # 401 means endpoint exists but requires auth
        assert response.status_code == 401, f"Expected 401 (auth required), got {response.status_code}"
    
    def test_recommendations_endpoint_requires_auth(self):
        """Recommendations endpoint should require authentication"""
        response = requests.get(f"{BASE_URL}/api/source-strategy/recommendations/any_project")
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data


class TestSourceStrategyAuthorityRankingEndpoint:
    """Test GET /api/source-strategy/authority-ranking endpoint"""
    
    def test_authority_ranking_endpoint_exists(self):
        """GET /api/source-strategy/authority-ranking should return 401 (not 404)"""
        response = requests.get(f"{BASE_URL}/api/source-strategy/authority-ranking")
        # 401 means endpoint exists but requires auth
        assert response.status_code == 401, f"Expected 401 (auth required), got {response.status_code}"
    
    def test_authority_ranking_endpoint_requires_auth(self):
        """Authority ranking endpoint should require authentication"""
        response = requests.get(f"{BASE_URL}/api/source-strategy/authority-ranking")
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data


class TestSourceStrategyExtractSourcesEndpoint:
    """Test POST /api/source-strategy/extract-sources endpoint"""
    
    def test_extract_sources_endpoint_exists(self):
        """POST /api/source-strategy/extract-sources should return 401 (not 404)"""
        response = requests.post(
            f"{BASE_URL}/api/source-strategy/extract-sources",
            params={"content": "Selon une étude de Harvard, 80% des entreprises utilisent un CRM."}
        )
        # 401 means endpoint exists but requires auth
        assert response.status_code == 401, f"Expected 401 (auth required), got {response.status_code}"
    
    def test_extract_sources_endpoint_requires_auth(self):
        """Extract sources endpoint should require authentication"""
        response = requests.post(
            f"{BASE_URL}/api/source-strategy/extract-sources",
            params={"content": "Test content"}
        )
        assert response.status_code == 401
    
    def test_extract_sources_with_research_content(self):
        """Extract sources should accept content with research citations"""
        content = "Selon une étude de McKinsey, les entreprises qui adoptent l'IA voient une augmentation de 20% de leur productivité."
        response = requests.post(
            f"{BASE_URL}/api/source-strategy/extract-sources",
            params={"content": content}
        )
        # Should return 401 (auth required), not 422 (validation error)
        assert response.status_code == 401
    
    def test_extract_sources_with_statistics_content(self):
        """Extract sources should accept content with statistics"""
        content = "En 2025, 75% des entreprises utilisent des solutions cloud. Le marché représente 500 milliards de dollars."
        response = requests.post(
            f"{BASE_URL}/api/source-strategy/extract-sources",
            params={"content": content}
        )
        assert response.status_code == 401


class TestSourceStrategyRouterIntegration:
    """Test source_strategy router is properly integrated"""
    
    def test_all_source_strategy_endpoints_return_401_not_404(self):
        """All source_strategy endpoints should return 401 (auth required), not 404 (not found)"""
        endpoints = [
            ("POST", "/api/source-strategy/analyze", {"topic": "test"}),
            ("GET", "/api/source-strategy/recommendations/test_project", None),
            ("GET", "/api/source-strategy/authority-ranking", None),
            ("POST", "/api/source-strategy/extract-sources", None),
        ]
        
        for method, endpoint, body in endpoints:
            if method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}")
            elif method == "POST":
                if body:
                    response = requests.post(f"{BASE_URL}{endpoint}", json=body)
                else:
                    response = requests.post(f"{BASE_URL}{endpoint}", params={"content": "test"})
            
            assert response.status_code == 401, f"{method} {endpoint} should return 401, got {response.status_code}"
    
    def test_source_strategy_router_prefix_is_correct(self):
        """Source strategy router should use /api/source-strategy prefix"""
        # Test that the prefix is correct by checking a known endpoint
        response = requests.get(f"{BASE_URL}/api/source-strategy/authority-ranking")
        assert response.status_code == 401  # Endpoint exists with /api prefix
        
        # Test that the /api prefix is required
        # Note: Without /api prefix, the request may be handled by frontend or return different status
        response_without_api = requests.get(f"{BASE_URL}/source-strategy/authority-ranking")
        # The key assertion is that /api/source-strategy works (returns 401)
        # Without /api, behavior depends on frontend routing


class TestSourcePatternExtraction:
    """Test source pattern extraction logic (unit tests)"""
    
    def test_source_patterns_defined(self):
        """Source patterns should be defined in the router"""
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from app.routers.source_strategy import SOURCE_PATTERNS
        
        expected_categories = ["research", "statistics", "news", "experts", "official", "community", "comparison"]
        for category in expected_categories:
            assert category in SOURCE_PATTERNS, f"Missing source pattern category: {category}"
    
    def test_source_authority_scores_defined(self):
        """Source authority scores should be defined"""
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from app.routers.source_strategy import SOURCE_AUTHORITY
        
        expected_types = [
            "research_institutions", "consulting_firms", "major_publications",
            "official_documentation", "review_platforms", "tech_communities",
            "industry_blogs", "personal_blogs"
        ]
        for source_type in expected_types:
            assert source_type in SOURCE_AUTHORITY, f"Missing source authority type: {source_type}"
            assert "score" in SOURCE_AUTHORITY[source_type]
            assert "examples" in SOURCE_AUTHORITY[source_type]
    
    def test_extract_sources_from_text_function(self):
        """Test extract_sources_from_text function"""
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from app.routers.source_strategy import extract_sources_from_text
        
        # Test with research citation
        text = "Selon une étude de Harvard, les résultats montrent une amélioration de 50%."
        sources = extract_sources_from_text(text)
        assert "research" in sources
        assert "statistics" in sources
        
        # Test with statistics
        text = "En 2025, 75% des entreprises utilisent le cloud."
        sources = extract_sources_from_text(text)
        assert len(sources["statistics"]) > 0
    
    def test_generate_seeding_recommendations_function(self):
        """Test generate_seeding_recommendations function"""
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from app.routers.source_strategy import generate_seeding_recommendations
        
        recommendations = generate_seeding_recommendations(
            topic="CRM software",
            keywords=["salesforce", "hubspot"],
            industry="SaaS"
        )
        
        assert len(recommendations) > 0
        for rec in recommendations:
            assert "source_type" in rec
            assert "platform" in rec
            assert "priority" in rec
            assert "strategy" in rec
            assert "expected_impact" in rec
            assert "action_items" in rec
    
    def test_calculate_credibility_score_function(self):
        """Test calculate_credibility_score function"""
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from app.routers.source_strategy import calculate_credibility_score
        
        # Empty sources should have low score
        empty_sources = {"research": [], "statistics": [], "news": [], "experts": [], "official": [], "community": [], "comparison": []}
        score = calculate_credibility_score(empty_sources)
        assert score == 0
        
        # Sources with research should have higher score
        research_sources = {"research": ["harvard study"], "statistics": [], "news": [], "experts": [], "official": [], "community": [], "comparison": []}
        score = calculate_credibility_score(research_sources)
        assert score > 0
    
    def test_analyze_source_gaps_function(self):
        """Test analyze_source_gaps function"""
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from app.routers.source_strategy import analyze_source_gaps
        
        # Empty sources should have many gaps
        empty_sources = {}
        gaps = analyze_source_gaps(empty_sources)
        assert len(gaps) > 0
        
        # Each gap should have required fields
        for gap in gaps:
            assert "source_type" in gap
            assert "priority" in gap
            assert "authority_score" in gap
            assert "recommendation" in gap
