"""
Test Sprint B Architecture - Modular Routers Migration
Tests:
1. GET /api/visibility/{project_id} - new router works (returns 401 not 404)
2. GET /api/content-audit/{project_id} - new router works (returns 401 not 404)
3. POST /api/content/generate - new router works with REAL geo_score calculation
4. POST /api/contact - new router works
5. Backend health check - stability after refactoring
6. calculate_real_geo_score function - validates REAL scoring (not fake formula)
"""
import pytest
import requests
import os
import sys
import asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://geo-visibility-hub.preview.emergentagent.com').rstrip('/')


class TestBackendHealthAfterRefactoring:
    """Test backend stability after Sprint B refactoring"""
    
    def test_health_endpoint_returns_200(self):
        """Health endpoint should return 200 after refactoring"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_health_contains_timestamp(self):
        """Health response should contain timestamp"""
        response = requests.get(f"{BASE_URL}/api/health")
        data = response.json()
        assert "timestamp" in data


class TestVisibilityRouter:
    """Test /api/visibility/{project_id} endpoint from visibility.py router"""
    
    def test_visibility_endpoint_exists(self):
        """GET /api/visibility/{project_id} should return 401 (not 404) - router is included"""
        response = requests.get(f"{BASE_URL}/api/visibility/test_project_id")
        # 401 means endpoint exists but requires auth
        # 404 would mean endpoint doesn't exist
        assert response.status_code == 401, f"Expected 401 (auth required), got {response.status_code}"
    
    def test_visibility_endpoint_requires_auth(self):
        """Visibility endpoint should require authentication"""
        response = requests.get(f"{BASE_URL}/api/visibility/any_project")
        assert response.status_code == 401


class TestContentAuditRouter:
    """Test /api/content-audit/{project_id} endpoint from content_audit.py router"""
    
    def test_content_audit_endpoint_exists(self):
        """GET /api/content-audit/{project_id} should return 401 (not 404) - router is included"""
        response = requests.get(f"{BASE_URL}/api/content-audit/test_project_id")
        # 401 means endpoint exists but requires auth
        assert response.status_code == 401, f"Expected 401 (auth required), got {response.status_code}"
    
    def test_content_audit_endpoint_requires_auth(self):
        """Content audit endpoint should require authentication"""
        response = requests.get(f"{BASE_URL}/api/content-audit/any_project")
        assert response.status_code == 401


class TestContentRouter:
    """Test /api/content/generate endpoint from content.py router"""
    
    def test_content_generate_endpoint_exists(self):
        """POST /api/content/generate should return 401 (not 404) - router is included"""
        response = requests.post(
            f"{BASE_URL}/api/content/generate",
            json={
                "content_type": "article",
                "topic": "Test topic",
                "keywords": ["test"],
                "brand_name": "TestBrand"
            }
        )
        # 401 means endpoint exists but requires auth
        assert response.status_code == 401, f"Expected 401 (auth required), got {response.status_code}"
    
    def test_content_reformulate_endpoint_exists(self):
        """POST /api/content/reformulate should return 401 (not 404) - router is included"""
        response = requests.post(
            f"{BASE_URL}/api/content/reformulate",
            json={
                "content": "Test content to reformulate",
                "brand_name": "TestBrand"
            }
        )
        # 401 means endpoint exists but requires auth
        assert response.status_code == 401, f"Expected 401 (auth required), got {response.status_code}"


class TestContactRouter:
    """Test /api/contact endpoint from contact.py router"""
    
    def test_contact_endpoint_exists(self):
        """POST /api/contact should accept requests (no auth required)"""
        response = requests.post(
            f"{BASE_URL}/api/contact",
            json={
                "name": "Test User",
                "email": "test@example.com",
                "company": "Test Company",
                "subject": "demo",
                "message": "This is a test message from Sprint B testing"
            }
        )
        # Contact endpoint should work without auth
        # 200 = success, 422 = validation error, 500 = server error
        # Should NOT be 404 (endpoint not found)
        assert response.status_code != 404, f"Contact endpoint not found, got {response.status_code}"
        # Should be 200 (success) or 500 (if email service fails)
        assert response.status_code in [200, 500], f"Unexpected status: {response.status_code}"
    
    def test_contact_returns_success_message(self):
        """Contact endpoint should return success message"""
        response = requests.post(
            f"{BASE_URL}/api/contact",
            json={
                "name": "Test Sprint B",
                "email": "sprintb.test@example.com",
                "company": "Sprint B Test Co",
                "subject": "support",
                "message": "Testing Sprint B contact router migration"
            }
        )
        if response.status_code == 200:
            data = response.json()
            assert "success" in data
            assert data["success"] is True
            assert "message" in data
    
    def test_contact_validates_email(self):
        """Contact endpoint should validate email format"""
        response = requests.post(
            f"{BASE_URL}/api/contact",
            json={
                "name": "Test User",
                "email": "invalid-email",  # Invalid email format
                "subject": "demo",
                "message": "Test message"
            }
        )
        # Should return 422 for validation error
        assert response.status_code == 422, f"Expected 422 for invalid email, got {response.status_code}"


class TestCalculateRealGeoScore:
    """Test the calculate_real_geo_score function directly"""
    
    def test_function_exists(self):
        """calculate_real_geo_score function should exist in content.py router"""
        from app.routers.content import calculate_real_geo_score
        assert callable(calculate_real_geo_score)
    
    def test_empty_content_returns_low_score(self):
        """Empty content should return a low score"""
        from app.routers.content import calculate_real_geo_score
        score = calculate_real_geo_score("", [], "")
        assert score >= 0
        assert score <= 30, f"Empty content should have low score, got {score}"
    
    def test_well_structured_content_returns_high_score(self):
        """Well-structured content should return a high score"""
        from app.routers.content import calculate_real_geo_score
        
        # Create well-structured content with all GEO elements
        content = """# Guide Complet sur le SEO

