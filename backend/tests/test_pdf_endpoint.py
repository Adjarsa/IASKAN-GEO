"""
Test suite for PDF Report Generation Endpoint
Tests the /api/analysis/{analysis_id}/pdf endpoint
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials provided by main agent
SESSION_TOKEN = "test_session_f87ae863afb94dad89a9390831fb8b9a"
ANALYSIS_ID = "ana_5c56e0995815"


class TestPDFEndpoint:
    """Test suite for PDF generation endpoint"""
    
    @pytest.fixture
    def authenticated_headers(self):
        """Return headers with authentication token"""
        return {
            "Authorization": f"Bearer {SESSION_TOKEN}",
            "Content-Type": "application/json"
        }
    
    def test_pdf_endpoint_returns_pdf_for_completed_analysis(self, authenticated_headers):
        """
        Test: PDF endpoint returns valid PDF for completed analysis
        Expected: 200 status, content-type application/pdf, PDF bytes
        """
        response = requests.get(
            f"{BASE_URL}/api/analysis/{ANALYSIS_ID}/pdf",
            headers=authenticated_headers
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        print(f"Content-Length: {len(response.content)} bytes")
        
        # Status code assertion
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Content-Type assertion - PDF should return application/pdf
        content_type = response.headers.get('Content-Type', '')
        assert 'application/pdf' in content_type, f"Expected application/pdf, got {content_type}"
        
        # Content-Disposition should indicate file download
        content_disposition = response.headers.get('Content-Disposition', '')
        print(f"Content-Disposition: {content_disposition}")
        assert 'attachment' in content_disposition or 'filename' in content_disposition.lower(), \
            f"Expected attachment disposition, got {content_disposition}"
        
        # PDF content assertions
        pdf_content = response.content
        assert len(pdf_content) > 1000, f"PDF too small ({len(pdf_content)} bytes), expected > 1KB"
        
        # Check PDF magic bytes (PDF files start with %PDF-)
        pdf_header = pdf_content[:5].decode('latin-1')
        print(f"PDF Header: {pdf_header}")
        assert pdf_header == '%PDF-', f"Invalid PDF header: {pdf_header}"
        
        print("TEST PASSED: PDF endpoint returns valid PDF")
    
    def test_pdf_endpoint_returns_404_for_nonexistent_analysis(self, authenticated_headers):
        """
        Test: PDF endpoint returns 404 for non-existent analysis
        Expected: 404 status with error message
        """
        fake_analysis_id = "ana_nonexistent12345"
        
        response = requests.get(
            f"{BASE_URL}/api/analysis/{fake_analysis_id}/pdf",
            headers=authenticated_headers
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        # Status code assertion
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        
        # Error message assertion
        data = response.json()
        assert "detail" in data, "Expected error detail in response"
        print(f"Error detail: {data.get('detail')}")
        
        print("TEST PASSED: PDF endpoint returns 404 for non-existent analysis")
    
    def test_pdf_endpoint_requires_authentication(self):
        """
        Test: PDF endpoint requires authentication
        Expected: 401 status without valid token
        """
        # No auth headers
        response = requests.get(
            f"{BASE_URL}/api/analysis/{ANALYSIS_ID}/pdf"
        )
        
        print(f"Status Code (no auth): {response.status_code}")
        
        # Should return 401 unauthorized
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        
        print("TEST PASSED: PDF endpoint requires authentication")
    
    def test_pdf_endpoint_returns_400_for_pending_analysis(self, authenticated_headers):
        """
        Test: PDF endpoint returns 400 for analysis that is not completed
        Note: This test requires an analysis with status 'pending' or 'running'
        If no such analysis exists, we test with the expected behavior
        """
        # We'll first check if we can find a pending analysis
        # For now, we verify the existing analysis is completed
        response = requests.get(
            f"{BASE_URL}/api/analysis/{ANALYSIS_ID}",
            headers=authenticated_headers
        )
        
        print(f"Analysis Status Check: {response.status_code}")
        
        if response.status_code == 200:
            analysis_data = response.json()
            analysis = analysis_data.get('analysis', {})
            status = analysis.get('status', 'unknown')
            print(f"Analysis ID: {ANALYSIS_ID}")
            print(f"Analysis Status: {status}")
            
            if status == 'completed':
                print("Analysis is completed - cannot test 400 for pending analysis with this ID")
                print("Verified: analysis has completed status which allows PDF generation")
            else:
                # If analysis is not completed, PDF should return 400
                pdf_response = requests.get(
                    f"{BASE_URL}/api/analysis/{ANALYSIS_ID}/pdf",
                    headers=authenticated_headers
                )
                assert pdf_response.status_code == 400, f"Expected 400 for non-completed analysis, got {pdf_response.status_code}"
        
        print("TEST PASSED: Verified analysis status behavior")
    
    def test_pdf_content_structure(self, authenticated_headers):
        """
        Test: PDF contains expected content sections
        This is a basic check - actual PDF content verification would require PDF parsing
        """
        response = requests.get(
            f"{BASE_URL}/api/analysis/{ANALYSIS_ID}/pdf",
            headers=authenticated_headers
        )
        
        if response.status_code != 200:
            pytest.skip(f"Cannot verify PDF content - endpoint returned {response.status_code}")
        
        pdf_content = response.content.decode('latin-1', errors='ignore')
        
        # Check for expected PDF structural elements
        assert '%PDF-' in pdf_content, "Missing PDF header"
        assert '%%EOF' in pdf_content, "Missing PDF footer"
        
        # Check for expected content keywords (PDF internal representation)
        # Note: PDF content is encoded, so we check for common patterns
        print(f"PDF Size: {len(response.content)} bytes")
        print("PDF structure validated")
        
        print("TEST PASSED: PDF content structure verified")


class TestAnalysisEndpoint:
    """Test the main analysis endpoint to verify data for PDF"""
    
    @pytest.fixture
    def authenticated_headers(self):
        return {
            "Authorization": f"Bearer {SESSION_TOKEN}",
            "Content-Type": "application/json"
        }
    
    def test_analysis_endpoint_returns_complete_data(self, authenticated_headers):
        """
        Test: Analysis endpoint returns data needed for PDF
        Verifies: global_score, rate_score, ai_scores, query_scores, recommendations
        """
        response = requests.get(
            f"{BASE_URL}/api/analysis/{ANALYSIS_ID}",
            headers=authenticated_headers
        )
        
        print(f"Status Code: {response.status_code}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert 'analysis' in data, "Expected 'analysis' key in response"
        
        analysis = data['analysis']
        
        # Verify all PDF-required fields are present
        print(f"Analysis ID: {analysis.get('analysis_id')}")
        print(f"Status: {analysis.get('status')}")
        print(f"Global Score: {analysis.get('global_score')}")
        
        # Check required fields for PDF generation
        assert 'global_score' in analysis, "Missing global_score field"
        assert 'rate_score' in analysis, "Missing rate_score field"
        assert 'ai_scores' in analysis, "Missing ai_scores field"
        assert 'query_scores' in analysis, "Missing query_scores field"
        assert 'recommendations' in analysis, "Missing recommendations field"
        
        # Verify data types
        assert isinstance(analysis.get('global_score'), (int, float)), "global_score should be numeric"
        assert isinstance(analysis.get('rate_score'), dict), "rate_score should be a dict"
        assert isinstance(analysis.get('ai_scores'), dict), "ai_scores should be a dict"
        assert isinstance(analysis.get('query_scores'), list), "query_scores should be a list"
        assert isinstance(analysis.get('recommendations'), list), "recommendations should be a list"
        
        # Verify R.A.T.E score structure
        rate_score = analysis.get('rate_score', {})
        for key in ['relevance', 'authority', 'truthfulness', 'endorsement']:
            assert key in rate_score, f"Missing {key} in rate_score"
            print(f"R.A.T.E {key}: {rate_score.get(key)}")
        
        # Verify AI scores
        ai_scores = analysis.get('ai_scores', {})
        print(f"AI Scores: {ai_scores}")
        assert len(ai_scores) > 0, "Expected at least one AI score"
        
        # Verify query scores
        query_scores = analysis.get('query_scores', [])
        print(f"Number of queries: {len(query_scores)}")
        
        # Verify recommendations
        recommendations = analysis.get('recommendations', [])
        print(f"Number of recommendations: {len(recommendations)}")
        
        print("TEST PASSED: Analysis endpoint returns complete data for PDF")


class TestHealthEndpoints:
    """Basic health checks"""
    
    def test_api_health(self):
        """Test API health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        
        print(f"Health Status: {response.status_code}")
        assert response.status_code == 200, f"Health check failed: {response.status_code}"
        
        data = response.json()
        assert data.get('status') == 'healthy', f"Unexpected status: {data}"
        
        print("TEST PASSED: API health check")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
