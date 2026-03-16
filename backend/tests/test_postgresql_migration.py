"""
Test suite for PostgreSQL migration and AnalysisPipelineService
Verifies:
1. PostgreSQL connection and health
2. AnalysisPipelineService imports and functionality
3. Updated Celery tasks with AnalysisPipelineService
4. API endpoints working with PostgreSQL
"""
import pytest
import requests
import os
import sys
import asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://geo-visibility-hub.preview.emergentagent.com').rstrip('/')


class TestPostgreSQLConnection:
    """Test PostgreSQL database connection and configuration"""
    
    def test_use_postgres_env_is_true(self):
        """Test USE_POSTGRES environment variable is enabled"""
        from app.db import USE_POSTGRES
        assert USE_POSTGRES is True, "USE_POSTGRES should be True for PostgreSQL migration"
    
    def test_database_url_is_postgresql(self):
        """Test DATABASE_URL points to PostgreSQL"""
        from app.db.database import ASYNC_DATABASE_URL
        assert ASYNC_DATABASE_URL.startswith("postgresql+asyncpg://"), \
            f"Expected PostgreSQL URL, got: {ASYNC_DATABASE_URL[:30]}"
    
    def test_async_session_maker_exists(self):
        """Test async_session_maker is properly configured"""
        from app.db.database import async_session_maker
        assert async_session_maker is not None, "async_session_maker should be configured"
    
    def test_engine_is_configured(self):
        """Test SQLAlchemy engine is configured"""
        from app.db.database import engine
        assert engine is not None, "engine should be configured"
    
    def test_database_connection_works(self):
        """Test actual database connection"""
        from app.db.database import async_session_maker
        from sqlalchemy import text
        
        async def check_connection():
            async with async_session_maker() as session:
                result = await session.execute(text("SELECT 1"))
                return result.scalar()
        
        result = asyncio.run(check_connection())
        assert result == 1, "Database connection should work"
    
    def test_postgresql_version(self):
        """Test PostgreSQL version is returned"""
        from app.db.database import async_session_maker
        from sqlalchemy import text
        
        async def get_version():
            async with async_session_maker() as session:
                result = await session.execute(text("SELECT version()"))
                return result.scalar()
        
        version = asyncio.run(get_version())
        assert "PostgreSQL" in version, f"Expected PostgreSQL, got: {version[:50]}"
    
    def test_expected_tables_exist(self):
        """Test all expected tables exist in PostgreSQL"""
        from app.db.database import async_session_maker
        from sqlalchemy import text
        
        expected_tables = [
            'users', 'user_sessions', 'subscriptions', 'projects', 
            'analyses', 'notifications', 'scan_schedules', 'organizations'
        ]
        
        async def get_tables():
            async with async_session_maker() as session:
                result = await session.execute(
                    text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
                )
                return [row[0] for row in result.fetchall()]
        
        tables = asyncio.run(get_tables())
        for expected in expected_tables:
            assert expected in tables, f"Expected table {expected} not found. Got: {tables}"


class TestAnalysisPipelineServiceImport:
    """Test AnalysisPipelineService imports and initialization"""
    
    def test_analysis_pipeline_service_import(self):
        """Test AnalysisPipelineService imports correctly"""
        from app.services.analysis_pipeline import AnalysisPipelineService, analysis_pipeline
        assert AnalysisPipelineService is not None
        assert analysis_pipeline is not None
        assert isinstance(analysis_pipeline, AnalysisPipelineService)
    
    def test_analysis_pipeline_has_required_components(self):
        """Test AnalysisPipelineService has all required component references"""
        from app.services.analysis_pipeline import analysis_pipeline
        
        assert hasattr(analysis_pipeline, 'llm_connector')
        assert hasattr(analysis_pipeline, 'geo_scoring')
        assert hasattr(analysis_pipeline, 'competitive_intel')
        assert hasattr(analysis_pipeline, 'query_generator')
        assert hasattr(analysis_pipeline, 'variation_engine')
        assert hasattr(analysis_pipeline, 'semantic_analyzer')
        assert hasattr(analysis_pipeline, 'gap_finder')
    
    def test_analysis_pipeline_has_run_full_analysis_method(self):
        """Test AnalysisPipelineService has run_full_analysis method"""
        from app.services.analysis_pipeline import analysis_pipeline
        assert hasattr(analysis_pipeline, 'run_full_analysis')
        assert callable(getattr(analysis_pipeline, 'run_full_analysis'))
    
    def test_query_type_distribution_defined(self):
        """Test QUERY_TYPE_DISTRIBUTION is properly defined"""
        from app.services.analysis_pipeline import QUERY_TYPE_DISTRIBUTION
        
        expected_types = ['transactional', 'comparative', 'informational', 'local', 'recommendation', 'review']
        for qtype in expected_types:
            assert qtype in QUERY_TYPE_DISTRIBUTION, f"Missing query type: {qtype}"
        
        # Verify distribution sums to 1.0
        total = sum(QUERY_TYPE_DISTRIBUTION.values())
        assert abs(total - 1.0) < 0.01, f"Distribution should sum to 1.0, got {total}"