## Introduction
Le SEO est essentiel pour la visibilité en ligne. Selon une étude de 2024, 75% des utilisateurs ne dépassent pas la première page.

## Les Bases du SEO
- Optimisation des mots-clés
- Structure du contenu
- Liens internes et externes
- Vitesse de chargement

### Mots-clés Importants
1. Recherche de mots-clés
2. Analyse de la concurrence
3. Optimisation on-page

## Statistiques Clés
- 93% du trafic web vient des moteurs de recherche
- 70% des clics vont aux 5 premiers résultats
- 50% des recherches sont locales

## FAQ

**Q: Qu'est-ce que le SEO?**
R: Le SEO (Search Engine Optimization) est l'optimisation pour les moteurs de recherche.

**Q: Combien de temps pour voir des résultats?**
R: En moyenne, 3 à 6 mois selon la concurrence.

## Conclusion
Le SEO est un investissement à long terme. Source: Google Search Central.
"""
        keywords = ["SEO", "optimisation", "mots-clés"]
        brand_name = "Google"
        
        score = calculate_real_geo_score(content, keywords, brand_name)
        assert score >= 50, f"Well-structured content should have score >= 50, got {score}"
    
    def test_score_not_fake_formula(self):
        """Score should NOT follow the fake formula: min(95, 75 + keywords*2)"""
        from app.routers.content import calculate_real_geo_score
        
        # Test with 5 keywords - fake formula would give min(95, 75 + 5*2) = 85
        # But with minimal content, real score should be much lower
        minimal_content = "Just a simple sentence."
        keywords = ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"]
        
        score = calculate_real_geo_score(minimal_content, keywords, "Brand")
        
        # Fake formula would give 85, real analysis should give much lower
        assert score < 70, f"Score {score} suggests fake formula is still being used"
    
    def test_structure_scoring(self):
        """Test that headers contribute to score"""
        from app.routers.content import calculate_real_geo_score
        
        # Content with headers
        with_headers = """# Main Title

## Section 1
Some content here.

## Section 2
More content here.

### Subsection
Details here.
"""
        # Content without headers
        without_headers = """Main Title

Section 1
Some content here.

Section 2
More content here.

