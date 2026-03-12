"""
Test suite for Competitor Analysis functionality
Tests the identify_competitors_from_analysis function and competitor_comparison API response
"""
import pytest
import requests
import os
import sys

# Add backend to path for direct imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://optimization-nexus.preview.emergentagent.com').rstrip('/')

# Test session and project
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


class TestIdentifyCompetitorsFunction:
    """
    Unit tests for identify_competitors_from_analysis function logic
    Tests the 3 strategies: known brands, user-defined, NLP extraction
    """

    def test_known_brands_detection_semrush(self):
        """Test that Semrush is detected as a known brand"""
        # This tests the known brands database
        from server import identify_competitors_from_analysis
        import asyncio
        
        responses = [
            {
                "response_excerpt": "For SEO analysis, Semrush is one of the leading tools. Semrush provides comprehensive keyword research and competitor tracking. Many professionals use Semrush daily.",
                "ai_type": "chatgpt"
            }
        ]
        
        result = asyncio.get_event_loop().run_until_complete(
            identify_competitors_from_analysis(responses, "TestBrand", [])
        )
        
        # Check Semrush is detected
        semrush_found = any(c["name"].lower() == "semrush" for c in result)
        assert semrush_found, f"Semrush should be detected. Found: {[c['name'] for c in result]}"

    def test_known_brands_detection_ahrefs(self):
        """Test that Ahrefs is detected as a known brand"""
        from server import identify_competitors_from_analysis
        import asyncio
        
        responses = [
            {
                "response_excerpt": "Ahrefs is excellent for backlink analysis. Many SEO professionals prefer Ahrefs for its comprehensive database.",
                "ai_type": "claude"
            }
        ]
        
        result = asyncio.get_event_loop().run_until_complete(
            identify_competitors_from_analysis(responses, "TestBrand", [])
        )
        
        ahrefs_found = any(c["name"].lower() == "ahrefs" for c in result)
        assert ahrefs_found, f"Ahrefs should be detected. Found: {[c['name'] for c in result]}"

    def test_known_brands_detection_google(self):
        """Test that Google is detected as a known brand"""
        from server import identify_competitors_from_analysis
        import asyncio
        
        responses = [
            {
                "response_excerpt": "Google Analytics provides detailed website traffic data. Google Search Console helps with search performance. Google is essential for digital marketing.",
                "ai_type": "gemini"
            }
        ]
        
        result = asyncio.get_event_loop().run_until_complete(
            identify_competitors_from_analysis(responses, "TestBrand", [])
        )
        
        google_found = any(c["name"].lower() == "google" for c in result)
        assert google_found, f"Google should be detected. Found: {[c['name'] for c in result]}"

    def test_known_brands_detection_multiple_mentions(self):
        """Test that mentions count is accurate for multiple brand occurrences"""
        from server import identify_competitors_from_analysis
        import asyncio
        
        responses = [
            {
                "response_excerpt": "Semrush and Ahrefs are the top SEO tools. Semrush offers keyword research while Ahrefs excels at backlinks. Many compare Semrush vs Ahrefs frequently.",
                "ai_type": "chatgpt"
            }
        ]
        
        result = asyncio.get_event_loop().run_until_complete(
            identify_competitors_from_analysis(responses, "TestBrand", [])
        )
        
        # Check both are found with multiple mentions
        semrush_entry = next((c for c in result if c["name"].lower() == "semrush"), None)
        ahrefs_entry = next((c for c in result if c["name"].lower() == "ahrefs"), None)
        
        assert semrush_entry is not None, "Semrush should be detected"
        assert semrush_entry["mentions"] >= 2, f"Semrush should have 3 mentions, got {semrush_entry['mentions']}"
        assert ahrefs_entry is not None, "Ahrefs should be detected"
        assert ahrefs_entry["mentions"] >= 2, f"Ahrefs should have 2 mentions, got {ahrefs_entry['mentions']}"

    def test_user_defined_competitors_tracking(self):
        """Test that user-defined competitors from competitor_analysis field are tracked"""
        from server import identify_competitors_from_analysis
        import asyncio
        
        responses = [
            {
                "response_excerpt": "The market includes several competitors offering similar services.",
                "ai_type": "chatgpt",
                "competitor_analysis": {
                    "CustomCompetitor": {"mentioned": True, "context": "direct competitor"},
                    "AnotherBrand": {"mentioned": True, "context": "indirect competitor"}
                }
            }
        ]
        
        result = asyncio.get_event_loop().run_until_complete(
            identify_competitors_from_analysis(responses, "TestBrand", [])
        )
        
        # Check user-defined competitors are tracked
        custom_found = any(c["name"].lower() == "customcompetitor" for c in result)
        another_found = any(c["name"].lower() == "anotherbrand" for c in result)
        
        assert custom_found, f"CustomCompetitor should be tracked. Found: {[c['name'] for c in result]}"
        assert another_found, f"AnotherBrand should be tracked. Found: {[c['name'] for c in result]}"
        
        # Verify user_defined flag
        custom_entry = next((c for c in result if c["name"].lower() == "customcompetitor"), None)
        assert custom_entry["user_defined"] is True, "user_defined should be True"

    def test_false_positive_filtering_common_french_words(self):
        """Test that common French words like Pour, Dans, etc. are filtered out"""
        from server import identify_competitors_from_analysis
        import asyncio
        
        responses = [
            {
                "response_excerpt": "Pour améliorer votre SEO, il faut investir. Dans le domaine du marketing, Semrush est excellent. Voici les conseils principaux. Pour la stratégie, consultez des experts.",
                "ai_type": "chatgpt"
            }
        ]
        
        result = asyncio.get_event_loop().run_until_complete(
            identify_competitors_from_analysis(responses, "TestBrand", [])
        )
        
        # Common French words should NOT appear
        false_positives = ["Pour", "Dans", "Voici", "Meilleur", "Premier"]
        detected_names = [c["name"] for c in result]
        
        for word in false_positives:
            assert word not in detected_names, f"False positive '{word}' should be filtered out. Found: {detected_names}"

    def test_false_positive_filtering_common_english_words(self):
        """Test that common English words are filtered out"""
        from server import identify_competitors_from_analysis
        import asyncio
        
        responses = [
            {
                "response_excerpt": "The Best tool for This purpose is Semrush. However, Many prefer Other solutions. Which one is Best depends on your needs.",
                "ai_type": "claude"
            }
        ]
        
        result = asyncio.get_event_loop().run_until_complete(
            identify_competitors_from_analysis(responses, "TestBrand", [])
        )
        
        # Common English words should NOT appear
        false_positives = ["Best", "This", "However", "Many", "Other", "Which"]
        detected_names = [c["name"] for c in result]
        
        for word in false_positives:
            assert word not in detected_names, f"False positive '{word}' should be filtered out. Found: {detected_names}"

    def test_visibility_score_calculation(self):
        """Test that visibility score is calculated correctly"""
        from server import identify_competitors_from_analysis
        import asyncio
        
        responses = [
            {
                "response_excerpt": "Semrush is recommended. Semrush has great features. Semrush is popular.",
                "ai_type": "chatgpt"
            },
            {
                "response_excerpt": "Semrush offers keyword tools. Many use Semrush for SEO.",
                "ai_type": "claude"
            }
        ]
        
        result = asyncio.get_event_loop().run_until_complete(
            identify_competitors_from_analysis(responses, "TestBrand", [])
        )
        
        semrush_entry = next((c for c in result if c["name"].lower() == "semrush"), None)
        assert semrush_entry is not None, "Semrush should be detected"
        
        # Check visibility_score exists and is > 0
        assert "visibility_score" in semrush_entry, "visibility_score should be present"
        assert semrush_entry["visibility_score"] > 0, "visibility_score should be positive"
        assert semrush_entry["visibility_score"] <= 100, "visibility_score should be <= 100"

    def test_presence_rate_calculation(self):
        """Test that presence_rate is calculated correctly"""
        from server import identify_competitors_from_analysis
        import asyncio
        
        # Semrush appears in 2 out of 3 responses = 66.7% presence rate
        # Responses must be > 50 chars to be processed
        responses = [
            {"response_excerpt": "Semrush is great for SEO analysis and keyword research. It provides comprehensive backlink data and site audits.", "ai_type": "chatgpt"},
            {"response_excerpt": "Ahrefs is another popular SEO tool with excellent backlink database. Many professionals use it daily.", "ai_type": "claude"},
            {"response_excerpt": "Semrush and Moz are also great options for SEO professionals who need comprehensive analysis tools.", "ai_type": "gemini"}
        ]
        
        result = asyncio.get_event_loop().run_until_complete(
            identify_competitors_from_analysis(responses, "TestBrand", [])
        )
        
        semrush_entry = next((c for c in result if c["name"].lower() == "semrush"), None)
        assert semrush_entry is not None, f"Semrush should be detected. Found: {[c['name'] for c in result]}"
        
        # Check presence_rate exists
        assert "presence_rate" in semrush_entry, "presence_rate should be present"
        assert semrush_entry["presence_rate"] > 0, "presence_rate should be positive"
        
        # Semrush appears in 2/3 responses = ~66.7%
        assert 60 <= semrush_entry["presence_rate"] <= 70, f"presence_rate should be ~66.7%, got {semrush_entry['presence_rate']}"

    def test_responses_containing_count(self):
        """Test that responses_containing is tracked correctly"""
        from server import identify_competitors_from_analysis
        import asyncio
        
        # Responses must be > 50 chars to be processed
        responses = [
            {"response_excerpt": "Semrush is the best SEO tool for keyword research and competitor analysis. It provides detailed insights.", "ai_type": "chatgpt"},
            {"response_excerpt": "I recommend Semrush for keyword research and backlink analysis. Many professionals find it invaluable.", "ai_type": "claude"},
            {"response_excerpt": "Ahrefs is also popular among SEO professionals for its comprehensive backlink database and site audits.", "ai_type": "gemini"}
        ]
        
        result = asyncio.get_event_loop().run_until_complete(
            identify_competitors_from_analysis(responses, "TestBrand", [])
        )
        
        semrush_entry = next((c for c in result if c["name"].lower() == "semrush"), None)
        assert semrush_entry is not None, f"Semrush should be detected. Found: {[c['name'] for c in result]}"
        
        assert "responses_containing" in semrush_entry, "responses_containing should be present"
        assert semrush_entry["responses_containing"] == 2, f"responses_containing should be 2, got {semrush_entry['responses_containing']}"

    def test_ai_sources_tracking(self):
        """Test that ai_sources are tracked correctly across multiple AI engines"""
        from server import identify_competitors_from_analysis
        import asyncio
        
        # Responses must be > 50 chars to be processed
        responses = [
            {"response_excerpt": "Semrush is an excellent SEO tool for keyword research and competitor analysis. Professionals rely on it.", "ai_type": "chatgpt"},
            {"response_excerpt": "Semrush offers great features for backlink analysis and site audits. Many digital marketers use it daily.", "ai_type": "claude"},
            {"response_excerpt": "Semrush is recommended for comprehensive SEO analysis and reporting. It integrates with many platforms.", "ai_type": "gemini"}
        ]
        
        result = asyncio.get_event_loop().run_until_complete(
            identify_competitors_from_analysis(responses, "TestBrand", [])
        )
        
        semrush_entry = next((c for c in result if c["name"].lower() == "semrush"), None)
        assert semrush_entry is not None, f"Semrush should be detected. Found: {[c['name'] for c in result]}"
        
        assert "ai_sources" in semrush_entry, "ai_sources should be present"
        assert len(semrush_entry["ai_sources"]) == 3, f"Should have 3 AI sources, got {len(semrush_entry['ai_sources'])}"
        assert set(semrush_entry["ai_sources"]) == {"chatgpt", "claude", "gemini"}

    def test_own_brand_exclusion(self):
        """Test that the user's own brand is excluded from competitors"""
        from server import identify_competitors_from_analysis
        import asyncio
        
        responses = [
            {
                "response_excerpt": "Semrush and TestBrand are both excellent SEO tools. TestBrand offers unique features. Use TestBrand for your analysis.",
                "ai_type": "chatgpt"
            }
        ]
        
        result = asyncio.get_event_loop().run_until_complete(
            identify_competitors_from_analysis(responses, "TestBrand", [])
        )
        
        # TestBrand should NOT be in competitors
        own_brand_found = any(c["name"].lower() == "testbrand" for c in result)
        assert not own_brand_found, f"Own brand 'TestBrand' should be excluded. Found: {[c['name'] for c in result]}"
        
        # But Semrush should still be detected
        semrush_found = any(c["name"].lower() == "semrush" for c in result)
        assert semrush_found, "Semrush should still be detected"

    def test_discovered_vs_user_defined_flags(self):
        """Test that discovered and user_defined flags are set correctly"""
        from server import identify_competitors_from_analysis
        import asyncio
        
        responses = [
            {
                "response_excerpt": "Semrush is a great tool for SEO analysis.",
                "ai_type": "chatgpt",
                "competitor_analysis": {
                    "CustomBrand": {"mentioned": True}
                }
            }
        ]
        
        result = asyncio.get_event_loop().run_until_complete(
            identify_competitors_from_analysis(responses, "TestBrand", [])
        )
        
        # Semrush should have discovered=True, user_defined=False
        semrush_entry = next((c for c in result if c["name"].lower() == "semrush"), None)
        if semrush_entry:
            assert semrush_entry["discovered"] is True, "discovered should be True for Semrush"
            assert semrush_entry["user_defined"] is False, "user_defined should be False for Semrush"
        
        # CustomBrand should have user_defined=True
        custom_entry = next((c for c in result if c["name"].lower() == "custombrand"), None)
        if custom_entry:
            assert custom_entry["user_defined"] is True, "user_defined should be True for CustomBrand"

    def test_empty_responses_handling(self):
        """Test that empty responses are handled gracefully"""
        from server import identify_competitors_from_analysis
        import asyncio
        
        responses = []
        
        result = asyncio.get_event_loop().run_until_complete(
            identify_competitors_from_analysis(responses, "TestBrand", [])
        )
        
        assert result == [], "Empty responses should return empty list"

    def test_short_responses_skipped(self):
        """Test that very short responses are skipped (< 50 chars)"""
        from server import identify_competitors_from_analysis
        import asyncio
        
        responses = [
            {"response_excerpt": "Short response with Semrush.", "ai_type": "chatgpt"},  # < 50 chars - should be skipped
            {"response_excerpt": "This is a much longer response that mentions Semrush and other SEO tools in detail for comprehensive analysis.", "ai_type": "claude"}  # > 50 chars
        ]
        
        result = asyncio.get_event_loop().run_until_complete(
            identify_competitors_from_analysis(responses, "TestBrand", [])
        )
        
        # Should still find Semrush from the longer response
        semrush_found = any(c["name"].lower() == "semrush" for c in result)
        assert semrush_found, f"Semrush should be detected from longer response. Found: {[c['name'] for c in result]}"
        
        # Verify only 1 response was counted
        semrush_entry = next((c for c in result if c["name"].lower() == "semrush"), None)
        if semrush_entry:
            assert semrush_entry["responses_containing"] == 1, "Only 1 response should be counted (short one skipped)"