class TestAnalysisPipelineServiceMethods:
    """Test AnalysisPipelineService internal methods"""
    
    def test_generate_brand_variants(self):
        """Test _generate_brand_variants method"""
        from app.services.analysis_pipeline import AnalysisPipelineService
        service = AnalysisPipelineService()
        
        variants = service._generate_brand_variants("TestBrand", ["Product1", "Product2"])
        
        assert "TestBrand" in variants, "Original brand should be in variants"
        assert "testbrand" in variants, "Lowercase variant should be present"
        assert "TESTBRAND" in variants, "Uppercase variant should be present"
    
    def test_generate_brand_variants_with_spaces(self):
        """Test brand variant generation with spaces/hyphens"""
        from app.services.analysis_pipeline import AnalysisPipelineService
        service = AnalysisPipelineService()
        
        variants = service._generate_brand_variants("Test Brand", [])
        
        # Should include version without space
        assert "TestBrand" in variants, "No-space variant should be included"
        # Should include abbreviation for multi-word
        assert "TB" in variants, "Abbreviation should be included for multi-word brand"
    
    def test_detect_brand_mentions_advanced_empty(self):
        """Test _detect_brand_mentions_advanced with empty response"""
        from app.services.analysis_pipeline import AnalysisPipelineService
        service = AnalysisPipelineService()
        
        result = service._detect_brand_mentions_advanced("", "Brand", ["Brand"])
        
        assert result["total_mentions"] == 0
        assert result["mention_quality"] == "absent"
    
    def test_detect_brand_mentions_advanced_exact_match(self):
        """Test _detect_brand_mentions_advanced with exact brand match"""
        from app.services.analysis_pipeline import AnalysisPipelineService
        service = AnalysisPipelineService()
        
        response = "TestBrand is a great solution. TestBrand offers many features."
        result = service._detect_brand_mentions_advanced(response, "TestBrand", ["TestBrand", "testbrand"])
        
        assert result["total_mentions"] >= 2
        assert result["mention_quality"] == "exact"
    
    def test_generate_queries_multi_dimension(self):
        """Test _generate_queries_multi_dimension generates correct query count"""
        from app.services.analysis_pipeline import AnalysisPipelineService
        service = AnalysisPipelineService()
        
        queries = service._generate_queries_multi_dimension(
            brand_name="TestBrand",
            keywords=["keyword1", "keyword2"],
            competitors=["Competitor1"],
            num_queries=10
        )
        
        assert len(queries) == 10, f"Expected 10 queries, got {len(queries)}"
        
        # Verify each query has required fields
        for query in queries:
            assert "text" in query
            assert "type" in query
            assert "keyword" in query
    
    def test_generate_queries_has_all_types(self):
        """Test generated queries include all query types"""
        from app.services.analysis_pipeline import AnalysisPipelineService, QUERY_TYPE_DISTRIBUTION
        service = AnalysisPipelineService()
        
        queries = service._generate_queries_multi_dimension(
            brand_name="TestBrand",
            keywords=["keyword1"],
            competitors=["Competitor1"],
            num_queries=30  # Large enough to include all types
        )
        
        query_types = set(q["type"] for q in queries)
        
        # Should include most types
        assert len(query_types) >= 4, f"Expected at least 4 query types, got {len(query_types)}: {query_types}"
    
    def test_analyze_query_types(self):
        """Test _analyze_query_types method"""
        from app.services.analysis_pipeline import AnalysisPipelineService
        service = AnalysisPipelineService()
        
        query_results = [
            {"query_type": "transactional", "avg_score": 75, "mention_rate": 50},
            {"query_type": "transactional", "avg_score": 80, "mention_rate": 60},
            {"query_type": "comparative", "avg_score": 70, "mention_rate": 40},
        ]
        
        breakdown = service._analyze_query_types(query_results)
        
        assert "transactional" in breakdown
        assert breakdown["transactional"]["count"] == 2
        assert "comparative" in breakdown
        assert breakdown["comparative"]["count"] == 1
    
    def test_build_competitor_comparison(self):
        """Test _build_competitor_comparison method"""
        from app.services.analysis_pipeline import AnalysisPipelineService
        service = AnalysisPipelineService()
        
        discovered = [
            {"name": "Competitor1", "mentions": 5, "visibility_score": 80, "ai_sources": ["chatgpt"]},
            {"name": "Competitor2", "mentions": 3, "visibility_score": 60, "ai_sources": ["claude"]},
        ]
        user_competitors = ["Competitor1", "Competitor3"]
        
        comparison = service._build_competitor_comparison(discovered, user_competitors)
        
        assert len(comparison) >= 2
        # Competitor1 should be from discovered
        comp1 = next(c for c in comparison if c["competitor"] == "Competitor1")
        assert comp1["mentions"] == 5
        # Competitor3 should be added as user-defined but not discovered
        comp3 = next((c for c in comparison if c["competitor"] == "Competitor3"), None)
        assert comp3 is not None
        assert comp3["user_defined"] is True
        assert comp3["discovered"] is False