Subsection
Details here.
"""
        score_with = calculate_real_geo_score(with_headers, [], "")
        score_without = calculate_real_geo_score(without_headers, [], "")
        
        assert score_with > score_without, f"Headers should increase score: {score_with} vs {score_without}"
    
    def test_lists_scoring(self):
        """Test that lists contribute to score"""
        from app.routers.content import calculate_real_geo_score
        
        # Content with lists
        with_lists = """# Title

Here are the key points:
- Point one
- Point two
- Point three
- Point four
- Point five

Steps to follow:
1. First step
2. Second step
3. Third step
"""
        # Content without lists
        without_lists = """# Title

Here are the key points:
Point one, point two, point three, point four, point five.

Steps to follow:
First step, second step, third step.
"""
        score_with = calculate_real_geo_score(with_lists, [], "")
        score_without = calculate_real_geo_score(without_lists, [], "")
        
        assert score_with > score_without, f"Lists should increase score: {score_with} vs {score_without}"
    
    def test_data_statistics_scoring(self):
        """Test that numbers/statistics contribute to score"""
        from app.routers.content import calculate_real_geo_score
        
        # Content with statistics
        with_stats = """# Market Analysis

The market grew by 25% in 2024. Revenue reached $1.5 billion.
Customer satisfaction is at 92%. We have 10,000 active users.
The average order value is €150. Growth rate: 15% year-over-year.
"""
        # Content without statistics
        without_stats = """# Market Analysis

The market grew significantly last year. Revenue reached a high level.
Customer satisfaction is excellent. We have many active users.
The average order value is good. Growth rate is positive.
"""
        score_with = calculate_real_geo_score(with_stats, [], "")
        score_without = calculate_real_geo_score(without_stats, [], "")
        
        assert score_with > score_without, f"Statistics should increase score: {score_with} vs {score_without}"
    
    def test_keywords_scoring(self):
        """Test that keyword presence contributes to score"""
        from app.routers.content import calculate_real_geo_score
        
        content = "This article discusses SEO optimization and digital marketing strategies."
        
        # Keywords present in content
        matching_keywords = ["SEO", "optimization", "marketing"]
        # Keywords not present
        non_matching_keywords = ["blockchain", "cryptocurrency", "NFT"]
        
        score_matching = calculate_real_geo_score(content, matching_keywords, "")
        score_non_matching = calculate_real_geo_score(content, non_matching_keywords, "")
        
        assert score_matching > score_non_matching, f"Matching keywords should increase score: {score_matching} vs {score_non_matching}"
    
    def test_brand_mentions_scoring(self):
        """Test that brand mentions contribute to score"""
        from app.routers.content import calculate_real_geo_score
        
        # Content with brand mentions
        with_brand = """# About IAskan

IAskan is a leading GEO platform. IAskan helps businesses improve visibility.
With IAskan, you can track your AI presence.
"""
        # Content without brand mentions
        without_brand = """# About the Platform

This is a leading GEO platform. It helps businesses improve visibility.
With this tool, you can track your AI presence.
"""
        score_with = calculate_real_geo_score(with_brand, [], "IAskan")
        score_without = calculate_real_geo_score(without_brand, [], "IAskan")
        
        assert score_with > score_without, f"Brand mentions should increase score: {score_with} vs {score_without}"
    
    def test_faq_presence_scoring(self):
        """Test that FAQ presence contributes to score"""
        from app.routers.content import calculate_real_geo_score
        
        # Content with FAQ
        with_faq = """# Guide

Some content here.

## FAQ

**Q: What is this?**
R: This is a guide.

**Q: How does it work?**
R: It works well.
"""
        # Content without FAQ
        without_faq = """# Guide

Some content here.

## More Information

