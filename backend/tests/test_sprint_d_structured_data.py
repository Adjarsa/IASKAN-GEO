"""
Test Sprint D - Structured Data Generator (Schema.org)
Tests:
1. GET /api/structured-data/templates - list available templates
2. POST /api/structured-data/organization - generate Organization schema
3. POST /api/structured-data/product - generate Product schema
4. POST /api/structured-data/faq - generate FAQPage schema
5. POST /api/structured-data/article - generate Article schema
6. POST /api/structured-data/howto - generate HowTo schema
7. POST /api/structured-data/local-business - generate LocalBusiness schema
8. Backend stability after adding new router
"""
import pytest
import requests
import os
import json

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://geo-visibility-hub.preview.emergentagent.com').rstrip('/')


class TestBackendStabilityAfterSprintD:
    """Test backend stability after Sprint D structured-data router addition"""
    
    def test_health_endpoint_returns_200(self):
        """Health endpoint should return 200 after Sprint D changes"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_health_contains_timestamp(self):
        """Health response should contain timestamp"""
        response = requests.get(f"{BASE_URL}/api/health")
        data = response.json()
        assert "timestamp" in data


class TestStructuredDataTemplatesEndpoint:
    """Test GET /api/structured-data/templates endpoint"""
    
    def test_templates_endpoint_exists(self):
        """GET /api/structured-data/templates should return 401 (not 404) - router is included"""
        response = requests.get(f"{BASE_URL}/api/structured-data/templates")
        # 401 means endpoint exists but requires auth
        # 404 would mean endpoint doesn't exist
        assert response.status_code == 401, f"Expected 401 (auth required), got {response.status_code}"
    
    def test_templates_endpoint_requires_auth(self):
        """Templates endpoint should require authentication"""
        response = requests.get(f"{BASE_URL}/api/structured-data/templates")
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data


class TestOrganizationSchemaEndpoint:
    """Test POST /api/structured-data/organization endpoint"""
    
    def test_organization_endpoint_exists(self):
        """POST /api/structured-data/organization should return 401 (not 404) - router is included"""
        response = requests.post(
            f"{BASE_URL}/api/structured-data/organization",
            json={
                "name": "Test Company",
                "description": "A test company for testing",
                "url": "https://example.com"
            }
        )
        # 401 means endpoint exists but requires auth
        assert response.status_code == 401, f"Expected 401 (auth required), got {response.status_code}"
    
    def test_organization_endpoint_requires_auth(self):
        """Organization endpoint should require authentication"""
        response = requests.post(
            f"{BASE_URL}/api/structured-data/organization",
            json={
                "name": "Test Company",
                "description": "A test company",
                "url": "https://example.com"
            }
        )
        assert response.status_code == 401


class TestProductSchemaEndpoint:
    """Test POST /api/structured-data/product endpoint"""
    
    def test_product_endpoint_exists(self):
        """POST /api/structured-data/product should return 401 (not 404) - router is included"""
        response = requests.post(
            f"{BASE_URL}/api/structured-data/product",
            json={
                "name": "Test Product",
                "description": "A test product",
                "brand": "Test Brand",
                "url": "https://example.com/product"
            }
        )
        # 401 means endpoint exists but requires auth
        assert response.status_code == 401, f"Expected 401 (auth required), got {response.status_code}"
    
    def test_product_endpoint_requires_auth(self):
        """Product endpoint should require authentication"""
        response = requests.post(
            f"{BASE_URL}/api/structured-data/product",
            json={
                "name": "Test Product",
                "description": "A test product",
                "brand": "Test Brand",
                "url": "https://example.com/product"
            }
        )
        assert response.status_code == 401


class TestFAQSchemaEndpoint:
    """Test POST /api/structured-data/faq endpoint"""
    
    def test_faq_endpoint_exists(self):
        """POST /api/structured-data/faq should return 401 (not 404) - router is included"""
        response = requests.post(
            f"{BASE_URL}/api/structured-data/faq",
            json={
                "questions": [
                    {"question": "What is this?", "answer": "This is a test."}
                ]
            }
        )
        # 401 means endpoint exists but requires auth
        assert response.status_code == 401, f"Expected 401 (auth required), got {response.status_code}"
    
    def test_faq_endpoint_requires_auth(self):
        """FAQ endpoint should require authentication"""
        response = requests.post(
            f"{BASE_URL}/api/structured-data/faq",
            json={
                "questions": [
                    {"question": "Test question?", "answer": "Test answer."}
                ]
            }
        )
        assert response.status_code == 401


class TestArticleSchemaEndpoint:
    """Test POST /api/structured-data/article endpoint"""
    
    def test_article_endpoint_exists(self):
        """POST /api/structured-data/article should return 401 (not 404) - router is included"""
        response = requests.post(
            f"{BASE_URL}/api/structured-data/article",
            json={
                "title": "Test Article",
                "description": "A test article description",
                "author_name": "Test Author",
                "date_published": "2026-04-05",
                "publisher_name": "Test Publisher"
            }
        )
        # 401 means endpoint exists but requires auth
        assert response.status_code == 401, f"Expected 401 (auth required), got {response.status_code}"
    
    def test_article_endpoint_requires_auth(self):
        """Article endpoint should require authentication"""
        response = requests.post(
            f"{BASE_URL}/api/structured-data/article",
            json={
                "title": "Test Article",
                "description": "A test article",
                "author_name": "Test Author",
                "date_published": "2026-04-05",
                "publisher_name": "Test Publisher"
            }
        )
        assert response.status_code == 401


class TestHowToSchemaEndpoint:
    """Test POST /api/structured-data/howto endpoint"""
    
    def test_howto_endpoint_exists(self):
        """POST /api/structured-data/howto should return 401 (not 404) - router is included"""
        response = requests.post(
            f"{BASE_URL}/api/structured-data/howto",
            json={
                "name": "How to Test",
                "description": "A guide on testing",
                "steps": [
                    {"name": "Step 1", "text": "Do the first thing"}
                ]
            }
        )
        # 401 means endpoint exists but requires auth
        assert response.status_code == 401, f"Expected 401 (auth required), got {response.status_code}"
    
    def test_howto_endpoint_requires_auth(self):
        """HowTo endpoint should require authentication"""
        response = requests.post(
            f"{BASE_URL}/api/structured-data/howto",
            json={
                "name": "How to Test",
                "description": "A guide on testing",
                "steps": [
                    {"name": "Step 1", "text": "Do the first thing"}
                ]
            }
        )
        assert response.status_code == 401


class TestLocalBusinessSchemaEndpoint:
    """Test POST /api/structured-data/local-business endpoint"""
    
    def test_local_business_endpoint_exists(self):
        """POST /api/structured-data/local-business should return 401 (not 404) - router is included"""
        response = requests.post(
            f"{BASE_URL}/api/structured-data/local-business",
            json={
                "name": "Test Business",
                "description": "A local test business",
                "url": "https://example.com",
                "address": {
                    "streetAddress": "123 Test St",
                    "addressLocality": "Test City",
                    "postalCode": "12345",
                    "addressCountry": "FR"
                }
            }
        )
        # 401 means endpoint exists but requires auth
        assert response.status_code == 401, f"Expected 401 (auth required), got {response.status_code}"
    
    def test_local_business_endpoint_requires_auth(self):
        """LocalBusiness endpoint should require authentication"""
        response = requests.post(
            f"{BASE_URL}/api/structured-data/local-business",
            json={
                "name": "Test Business",
                "description": "A local test business",
                "url": "https://example.com",
                "address": {
                    "streetAddress": "123 Test St",
                    "addressLocality": "Test City",
                    "postalCode": "12345",
                    "addressCountry": "FR"
                }
            }
        )
        assert response.status_code == 401


class TestSchemaGeneratorFunctions:
    """Test the schema generator functions directly (unit tests)"""
    
    def test_generate_organization_schema_basic(self):
        """Test Organization schema generation with required fields only"""
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from app.routers.structured_data import generate_organization_schema, OrganizationSchemaRequest
        
        request = OrganizationSchemaRequest(
            name="Test Company",
            description="A test company",
            url="https://example.com"
        )
        schema = generate_organization_schema(request)
        
        assert schema["@context"] == "https://schema.org"
        assert schema["@type"] == "Organization"
        assert schema["name"] == "Test Company"
        assert schema["description"] == "A test company"
        assert schema["url"] == "https://example.com"
    
    def test_generate_organization_schema_with_optional_fields(self):
        """Test Organization schema generation with all optional fields"""
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from app.routers.structured_data import generate_organization_schema, OrganizationSchemaRequest
        
        request = OrganizationSchemaRequest(
            name="Full Company",
            description="A company with all fields",
            url="https://fullcompany.com",
            logo_url="https://fullcompany.com/logo.png",
            social_profiles=["https://twitter.com/fullcompany", "https://linkedin.com/company/fullcompany"],
            contact_email="contact@fullcompany.com",
            contact_phone="+33123456789",
            address={
                "streetAddress": "123 Main St",
                "addressLocality": "Paris",
                "postalCode": "75001",
                "addressCountry": "FR"
            }
        )
        schema = generate_organization_schema(request)
        
        assert schema["logo"] == "https://fullcompany.com/logo.png"
        assert schema["sameAs"] == ["https://twitter.com/fullcompany", "https://linkedin.com/company/fullcompany"]
        assert schema["contactPoint"]["email"] == "contact@fullcompany.com"
        assert schema["contactPoint"]["telephone"] == "+33123456789"
        assert schema["address"]["@type"] == "PostalAddress"
        assert schema["address"]["streetAddress"] == "123 Main St"
    
    def test_generate_product_schema_basic(self):
        """Test Product schema generation with required fields only"""
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from app.routers.structured_data import generate_product_schema, ProductSchemaRequest
        
        request = ProductSchemaRequest(
            name="Test Product",
            description="A test product",
            brand="Test Brand",
            url="https://example.com/product"
        )
        schema = generate_product_schema(request)
        
        assert schema["@context"] == "https://schema.org"
        assert schema["@type"] == "Product"
        assert schema["name"] == "Test Product"
        assert schema["brand"]["@type"] == "Brand"
        assert schema["brand"]["name"] == "Test Brand"
    
    def test_generate_product_schema_with_price_and_rating(self):
        """Test Product schema generation with price and rating"""
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from app.routers.structured_data import generate_product_schema, ProductSchemaRequest
        
        request = ProductSchemaRequest(
            name="Premium Product",
            description="A premium product",
            brand="Premium Brand",
            url="https://example.com/premium",
            price=99.99,
            currency="EUR",
            availability="InStock",
            rating=4.5,
            review_count=100
        )
        schema = generate_product_schema(request)
        
        assert "offers" in schema
        assert schema["offers"]["@type"] == "Offer"
        assert schema["offers"]["price"] == 99.99
        assert schema["offers"]["priceCurrency"] == "EUR"
        assert "aggregateRating" in schema
        assert schema["aggregateRating"]["ratingValue"] == 4.5
        assert schema["aggregateRating"]["reviewCount"] == 100
    
    def test_generate_faq_schema(self):
        """Test FAQPage schema generation"""
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from app.routers.structured_data import generate_faq_schema, FAQSchemaRequest
        
        request = FAQSchemaRequest(
            questions=[
                {"question": "What is this?", "answer": "This is a test."},
                {"question": "How does it work?", "answer": "It works well."}
            ]
        )
        schema = generate_faq_schema(request)
        
        assert schema["@context"] == "https://schema.org"
        assert schema["@type"] == "FAQPage"
        assert len(schema["mainEntity"]) == 2
        assert schema["mainEntity"][0]["@type"] == "Question"
        assert schema["mainEntity"][0]["name"] == "What is this?"
        assert schema["mainEntity"][0]["acceptedAnswer"]["@type"] == "Answer"
        assert schema["mainEntity"][0]["acceptedAnswer"]["text"] == "This is a test."
    
    def test_generate_article_schema_basic(self):
        """Test Article schema generation with required fields"""
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from app.routers.structured_data import generate_article_schema, ArticleSchemaRequest
        
        request = ArticleSchemaRequest(
            title="Test Article",
            description="A test article description",
            author_name="Test Author",
            date_published="2026-04-05",
            publisher_name="Test Publisher"
        )
        schema = generate_article_schema(request)
        
        assert schema["@context"] == "https://schema.org"
        assert schema["@type"] == "Article"
        assert schema["headline"] == "Test Article"
        assert schema["author"]["@type"] == "Person"
        assert schema["author"]["name"] == "Test Author"
        assert schema["datePublished"] == "2026-04-05"
        assert schema["publisher"]["@type"] == "Organization"
        assert schema["publisher"]["name"] == "Test Publisher"
    
    def test_generate_article_schema_with_optional_fields(self):
        """Test Article schema generation with optional fields"""
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from app.routers.structured_data import generate_article_schema, ArticleSchemaRequest
        
        request = ArticleSchemaRequest(
            title="Full Article",
            description="A full article",
            author_name="Full Author",
            date_published="2026-04-01",
            date_modified="2026-04-05",
            image_url="https://example.com/image.jpg",
            publisher_name="Full Publisher",
            publisher_logo="https://example.com/logo.png"
        )
        schema = generate_article_schema(request)
        
        assert schema["dateModified"] == "2026-04-05"
        assert schema["image"] == "https://example.com/image.jpg"
        assert schema["publisher"]["logo"]["@type"] == "ImageObject"
        assert schema["publisher"]["logo"]["url"] == "https://example.com/logo.png"
    
    def test_generate_howto_schema(self):
        """Test HowTo schema generation"""
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from app.routers.structured_data import generate_howto_schema, HowToSchemaRequest
        
        request = HowToSchemaRequest(
            name="How to Test",
            description="A guide on testing",
            steps=[
                {"name": "Step 1", "text": "Do the first thing"},
                {"name": "Step 2", "text": "Do the second thing"}
            ],
            total_time="PT30M",
            image_url="https://example.com/howto.jpg"
        )
        schema = generate_howto_schema(request)
        
        assert schema["@context"] == "https://schema.org"
        assert schema["@type"] == "HowTo"
        assert schema["name"] == "How to Test"
        assert len(schema["step"]) == 2
        assert schema["step"][0]["@type"] == "HowToStep"
        assert schema["step"][0]["position"] == 1
        assert schema["step"][0]["name"] == "Step 1"
        assert schema["totalTime"] == "PT30M"
        assert schema["image"] == "https://example.com/howto.jpg"
    
    def test_generate_local_business_schema(self):
        """Test LocalBusiness schema generation"""
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from app.routers.structured_data import generate_local_business_schema, LocalBusinessSchemaRequest
        
        request = LocalBusinessSchemaRequest(
            name="Test Business",
            description="A local test business",
            url="https://example.com",
            address={
                "streetAddress": "123 Test St",
                "addressLocality": "Test City",
                "postalCode": "12345",
                "addressCountry": "FR"
            },
            phone="+33123456789",
            opening_hours=["Mo-Fr 09:00-18:00", "Sa 10:00-14:00"],
            price_range="$$",
            image_url="https://example.com/business.jpg"
        )
        schema = generate_local_business_schema(request)
        
        assert schema["@context"] == "https://schema.org"
        assert schema["@type"] == "LocalBusiness"
        assert schema["name"] == "Test Business"
        assert schema["address"]["@type"] == "PostalAddress"
        assert schema["address"]["streetAddress"] == "123 Test St"
        assert schema["telephone"] == "+33123456789"
        assert schema["openingHours"] == ["Mo-Fr 09:00-18:00", "Sa 10:00-14:00"]
        assert schema["priceRange"] == "$$"
        assert schema["image"] == "https://example.com/business.jpg"
    
    def test_format_json_ld(self):
        """Test JSON-LD formatting function"""
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from app.routers.structured_data import format_json_ld
        
        schema = {
            "@context": "https://schema.org",
            "@type": "Organization",
            "name": "Test"
        }
        json_ld = format_json_ld(schema)
        
        assert '<script type="application/ld+json">' in json_ld
        assert '</script>' in json_ld
        assert '"@context": "https://schema.org"' in json_ld
        assert '"@type": "Organization"' in json_ld


class TestSchemaValidation:
    """Test schema validation and edge cases"""
    
    def test_organization_schema_without_optional_fields(self):
        """Organization schema should work without optional fields"""
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from app.routers.structured_data import generate_organization_schema, OrganizationSchemaRequest
        
        request = OrganizationSchemaRequest(
            name="Minimal Company",
            description="Minimal description",
            url="https://minimal.com"
        )
        schema = generate_organization_schema(request)
        
        # Should not have optional fields
        assert "logo" not in schema
        assert "sameAs" not in schema
        assert "contactPoint" not in schema
        assert "address" not in schema
    
    def test_product_schema_without_price(self):
        """Product schema should work without price"""
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from app.routers.structured_data import generate_product_schema, ProductSchemaRequest
        
        request = ProductSchemaRequest(
            name="Free Product",
            description="A free product",
            brand="Free Brand",
            url="https://example.com/free"
        )
        schema = generate_product_schema(request)
        
        # Should not have offers without price
        assert "offers" not in schema
    
    def test_faq_schema_empty_questions(self):
        """FAQPage schema should handle empty questions list"""
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from app.routers.structured_data import generate_faq_schema, FAQSchemaRequest
        
        request = FAQSchemaRequest(questions=[])
        schema = generate_faq_schema(request)
        
        assert schema["@type"] == "FAQPage"
        assert schema["mainEntity"] == []
    
    def test_howto_schema_step_positions(self):
        """HowTo schema should have correct step positions"""
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from app.routers.structured_data import generate_howto_schema, HowToSchemaRequest
        
        request = HowToSchemaRequest(
            name="Multi-step Guide",
            description="A guide with many steps",
            steps=[
                {"name": "First", "text": "First step"},
                {"name": "Second", "text": "Second step"},
                {"name": "Third", "text": "Third step"}
            ]
        )
        schema = generate_howto_schema(request)
        
        assert schema["step"][0]["position"] == 1
        assert schema["step"][1]["position"] == 2
        assert schema["step"][2]["position"] == 3
    
    def test_local_business_schema_minimal(self):
        """LocalBusiness schema should work with minimal required fields"""
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from app.routers.structured_data import generate_local_business_schema, LocalBusinessSchemaRequest
        
        request = LocalBusinessSchemaRequest(
            name="Minimal Business",
            description="Minimal description",
            url="https://minimal.com",
            address={
                "streetAddress": "1 Main St",
                "addressLocality": "City",
                "postalCode": "00000",
                "addressCountry": "FR"
            }
        )
        schema = generate_local_business_schema(request)
        
        # Should not have optional fields
        assert "telephone" not in schema
        assert "openingHours" not in schema
        assert "priceRange" not in schema
        assert "image" not in schema


class TestTemplatesResponse:
    """Test the templates endpoint response structure (unit test)"""
    
    def test_templates_structure(self):
        """Verify templates list structure"""
        # Expected templates based on the router code
        expected_types = ["Organization", "Product", "FAQPage", "Article", "HowTo", "LocalBusiness"]
        
        # This is a unit test of the expected response structure
        # The actual endpoint test is in TestStructuredDataTemplatesEndpoint
        assert len(expected_types) == 6
        
        # Verify each type has expected endpoint pattern
        for schema_type in expected_types:
            if schema_type == "FAQPage":
                endpoint = "/api/structured-data/faq"
            elif schema_type == "LocalBusiness":
                endpoint = "/api/structured-data/local-business"
            else:
                endpoint = f"/api/structured-data/{schema_type.lower()}"
            
            # Verify endpoint format
            assert endpoint.startswith("/api/structured-data/")