class TestCeleryTasksWithAnalysisPipeline:
    """Test Celery tasks using AnalysisPipelineService"""
    
    def test_run_full_analysis_task_imports_pipeline(self):
        """Test run_full_analysis task imports AnalysisPipelineService"""
        from app.tasks.analysis_tasks import run_full_analysis, analysis_pipeline
        
        assert run_full_analysis is not None
        assert hasattr(run_full_analysis, 'delay')
        assert analysis_pipeline is not None
    
    def test_task_uses_correct_service_instances(self):
        """Test tasks use correct service instances"""
        from app.tasks.analysis_tasks import llm_connector, geo_scoring, competitive_intel
        from app.services.llm_connector import LLMConnector
        from app.services.geo_scoring import GEOScoringEngine
        from app.services.competitive_intelligence import CompetitiveIntelligenceEngine
        
        assert isinstance(llm_connector, LLMConnector)
        assert isinstance(geo_scoring, GEOScoringEngine)
        assert isinstance(competitive_intel, CompetitiveIntelligenceEngine)
    
    def test_query_single_llm_task_exists(self):
        """Test query_single_llm task is defined"""
        from app.tasks.analysis_tasks import query_single_llm
        
        assert query_single_llm is not None
        assert hasattr(query_single_llm, 'delay')
        assert hasattr(query_single_llm, 'max_retries')
    
    def test_query_all_llms_task_exists(self):
        """Test query_all_llms_task is defined"""
        from app.tasks.analysis_tasks import query_all_llms_task
        
        assert query_all_llms_task is not None
        assert hasattr(query_all_llms_task, 'delay')


class TestDBServicesImport:
    """Test database services import correctly"""
    
    def test_user_service_import(self):
        """Test UserService imports from db module"""
        from app.db import UserService
        assert UserService is not None
    
    def test_project_service_import(self):
        """Test ProjectService imports from db module"""
        from app.db import ProjectService
        assert ProjectService is not None
    
    def test_analysis_service_import(self):
        """Test AnalysisService imports from db module"""
        from app.db import AnalysisService
        assert AnalysisService is not None
    
    def test_subscription_service_import(self):
        """Test SubscriptionService imports from db module"""
        from app.db import SubscriptionService
        assert SubscriptionService is not None
    
    def test_notification_service_import(self):
        """Test NotificationService imports from db module"""
        from app.db import NotificationService
        assert NotificationService is not None
    
    def test_schedule_service_import(self):
        """Test ScheduleService imports from db module"""
        from app.db import ScheduleService
        assert ScheduleService is not None