This is additional information about the topic.
"""
        score_with = calculate_real_geo_score(with_faq, [], "")
        score_without = calculate_real_geo_score(without_faq, [], "")
        
        assert score_with > score_without, f"FAQ should increase score: {score_with} vs {score_without}"
    
    def test_score_bounds(self):
        """Test that score is always between 0 and 100"""
        from app.routers.content import calculate_real_geo_score
        
        # Test with various inputs
        test_cases = [
            ("", [], ""),
            ("Short", [], ""),
            ("A" * 10000, ["keyword"] * 100, "Brand" * 50),
            ("# Title\n" * 100, [], ""),
        ]
        
        for content, keywords, brand in test_cases:
            score = calculate_real_geo_score(content, keywords, brand)
            assert 0 <= score <= 100, f"Score {score} out of bounds for content length {len(content)}"


class TestRouterPriority:
    """Test that Sprint B routers have priority over legacy api_router"""
    
    def test_visibility_router_has_priority(self):
        """Visibility router should be included before api_router"""
        # Read server.py to verify router order
        server_path = "/app/backend/server.py"
        with open(server_path, 'r') as f:
            content = f.read()
        
        # Find positions of router includes
        visibility_pos = content.find("app.include_router(visibility_router.router)")
        api_router_pos = content.find("app.include_router(api_router)")
        
        assert visibility_pos > 0, "visibility_router not found in server.py"
        assert api_router_pos > 0, "api_router not found in server.py"
        assert visibility_pos < api_router_pos, "visibility_router should be included BEFORE api_router"
    
    def test_content_audit_router_has_priority(self):
        """Content audit router should be included before api_router"""
        server_path = "/app/backend/server.py"
        with open(server_path, 'r') as f:
            content = f.read()
        
        content_audit_pos = content.find("app.include_router(content_audit_router.router)")
        api_router_pos = content.find("app.include_router(api_router)")
        
        assert content_audit_pos > 0, "content_audit_router not found in server.py"
        assert content_audit_pos < api_router_pos, "content_audit_router should be included BEFORE api_router"
    
    def test_content_router_has_priority(self):
        """Content router should be included before api_router"""
        server_path = "/app/backend/server.py"
        with open(server_path, 'r') as f:
            content = f.read()
        
        content_pos = content.find("app.include_router(content_router.router)")
        api_router_pos = content.find("app.include_router(api_router)")
        
        assert content_pos > 0, "content_router not found in server.py"
        assert content_pos < api_router_pos, "content_router should be included BEFORE api_router"
    
    def test_contact_router_has_priority(self):
        """Contact router should be included before api_router"""
        server_path = "/app/backend/server.py"
        with open(server_path, 'r') as f:
            content = f.read()
        
        contact_pos = content.find("app.include_router(contact_router.router)")
        api_router_pos = content.find("app.include_router(api_router)")
        
        assert contact_pos > 0, "contact_router not found in server.py"
        assert contact_pos < api_router_pos, "contact_router should be included BEFORE api_router"


class TestRouterFileStructure:
    """Test that router files exist and have correct structure"""
    
    def test_visibility_router_file_exists(self):
        """visibility.py router file should exist"""
        import os
        assert os.path.exists("/app/backend/app/routers/visibility.py")
    
    def test_content_audit_router_file_exists(self):
        """content_audit.py router file should exist"""
        import os
        assert os.path.exists("/app/backend/app/routers/content_audit.py")
    
    def test_content_router_file_exists(self):
        """content.py router file should exist"""
        import os
        assert os.path.exists("/app/backend/app/routers/content.py")
    
    def test_contact_router_file_exists(self):
        """contact.py router file should exist"""
        import os
        assert os.path.exists("/app/backend/app/routers/contact.py")
    
    def test_visibility_router_has_correct_prefix(self):
        """Visibility router should have /api prefix"""
        with open("/app/backend/app/routers/visibility.py", 'r') as f:
            content = f.read()
        assert 'prefix="/api"' in content, "Visibility router should have /api prefix"
    
    def test_content_audit_router_has_correct_prefix(self):
        """Content audit router should have /api prefix"""
        with open("/app/backend/app/routers/content_audit.py", 'r') as f:
            content = f.read()
        assert 'prefix="/api"' in content, "Content audit router should have /api prefix"
    
    def test_content_router_has_correct_prefix(self):
        """Content router should have /api prefix"""
        with open("/app/backend/app/routers/content.py", 'r') as f:
            content = f.read()
        assert 'prefix="/api"' in content, "Content router should have /api prefix"
    
    def test_contact_router_has_correct_prefix(self):
        """Contact router should have /api prefix"""
        with open("/app/backend/app/routers/contact.py", 'r') as f:
            content = f.read()
        assert 'prefix="/api"' in content, "Contact router should have /api prefix"
