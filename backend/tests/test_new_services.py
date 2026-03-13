"""
Test suite for new refactored services: LLMConnector, GEOScoringEngine, CompetitiveIntelligenceEngine
Also tests Celery task imports (query_single_llm, run_full_analysis)
"""
import pytest
import sys
import os

# Add backend to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://optimize-visibility.preview.emergentagent.com').rstrip('/')


class TestServiceImports:
    """Test that all new services can be imported correctly"""
    
    def test_llm_connector_import(self):
        """Test LLMConnector service imports correctly"""
        from app.services.llm_connector import LLMConnector, llm_connector
        assert LLMConnector is not None
        assert llm_connector is not None
        assert isinstance(llm_connector, LLMConnector)
    
    def test_geo_scoring_engine_import(self):
        """Test GEOScoringEngine service imports correctly"""
        from app.services.geo_scoring import GEOScoringEngine, geo_scoring_engine
        assert GEOScoringEngine is not None
        assert geo_scoring_engine is not None
        assert isinstance(geo_scoring_engine, GEOScoringEngine)
    
    def test_competitive_intelligence_engine_import(self):
        """Test CompetitiveIntelligenceEngine service imports correctly"""
        from app.services.competitive_intelligence import CompetitiveIntelligenceEngine, competitive_intelligence_engine
        assert CompetitiveIntelligenceEngine is not None
        assert competitive_intelligence_engine is not None
        assert isinstance(competitive_intelligence_engine, CompetitiveIntelligenceEngine)


class TestCeleryTaskImports:
    """Test that Celery tasks can be imported correctly"""
    
    def test_query_single_llm_import(self):
        """Test query_single_llm task imports correctly"""
        from app.tasks.analysis_tasks import query_single_llm
        assert query_single_llm is not None
        # Verify it's a Celery task
        assert hasattr(query_single_llm, 'delay')
        assert hasattr(query_single_llm, 'apply_async')
    
    def test_run_full_analysis_import(self):
        """Test run_full_analysis task imports correctly"""
        from app.tasks.analysis_tasks import run_full_analysis
        assert run_full_analysis is not None
        # Verify it's a Celery task
        assert hasattr(run_full_analysis, 'delay')
        assert hasattr(run_full_analysis, 'apply_async')
    
    def test_check_scheduled_scans_task_import(self):
        """Test check_scheduled_scans_task imports correctly"""
        from app.tasks.analysis_tasks import check_scheduled_scans_task
        assert check_scheduled_scans_task is not None
        assert hasattr(check_scheduled_scans_task, 'delay')


class TestLLMConnectorMethods:
    """Test LLMConnector class methods and configuration"""
    
    def test_llm_config_contains_required_providers(self):
        """Test LLM_CONFIG has required providers"""
        from app.services.llm_connector import LLM_CONFIG
        assert "chatgpt" in LLM_CONFIG
        assert "claude" in LLM_CONFIG
        assert "gemini" in LLM_CONFIG
        assert "perplexity" in LLM_CONFIG
    
    def test_llm_config_has_correct_structure(self):
        """Test each LLM config has required fields"""
        from app.services.llm_connector import LLM_CONFIG
        for provider, config in LLM_CONFIG.items():
            assert "provider" in config, f"{provider} missing 'provider'"
            assert "model" in config, f"{provider} missing 'model'"
            assert "display_name" in config, f"{provider} missing 'display_name'"
    
    def test_llm_connector_initialization(self):
        """Test LLMConnector initializes with correct attributes"""
        from app.services.llm_connector import LLMConnector, GEO_SYSTEM_MESSAGE
        connector = LLMConnector()
        assert connector.api_key is not None
        assert connector.system_message == GEO_SYSTEM_MESSAGE
    
    def test_llm_connector_custom_initialization(self):
        """Test LLMConnector initializes with custom params"""
        from app.services.llm_connector import LLMConnector
        custom_message = "Custom system message"
        connector = LLMConnector(api_key="test_key", system_message=custom_message)
        assert connector.api_key == "test_key"
        assert connector.system_message == custom_message
    
    def test_analyze_response_method_exists(self):
        """Test _analyze_response method exists"""
        from app.services.llm_connector import LLMConnector
        connector = LLMConnector()
        assert hasattr(connector, '_analyze_response')
    
    def test_analyze_role_method_exists(self):
        """Test _analyze_role method exists"""
        from app.services.llm_connector import LLMConnector
        connector = LLMConnector()
        assert hasattr(connector, '_analyze_role')