class TestAPIEndpointsWithPostgreSQL:
    """Test API endpoints work correctly with PostgreSQL backend"""
    
    def test_health_endpoint_is_healthy(self):
        """Test /api/health returns healthy status"""
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    def test_subscription_plans_endpoint_works(self):
        """Test /api/subscription/plans returns all plans"""
        response = requests.get(f"{BASE_URL}/api/subscription/plans", timeout=10)
        assert response.status_code == 200
        
        data = response.json()
        assert "plans" in data
        plans = data["plans"]
        
        expected_plans = ["free", "starter", "pro", "business"]
        for plan in expected_plans:
            assert plan in plans, f"Missing plan: {plan}"
    
    def test_auth_me_requires_authentication(self):
        """Test /api/auth/me returns 401 without auth"""
        response = requests.get(f"{BASE_URL}/api/auth/me", timeout=10)
        assert response.status_code == 401
    
    def test_analysis_quota_requires_authentication(self):
        """Test /api/analysis/quota returns 401 without auth"""
        response = requests.get(f"{BASE_URL}/api/analysis/quota", timeout=10)
        assert response.status_code == 401
    
    def test_projects_endpoint_requires_auth(self):
        """Test /api/projects requires authentication"""
        response = requests.get(f"{BASE_URL}/api/projects", timeout=10)
        assert response.status_code == 401


class TestGEOScoringWithPipeline:
    """Test GEO scoring integration with pipeline"""
    
    def test_scoring_engine_in_pipeline(self):
        """Test GEOScoringEngine is properly integrated in pipeline"""
        from app.services.analysis_pipeline import analysis_pipeline
        from app.services.geo_scoring import GEOScoringEngine
        
        assert isinstance(analysis_pipeline.geo_scoring, GEOScoringEngine)
    
    def test_calculate_stability_with_pipeline_responses(self):
        """Test stability calculation with pipeline-style responses"""
        from app.services.analysis_pipeline import analysis_pipeline
        
        # Simulate responses from pipeline
        responses = [
            {"ai_type": "chatgpt", "brand_mentioned": True, "role": "top_recommendation", "role_score": 1.0, "run_id": 1},
            {"ai_type": "chatgpt", "brand_mentioned": True, "role": "top_recommendation", "role_score": 0.95, "run_id": 2},
            {"ai_type": "claude", "brand_mentioned": True, "role": "shortlist", "role_score": 0.85, "run_id": 1},
            {"ai_type": "claude", "brand_mentioned": False, "role": "absent", "role_score": 0.0, "run_id": 2},
        ]
        
        stability = analysis_pipeline.geo_scoring.calculate_stability_index(responses)
        
        assert "stability_score" in stability
        assert "per_ai_stability" in stability
        assert "chatgpt" in stability["per_ai_stability"]
        assert "claude" in stability["per_ai_stability"]


class TestCompetitiveIntelligenceWithPipeline:
    """Test competitive intelligence integration with pipeline"""
    
    def test_competitive_intel_in_pipeline(self):
        """Test CompetitiveIntelligenceEngine is integrated in pipeline"""
        from app.services.analysis_pipeline import analysis_pipeline
        from app.services.competitive_intelligence import CompetitiveIntelligenceEngine
        
        assert isinstance(analysis_pipeline.competitive_intel, CompetitiveIntelligenceEngine)
    
    def test_identify_competitors_integration(self):
        """Test competitor identification through pipeline"""
        from app.services.analysis_pipeline import analysis_pipeline
        
        responses = [
            {"response_excerpt": "Google and Microsoft are leading cloud providers. Amazon AWS is also popular.", "ai_type": "chatgpt"},
            {"response_excerpt": "For search, Google dominates while Microsoft Bing is growing.", "ai_type": "claude"},
        ]
        
        competitors = analysis_pipeline.competitive_intel.identify_competitors(
            responses, "TestBrand", ["Google", "Microsoft"]
        )
        
        assert len(competitors) > 0
        competitor_names = [c["name"] for c in competitors]
        assert "Google" in competitor_names or "Microsoft" in competitor_names


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
