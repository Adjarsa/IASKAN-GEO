"""
Backend API Integration Tests for IAskan Verified GEO Protocol™
Tests the API endpoints for the GEO analysis platform.
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def test_session_token():
    """Get test session token from environment or create new one"""
    # Use a fixed test session token for testing
    import subprocess
    result = subprocess.run([
        'mongosh', '--quiet', '--eval', '''
use('test_database');
var timestamp = Date.now();
var userId = 'test-api-user-' + timestamp;
var sessionToken = 'test_api_session_' + timestamp;

db.users.deleteMany({email: /test\\.api\\./});
db.user_sessions.deleteMany({session_token: /test_api_session/});
db.subscriptions.deleteMany({subscription_id: /sub_api_test/});

db.users.insertOne({
  user_id: userId,
  email: 'test.api.' + timestamp + '@example.com',
  name: 'Test API User',
  picture: 'https://via.placeholder.com/150',
  created_at: new Date().toISOString()
});

db.user_sessions.insertOne({
  user_id: userId,
  session_token: sessionToken,
  expires_at: new Date(Date.now() + 7*24*60*60*1000).toISOString(),
  created_at: new Date().toISOString()
});

db.subscriptions.insertOne({
  subscription_id: 'sub_api_test_' + timestamp,
  user_id: userId,
  plan: 'pro',
  status: 'active',
  queries_limit: 600,
  queries_used: 0,
  current_period_start: new Date().toISOString(),
  current_period_end: new Date(Date.now() + 30*24*60*60*1000).toISOString(),
  created_at: new Date().toISOString()
});

print(sessionToken);
'''
    ], capture_output=True, text=True)
    
    return result.stdout.strip()


@pytest.fixture(scope="module")
def authenticated_client(api_client, test_session_token):
    """Session with auth header"""
    api_client.headers.update({"Authorization": f"Bearer {test_session_token}"})
    return api_client


class TestHealthEndpoint:
    """Tests for /api/health endpoint"""
    
    def test_health_returns_healthy_status(self, api_client):
        """API health check should return healthy status"""
        response = api_client.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data['status'] == 'healthy'
        assert 'timestamp' in data
    
    def test_health_response_format(self, api_client):
        """Health endpoint should return proper JSON format"""
        response = api_client.get(f"{BASE_URL}/api/health")
        data = response.json()
        
        assert isinstance(data, dict)
        assert 'status' in data
        assert 'timestamp' in data


class TestSubscriptionPlans:
    """Tests for /api/subscription/plans endpoint"""
    
    def test_get_subscription_plans(self, api_client):
        """Should return all subscription plans"""
        response = api_client.get(f"{BASE_URL}/api/subscription/plans")
        assert response.status_code == 200
        
        data = response.json()
        assert 'plans' in data
        plans = data['plans']
        
        # Should have starter, pro, and business plans
        assert 'starter' in plans
        assert 'pro' in plans
        assert 'business' in plans
    
    def test_starter_plan_details(self, api_client):
        """Starter plan should have correct details"""
        response = api_client.get(f"{BASE_URL}/api/subscription/plans")
        data = response.json()
        
        starter = data['plans']['starter']
        assert starter['name'] == 'Starter'
        assert starter['price'] == 79.0
        assert starter['queries_limit'] == 300
        assert 'chatgpt' in starter['ai_engines']
    
    def test_pro_plan_has_multi_ia(self, api_client):
        """Pro plan should include multi-IA feature"""
        response = api_client.get(f"{BASE_URL}/api/subscription/plans")
        data = response.json()
        
        pro = data['plans']['pro']
        assert pro['name'] == 'Pro'
        assert len(pro['ai_engines']) >= 4
        assert 'chatgpt' in pro['ai_engines']
        assert 'claude' in pro['ai_engines']
        assert 'gemini' in pro['ai_engines']
        assert 'perplexity' in pro['ai_engines']
        assert 'Multi-IA (4 moteurs)' in pro['features']


class TestAuthEndpoints:
    """Tests for authentication endpoints"""
    
    def test_auth_me_requires_authentication(self, api_client):
        """Auth endpoint should require authentication"""
        response = api_client.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 401
    
    def test_auth_me_with_valid_token(self, authenticated_client):
        """Auth endpoint should return user data with valid token"""
        response = authenticated_client.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 200
        
        data = response.json()
        assert 'user' in data
        assert 'subscription' in data
        assert 'user_id' in data['user']
        assert 'email' in data['user']
    
    def test_auth_providers_endpoint(self, api_client):
        """Auth providers endpoint should return available providers"""
        response = api_client.get(f"{BASE_URL}/api/auth/providers")
        assert response.status_code == 200
        
        data = response.json()
        assert 'providers' in data
        assert 'google' in data['providers']


class TestProjectsEndpoints:
    """Tests for project CRUD endpoints"""
    
    def test_create_project(self, authenticated_client):
        """Should create a new project"""
        project_data = {
            "name": "TEST_API_Project",
            "website_url": "https://testbrand.com",
            "brand_name": "TestBrand API",
            "competitors": ["competitor1", "competitor2"],
            "keywords": ["geo", "ai", "visibility"]
        }
        
        response = authenticated_client.post(
            f"{BASE_URL}/api/projects",
            json=project_data
        )
        assert response.status_code == 200
        
        data = response.json()
        assert 'project' in data
        assert data['project']['name'] == "TEST_API_Project"
        assert data['project']['brand_name'] == "TestBrand API"
        return data['project']['project_id']
    
    def test_get_projects(self, authenticated_client):
        """Should list user projects"""
        response = authenticated_client.get(f"{BASE_URL}/api/projects")
        assert response.status_code == 200
        
        data = response.json()
        assert 'projects' in data
        assert isinstance(data['projects'], list)
    
    def test_projects_require_auth(self, api_client):
        """Projects endpoint should require authentication"""
        # Make a fresh request without auth
        response = requests.get(f"{BASE_URL}/api/projects")
        assert response.status_code == 401


class TestAnalysisEndpoints:
    """Tests for analysis endpoints (structure verification only)"""
    
    def test_analyses_list_requires_auth(self, api_client):
        """Analyses list should require authentication"""
        response = api_client.get(f"{BASE_URL}/api/analyses")
        assert response.status_code == 401
    
    def test_get_analyses_with_auth(self, authenticated_client):
        """Should get analyses list with auth"""
        response = authenticated_client.get(f"{BASE_URL}/api/analyses")
        assert response.status_code == 200
        
        data = response.json()
        assert 'analyses' in data
        assert isinstance(data['analyses'], list)


class TestCleanup:
    """Cleanup test data after tests"""
    
    def test_cleanup_test_data(self):
        """Clean up test data created during tests"""
        import subprocess
        result = subprocess.run([
            'mongosh', '--quiet', '--eval', '''
use('test_database');
var deleted_users = db.users.deleteMany({email: /test\\.api\\./});
var deleted_sessions = db.user_sessions.deleteMany({session_token: /test_api_session/});
var deleted_subs = db.subscriptions.deleteMany({subscription_id: /sub_api_test/});
var deleted_projects = db.projects.deleteMany({name: /TEST_API/});
print('Cleaned up test data');
'''
        ], capture_output=True, text=True)
        
        assert 'Cleaned up' in result.stdout