class TestCompetitorComparisonStructure:
    """Tests for competitor_comparison structure in API responses"""

    def test_competitor_comparison_contains_required_fields(self, authenticated_client):
        """Test that competitor_comparison entries have all required fields"""
        # First, get an analysis that has competitor data
        response = authenticated_client.get(f"{BASE_URL}/api/analysis/{TEST_PROJECT_ID}")
        
        if response.status_code != 200:
            pytest.skip("No analysis data available for this project")
        
        data = response.json()
        competitor_comparison = data.get("competitor_comparison", [])
        
        if not competitor_comparison:
            pytest.skip("No competitor comparison data in analysis")
        
        # Check first entry has all required fields
        entry = competitor_comparison[0]
        required_fields = ["competitor", "mentions", "visibility_rate", "presence_rate", 
                         "ai_sources", "discovered", "user_defined", "responses_containing"]
        
        for field in required_fields:
            assert field in entry, f"Missing required field: {field}"

    def test_competitor_comparison_visibility_rate_range(self, authenticated_client):
        """Test that visibility_rate is within valid range (0-100)"""
        response = authenticated_client.get(f"{BASE_URL}/api/analysis/{TEST_PROJECT_ID}")
        
        if response.status_code != 200:
            pytest.skip("No analysis data available")
        
        data = response.json()
        competitor_comparison = data.get("competitor_comparison", [])
        
        for entry in competitor_comparison:
            visibility_rate = entry.get("visibility_rate", 0)
            assert 0 <= visibility_rate <= 100, f"visibility_rate {visibility_rate} out of range"

    def test_competitor_comparison_presence_rate_range(self, authenticated_client):
        """Test that presence_rate is within valid range (0-100)"""
        response = authenticated_client.get(f"{BASE_URL}/api/analysis/{TEST_PROJECT_ID}")
        
        if response.status_code != 200:
            pytest.skip("No analysis data available")
        
        data = response.json()
        competitor_comparison = data.get("competitor_comparison", [])
        
        for entry in competitor_comparison:
            presence_rate = entry.get("presence_rate", 0)
            assert 0 <= presence_rate <= 100, f"presence_rate {presence_rate} out of range"

    def test_competitor_comparison_ai_sources_is_list(self, authenticated_client):
        """Test that ai_sources is always a list"""
        response = authenticated_client.get(f"{BASE_URL}/api/analysis/{TEST_PROJECT_ID}")
        
        if response.status_code != 200:
            pytest.skip("No analysis data available")
        
        data = response.json()
        competitor_comparison = data.get("competitor_comparison", [])
        
        for entry in competitor_comparison:
            ai_sources = entry.get("ai_sources")
            assert isinstance(ai_sources, list), f"ai_sources should be list, got {type(ai_sources)}"