class TestGEOScoringEngineMethods:
    """Test GEOScoringEngine class methods"""
    
    def test_calculate_stability_index_empty_input(self):
        """Test stability index with empty input returns default"""
        from app.services.geo_scoring import GEOScoringEngine
        engine = GEOScoringEngine()
        result = engine.calculate_stability_index([])
        assert result["stability_score"] == 100.0
        assert result["variance"] == 0.0
        assert result["status"] == "insufficient_data"
    
    def test_calculate_stability_index_single_result(self):
        """Test stability index with single result returns insufficient_data"""
        from app.services.geo_scoring import GEOScoringEngine
        engine = GEOScoringEngine()
        result = engine.calculate_stability_index([{"ai_type": "chatgpt", "brand_mentioned": True}])
        assert result["status"] == "insufficient_data"
    
    def test_calculate_stability_index_multiple_results(self):
        """Test stability index with multiple results calculates correctly"""
        from app.services.geo_scoring import GEOScoringEngine
        engine = GEOScoringEngine()
        
        results = [
            {"ai_type": "chatgpt", "brand_mentioned": True, "role": "top_recommendation", "role_score": 1.0},
            {"ai_type": "chatgpt", "brand_mentioned": True, "role": "top_recommendation", "role_score": 1.0},
            {"ai_type": "claude", "brand_mentioned": True, "role": "shortlist", "role_score": 0.85},
            {"ai_type": "claude", "brand_mentioned": True, "role": "shortlist", "role_score": 0.85},
        ]
        
        result = engine.calculate_stability_index(results)
        assert "stability_score" in result
        assert "per_ai_stability" in result
        assert result["total_runs_analyzed"] == 4
    
    def test_calculate_advanced_indices_empty_input(self):
        """Test advanced indices with empty input"""
        from app.services.geo_scoring import GEOScoringEngine
        engine = GEOScoringEngine()
        result = engine.calculate_advanced_indices([], "TestBrand", [])
        
        assert result["stability_index"] == 0.0
        assert result["dominance_index"] == 0.0
        assert result["trust_gap"] == 0.0
        assert result["opportunity_score"] == 0.0
    
    def test_calculate_rate_score_empty_input(self):
        """Test R.A.T.E. score with empty input returns zeros"""
        from app.services.geo_scoring import GEOScoringEngine
        engine = GEOScoringEngine()
        result = engine.calculate_rate_score([], {})
        
        assert result["relevance"] == 0
        assert result["authority"] == 0
        assert result["truthfulness"] == 0
        assert result["endorsement"] == 0
        assert result["total"] == 0
        assert result["grade"] == "F"
    
    def test_calculate_rate_score_with_responses(self):
        """Test R.A.T.E. score calculation with valid responses"""
        from app.services.geo_scoring import GEOScoringEngine
        engine = GEOScoringEngine()
        
        responses = [
            {
                "ai_type": "chatgpt",
                "brand_mentioned": True,
                "role": "top_recommendation",
                "role_score": 1.0,
                "position_ratio": 0.1,
                "credibility_score": 80,
                "conversion_score": 70,
                "hallucination_penalty": 0,
                "credibility_factors": ["numbers", "testimonials"]
            },
            {
                "ai_type": "claude",
                "brand_mentioned": True,
                "role": "shortlist",
                "role_score": 0.85,
                "position_ratio": 0.2,
                "credibility_score": 75,
                "conversion_score": 60,
                "hallucination_penalty": 0,
                "credibility_factors": ["facts"]
            }
        ]
        
        stability_data = {"stability_score": 90}
        result = engine.calculate_rate_score(responses, stability_data)
        
        assert "relevance" in result
        assert "authority" in result
        assert "truthfulness" in result
        assert "endorsement" in result
        assert "total" in result
        assert "grade" in result
        assert result["grade"] in ["A", "B", "C", "D", "F"]
    
    def test_calculate_ai_scores(self):
        """Test per-AI score calculation"""
        from app.services.geo_scoring import GEOScoringEngine
        engine = GEOScoringEngine()
        
        responses = [
            {"ai_type": "chatgpt", "brand_mentioned": True, "role": "top_recommendation", "role_score": 1.0},
            {"ai_type": "chatgpt", "brand_mentioned": True, "role": "shortlist", "role_score": 0.85},
            {"ai_type": "claude", "brand_mentioned": False, "role": "absent", "role_score": 0.0},
        ]
        
        result = engine.calculate_ai_scores(responses)
        assert "chatgpt" in result
        assert "claude" in result
        assert result["chatgpt"] > result["claude"]
    
    def test_generate_recommendations(self):
        """Test recommendations generation"""
        from app.services.geo_scoring import GEOScoringEngine
        engine = GEOScoringEngine()
        
        rate_score = {"total": 35, "relevance": 40, "authority": 30, "truthfulness": 50, "endorsement": 25}
        ai_scores = {"chatgpt": 60, "claude": 25}
        indices = {"opportunity_score": 70}
        stability_data = {"stability_score": 60}
        
        recommendations = engine.generate_recommendations(rate_score, ai_scores, indices, stability_data)
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        
        # Check first recommendation has required fields
        first_rec = recommendations[0]
        assert "priority" in first_rec
        assert "category" in first_rec
        assert "title" in first_rec
        assert "description" in first_rec
        assert "actions" in first_rec


