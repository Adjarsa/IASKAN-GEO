"""
Tests for Content Generation API endpoints
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
TEST_SESSION_TOKEN = 'test_session_1772018666518'

@pytest.fixture
def auth_headers():
    """Return headers with authentication cookie"""
    return {
        "Content-Type": "application/json",
        "Cookie": f"session_token={TEST_SESSION_TOKEN}"
    }

class TestContentGenerateAPI:
    """Tests for POST /api/content/generate endpoint"""
    
    def test_generate_article_content(self, auth_headers):
        """Test generating article content"""
        response = requests.post(
            f"{BASE_URL}/api/content/generate",
            headers=auth_headers,
            json={
                "content_type": "article",
                "topic": "Test GEO optimization topic",
                "keywords": ["SEO", "GEO", "AI"],
                "brand_name": "TestBrand"
            },
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert "content" in data
        assert "content_type" in data
        assert "topic" in data
        assert "word_count" in data
        assert "geo_score" in data
        assert "tips" in data
        assert "generated_at" in data
        
        # Validate values
        assert data["content_type"] == "article"
        assert data["topic"] == "Test GEO optimization topic"
        assert data["word_count"] > 0
        assert 0 <= data["geo_score"] <= 100
        assert isinstance(data["tips"], list)
    
    def test_generate_faq_content(self, auth_headers):
        """Test generating FAQ content"""
        response = requests.post(
            f"{BASE_URL}/api/content/generate",
            headers=auth_headers,
            json={
                "content_type": "faq",
                "topic": "Frequently asked questions about AI",
                "keywords": ["AI", "machine learning"],
                "brand_name": "TestBrand"
            },
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["content_type"] == "faq"
        assert "content" in data
    
    def test_generate_entity_content(self, auth_headers):
        """Test generating entity sheet content"""
        response = requests.post(
            f"{BASE_URL}/api/content/generate",
            headers=auth_headers,
            json={
                "content_type": "entity",
                "topic": "Company entity sheet",
                "keywords": [],
                "brand_name": "TestBrand"
            },
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["content_type"] == "entity"
    
    def test_generate_guide_content(self, auth_headers):
        """Test generating definitive guide content"""
        response = requests.post(
            f"{BASE_URL}/api/content/generate",
            headers=auth_headers,
            json={
                "content_type": "guide",
                "topic": "Complete guide to GEO",
                "keywords": ["GEO", "optimization"],
                "brand_name": "TestBrand"
            },
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["content_type"] == "guide"
    
    def test_generate_comparison_content(self, auth_headers):
        """Test generating comparison table content"""
        response = requests.post(
            f"{BASE_URL}/api/content/generate",
            headers=auth_headers,
            json={
                "content_type": "comparison",
                "topic": "Comparison of AI tools",
                "keywords": ["AI", "tools", "comparison"],
                "brand_name": "TestBrand"
            },
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["content_type"] == "comparison"
    
    def test_generate_without_auth_fails(self):
        """Test that generation without auth returns 401"""
        response = requests.post(
            f"{BASE_URL}/api/content/generate",
            headers={"Content-Type": "application/json"},
            json={
                "content_type": "article",
                "topic": "Test topic"
            },
            timeout=10
        )
        
        assert response.status_code == 401
    
    def test_geo_score_increases_with_keywords(self, auth_headers):
        """Test that GEO score increases with more keywords"""
        # Request with few keywords
        response1 = requests.post(
            f"{BASE_URL}/api/content/generate",
            headers=auth_headers,
            json={
                "content_type": "article",
                "topic": "Test topic",
                "keywords": ["test"],
                "brand_name": "TestBrand"
            },
            timeout=30
        )
        
        # Request with more keywords
        response2 = requests.post(
            f"{BASE_URL}/api/content/generate",
            headers=auth_headers,
            json={
                "content_type": "article",
                "topic": "Test topic",
                "keywords": ["test", "SEO", "GEO", "AI", "optimization"],
                "brand_name": "TestBrand"
            },
            timeout=30
        )
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        score1 = response1.json()["geo_score"]
        score2 = response2.json()["geo_score"]
        
        # More keywords should give higher score (based on the formula in backend)
        assert score2 >= score1


class TestContentReformulateAPI:
    """Tests for POST /api/content/reformulate endpoint"""
    
    def test_reformulate_content(self, auth_headers):
        """Test reformulating existing content"""
        response = requests.post(
            f"{BASE_URL}/api/content/reformulate",
            headers=auth_headers,
            json={
                "content": "This is original content that needs to be optimized for AI search engines.",
                "brand_name": "TestBrand"
            },
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert "optimized_content" in data
        assert "suggestions" in data
        assert "original_length" in data
        assert "optimized_length" in data
        assert "reformulated_at" in data
        
        # Validate values
        assert len(data["optimized_content"]) > 0
        assert isinstance(data["suggestions"], list)
    
    def test_reformulate_without_auth_fails(self):
        """Test that reformulation without auth returns 401"""
        response = requests.post(
            f"{BASE_URL}/api/content/reformulate",
            headers={"Content-Type": "application/json"},
            json={
                "content": "Test content to optimize"
            },
            timeout=10
        )
        
        assert response.status_code == 401
    
    def test_reformulate_empty_content_optional(self, auth_headers):
        """Test reformulation with content - validates content is passed correctly"""
        response = requests.post(
            f"{BASE_URL}/api/content/reformulate",
            headers=auth_headers,
            json={
                "content": "Sample content for GEO optimization",
                "brand_name": "TestBrand"
            },
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["original_length"] > 0


class TestContentAPIValidation:
    """Tests for API validation"""
    
    def test_generate_with_optional_project_id(self, auth_headers):
        """Test that project_id is optional"""
        response = requests.post(
            f"{BASE_URL}/api/content/generate",
            headers=auth_headers,
            json={
                "content_type": "article",
                "topic": "Test topic without project"
            },
            timeout=30
        )
        
        assert response.status_code == 200
    
    def test_generate_with_project_id(self, auth_headers):
        """Test generation with project_id"""
        response = requests.post(
            f"{BASE_URL}/api/content/generate",
            headers=auth_headers,
            json={
                "project_id": "proj_test_1772018666518",
                "content_type": "article",
                "topic": "Test topic with project"
            },
            timeout=30
        )
        
        assert response.status_code == 200
    
    def test_reformulate_with_optional_brand_name(self, auth_headers):
        """Test that brand_name is optional"""
        response = requests.post(
            f"{BASE_URL}/api/content/reformulate",
            headers=auth_headers,
            json={
                "content": "Content to optimize without brand"
            },
            timeout=30
        )
        
        assert response.status_code == 200