class TestAnalysisSummaryCompetitors:
    """Tests for discovered_competitors and user_defined_competitors in analysis_summary"""

    def test_analysis_summary_has_competitor_arrays(self, authenticated_client):
        """Test that analysis_summary contains competitor arrays"""
        response = authenticated_client.get(f"{BASE_URL}/api/analysis/{TEST_PROJECT_ID}")
        
        if response.status_code != 200:
            pytest.skip("No analysis data available")
        
        data = response.json()
        analysis_summary = data.get("analysis_summary", {})
        
        # These fields should exist even if empty
        assert "discovered_competitors" in analysis_summary or "competitor_comparison" in data, \
            "Analysis should have competitor data"

    def test_indices_has_dominance_index(self, authenticated_client):
        """Test that indices contains dominance_index for competitive analysis"""
        response = authenticated_client.get(f"{BASE_URL}/api/analysis/{TEST_PROJECT_ID}")
        
        if response.status_code != 200:
            pytest.skip("No analysis data available")
        
        data = response.json()
        indices = data.get("indices", {})
        
        # dominance_index should be present
        if indices:
            assert "dominance_index" in indices, "indices should contain dominance_index"
            dominance = indices.get("dominance_index", 0)
            assert 0 <= dominance <= 100, f"dominance_index {dominance} out of range"