class TestCompetitiveIntelligenceEngineMethods:
    """Test CompetitiveIntelligenceEngine class methods"""
    
    def test_identify_competitors_empty_input(self):
        """Test competitor identification with empty input"""
        from app.services.competitive_intelligence import CompetitiveIntelligenceEngine
        engine = CompetitiveIntelligenceEngine()
        result = engine.identify_competitors([], "TestBrand", [])
        
        assert isinstance(result, list)
        assert len(result) == 0
    
    def test_identify_competitors_with_known_brands(self):
        """Test competitor identification detects known brands"""
        from app.services.competitive_intelligence import CompetitiveIntelligenceEngine
        engine = CompetitiveIntelligenceEngine()
        
        responses = [
            {"response_excerpt": "Google and Microsoft are the leading tech companies. Apple also innovates."},
            {"response_excerpt": "Semrush and Ahrefs are popular SEO tools."}
        ]
        
        result = engine.identify_competitors(responses, "MyBrand", [])
        
        assert isinstance(result, list)
        # Should find at least some known brands
        brand_names = [c["name"] for c in result]
        # Check if any expected brands are found
        expected = ["Google", "Microsoft", "Apple", "Semrush", "Ahrefs"]
        found = any(b in brand_names for b in expected)
        assert found, f"Expected to find at least one of {expected} but got {brand_names}"
    
    def test_identify_competitors_excludes_own_brand(self):
        """Test that own brand is excluded from competitors"""
        from app.services.competitive_intelligence import CompetitiveIntelligenceEngine
        engine = CompetitiveIntelligenceEngine()
        
        responses = [
            {"response_excerpt": "TestBrand is great. Google and Microsoft are also good."}
        ]
        
        result = engine.identify_competitors(responses, "TestBrand", [])
        brand_names = [c["name"].lower() for c in result]
        
        assert "testbrand" not in brand_names
    
    def test_identify_competitors_tracks_user_defined(self):
        """Test user-defined competitors are tracked with user_defined=True"""
        from app.services.competitive_intelligence import CompetitiveIntelligenceEngine
        engine = CompetitiveIntelligenceEngine()
        
        # Note: The implementation uses lowercase matching (comp_lower in response_lower)
        # So we need to ensure the competitor names appear exactly in the response
        responses = [
            {"response_excerpt": "competitor1 and competitor2 are mentioned here as alternatives."}
        ]
        
        result = engine.identify_competitors(responses, "MyBrand", ["competitor1", "competitor2"])
        
        # Find user-defined competitors
        user_defined = [c for c in result if c.get("user_defined")]
        assert len(user_defined) >= 1
    
    def test_extract_potential_brands_method(self):
        """Test _extract_potential_brands extracts capitalized words"""
        from app.services.competitive_intelligence import CompetitiveIntelligenceEngine
        engine = CompetitiveIntelligenceEngine()
        
        text = "TechCorp and Acme Solutions are innovative companies."
        result = engine._extract_potential_brands(text)
        
        assert isinstance(result, list)
        # Should extract capitalized words
        assert "TechCorp" in result or "Acme" in result or "Solutions" in result
    
    def test_calculate_competitive_gap(self):
        """Test competitive gap calculation"""
        from app.services.competitive_intelligence import CompetitiveIntelligenceEngine
        engine = CompetitiveIntelligenceEngine()
        
        responses = [
            {"response_excerpt": "mybrand is great. competitor1 is also mentioned."},
            {"response_excerpt": "competitor1 leads the market. mybrand follows."},
            {"response_excerpt": "mybrand is the best choice."}
        ]
        
        result = engine.calculate_competitive_gap(responses, "mybrand", ["competitor1", "competitor2"])
        
        assert "brand_stats" in result
        assert "competitor_stats" in result
        assert "competitive_position" in result
        assert result["total_responses_analyzed"] == 3
    
    def test_generate_competitive_recommendations(self):
        """Test competitive recommendations generation"""
        from app.services.competitive_intelligence import CompetitiveIntelligenceEngine
        engine = CompetitiveIntelligenceEngine()
        
        gap_analysis = {
            "competitive_position": "at_risk",
            "threats": [
                {"competitor": "Rival1", "presence_rate": 80, "beat_rate": 60}
            ],
            "opportunities": [
                {"competitor": "WeakRival", "gap": 40}
            ]
        }
        
        recommendations = engine.generate_competitive_recommendations(gap_analysis, "MyBrand")
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0