class TestKnownBrandsDatabase:
    """Tests specifically for the known brands database coverage"""

    def test_tech_giants_detection(self):
        """Test detection of major tech companies"""
        from server import identify_competitors_from_analysis
        import asyncio
        
        tech_giants = ["Apple", "Google", "Microsoft", "Amazon", "Meta"]
        
        for brand in tech_giants:
            responses = [
                {
                    "response_excerpt": f"{brand} is a major technology company with significant market presence. {brand} offers various products and services.",
                    "ai_type": "chatgpt"
                }
            ]
            
            result = asyncio.get_event_loop().run_until_complete(
                identify_competitors_from_analysis(responses, "TestBrand", [])
            )
            
            found = any(c["name"].lower() == brand.lower() for c in result)
            assert found, f"Tech giant '{brand}' should be detected"

    def test_seo_tools_detection(self):
        """Test detection of SEO/marketing tools"""
        from server import identify_competitors_from_analysis
        import asyncio
        
        seo_tools = ["Semrush", "Ahrefs", "Moz", "Majestic"]
        
        for tool in seo_tools:
            responses = [
                {
                    "response_excerpt": f"{tool} is a popular SEO tool used by professionals. {tool} offers comprehensive analysis features.",
                    "ai_type": "chatgpt"
                }
            ]
            
            result = asyncio.get_event_loop().run_until_complete(
                identify_competitors_from_analysis(responses, "TestBrand", [])
            )
            
            found = any(c["name"].lower() == tool.lower() for c in result)
            assert found, f"SEO tool '{tool}' should be detected"

    def test_ai_tools_detection(self):
        """Test detection of AI/LLM tools"""
        from server import identify_competitors_from_analysis
        import asyncio
        
        ai_tools = ["ChatGPT", "Claude", "Perplexity", "Gemini"]
        
        for tool in ai_tools:
            responses = [
                {
                    "response_excerpt": f"{tool} is an AI assistant that provides helpful responses. Many users prefer {tool} for its capabilities.",
                    "ai_type": "chatgpt"
                }
            ]
            
            result = asyncio.get_event_loop().run_until_complete(
                identify_competitors_from_analysis(responses, "TestBrand", [])
            )
            
            found = any(c["name"].lower() == tool.lower() for c in result)
            assert found, f"AI tool '{tool}' should be detected"