class TestDBModuleImports:
    """Test database module imports"""
    
    def test_db_init_imports(self):
        """Test db/__init__.py imports correctly"""
        from app.db import USE_POSTGRES, initialize_database, shutdown_database
        assert USE_POSTGRES is not None
        assert initialize_database is not None
        assert shutdown_database is not None
    
    def test_use_postgres_is_boolean(self):
        """Test USE_POSTGRES is a boolean"""
        from app.db import USE_POSTGRES
        assert isinstance(USE_POSTGRES, bool)


class TestHealthEndpoint:
    """Test health check endpoint"""
    
    def test_health_endpoint_returns_200(self):
        """Test health endpoint returns 200"""
        import requests
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
    
    def test_health_endpoint_returns_healthy_status(self):
        """Test health endpoint returns healthy status"""
        import requests
        response = requests.get(f"{BASE_URL}/api/health")
        data = response.json()
        assert data.get("status") == "healthy"
    
    def test_health_endpoint_returns_timestamp(self):
        """Test health endpoint returns timestamp"""
        import requests
        response = requests.get(f"{BASE_URL}/api/health")
        data = response.json()
        assert "timestamp" in data


class TestAuthEndpoints:
    """Test authentication endpoints"""
    
    def test_auth_me_returns_401_without_session(self):
        """Test /api/auth/me returns 401 without authentication"""
        import requests
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
    
    def test_auth_me_error_message_is_french(self):
        """Test /api/auth/me returns French error message"""
        import requests
        response = requests.get(f"{BASE_URL}/api/auth/me")
        data = response.json()
        assert data.get("detail") == "Non authentifié"


class TestAnalysisQuotaEndpoint:
    """Test analysis quota endpoint"""
    
    def test_analysis_quota_returns_401_without_auth(self):
        """Test /api/analysis/quota returns 401 without authentication"""
        import requests
        response = requests.get(f"{BASE_URL}/api/analysis/quota")
        assert response.status_code == 401


class TestSubscriptionPlansEndpoint:
    """Test subscription plans endpoint (public)"""
    
    def test_subscription_plans_returns_200(self):
        """Test subscription plans endpoint returns 200"""
        import requests
        response = requests.get(f"{BASE_URL}/api/subscription/plans")
        assert response.status_code == 200
    
    def test_subscription_plans_contains_all_plans(self):
        """Test subscription plans contains free, starter, pro, business"""
        import requests
        response = requests.get(f"{BASE_URL}/api/subscription/plans")
        data = response.json()
        
        plans = data.get("plans", {})
        assert "free" in plans
        assert "starter" in plans
        assert "pro" in plans
        assert "business" in plans
    
    def test_subscription_plan_structure(self):
        """Test each plan has required structure"""
        import requests
        response = requests.get(f"{BASE_URL}/api/subscription/plans")
        data = response.json()
        
        plans = data.get("plans", {})
        for plan_name, plan_data in plans.items():
            assert "name" in plan_data, f"{plan_name} missing 'name'"
            assert "price" in plan_data, f"{plan_name} missing 'price'"
            assert "features" in plan_data, f"{plan_name} missing 'features'"
