"""
Backend API Integration Tests for IAskan Modular Router Endpoints
Tests the refactored auth, projects, dashboard, organizations, and onboarding endpoints.
"""
import pytest
import requests
import subprocess
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def test_session_data():
    """Create test user, session, and subscription"""
    result = subprocess.run([
        'mongosh', '--quiet', '--eval', '''
use('test_database');
var timestamp = Date.now();
var userId = 'test-router-' + timestamp;
var sessionToken = 'test_router_sess_' + timestamp;

// Cleanup old test data first
db.users.deleteMany({email: /test\\.router_test\\./});
db.user_sessions.deleteMany({session_token: /test_router_sess_/});
db.subscriptions.deleteMany({subscription_id: /sub_router_pytest_/});
db.projects.deleteMany({name: /PYTEST_ROUTER/});
db.organizations.deleteMany({name: /PYTEST_ROUTER/});
db.user_onboarding.deleteMany({user_id: /test-router-/});

db.users.insertOne({
  user_id: userId,
  email: 'test.router_test.' + timestamp + '@example.com',
  name: 'Test Router Pytest User',
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
  subscription_id: 'sub_router_pytest_' + timestamp,
  user_id: userId,
  plan: 'pro',
  status: 'active',
  queries_limit: 600,
  queries_used: 0,
  scans_limit: 50,
  scans_used: 0,
  current_period_start: new Date().toISOString(),
  current_period_end: new Date(Date.now() + 30*24*60*60*1000).toISOString(),
  created_at: new Date().toISOString()
});

print(sessionToken + '|' + userId);
'''
    ], capture_output=True, text=True)
    
    output = result.stdout.strip()
    parts = output.split('|')
    return {"session_token": parts[0], "user_id": parts[1]}


@pytest.fixture(scope="module")
def authenticated_client(api_client, test_session_data):
    """Session with auth header"""
    api_client.headers.update({"Authorization": f"Bearer {test_session_data['session_token']}"})
    return api_client


class TestAuthRouter:
    """Tests for /api/auth/* endpoints from auth.py router"""
    
    def test_auth_providers_returns_available_providers(self, api_client):
        """GET /api/auth/providers should return available auth providers"""
        response = api_client.get(f"{BASE_URL}/api/auth/providers")
        assert response.status_code == 200
        
        data = response.json()
        assert 'providers' in data
        assert 'google' in data['providers']
        assert 'microsoft' in data['providers']
        assert 'linkedin' in data['providers']
        assert 'magic_link' in data['providers']
        # Google and magic_link should always be true
        assert data['providers']['google'] is True
        assert data['providers']['magic_link'] is True
    
    def test_auth_session_requires_session_id(self, api_client):
        """POST /api/auth/session should require session_id"""
        response = api_client.post(f"{BASE_URL}/api/auth/session", json={})
        assert response.status_code == 400
        assert "session_id" in response.json().get("detail", "").lower()
    
    def test_auth_me_requires_authentication(self, api_client):
        """GET /api/auth/me should return 401 without auth"""
        # Create new session without auth header
        clean_session = requests.Session()
        clean_session.headers.update({"Content-Type": "application/json"})
        response = clean_session.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 401
        assert response.json().get("detail") == "Non authentifié"
    
    def test_auth_me_returns_user_with_valid_token(self, authenticated_client, test_session_data):
        """GET /api/auth/me should return user data with valid token"""
        response = authenticated_client.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 200
        
        data = response.json()
        assert 'user' in data
        assert 'subscription' in data
        assert data['user']['user_id'] == test_session_data['user_id']
        assert 'email' in data['user']
        assert data['subscription']['plan'] == 'pro'
    
    def test_auth_logout_succeeds(self, api_client):
        """POST /api/auth/logout should succeed"""
        response = api_client.post(f"{BASE_URL}/api/auth/logout")
        assert response.status_code == 200
        assert response.json().get("message") == "Déconnexion réussie"


class TestProjectsRouter:
    """Tests for /api/projects/* endpoints from projects.py router"""
    
    def test_projects_requires_authentication(self, api_client):
        """GET /api/projects should return 401 without auth"""
        clean_session = requests.Session()
        response = clean_session.get(f"{BASE_URL}/api/projects")
        assert response.status_code == 401
    
    def test_get_projects_returns_list(self, authenticated_client):
        """GET /api/projects should return projects list"""
        response = authenticated_client.get(f"{BASE_URL}/api/projects")
        assert response.status_code == 200
        
        data = response.json()
        assert 'projects' in data
        assert isinstance(data['projects'], list)
    
    def test_create_project(self, authenticated_client):
        """POST /api/projects should create a new project"""
        project_data = {
            "name": "PYTEST_ROUTER_Project",
            "website_url": "https://pytest-router.com",
            "brand_name": "PytestRouterBrand",
            "competitors": ["comp1", "comp2"],
            "keywords": ["test", "pytest"]
        }
        
        response = authenticated_client.post(f"{BASE_URL}/api/projects", json=project_data)
        assert response.status_code == 200
        
        data = response.json()
        assert 'project' in data
        assert data['project']['name'] == "PYTEST_ROUTER_Project"
        assert data['project']['brand_name'] == "PytestRouterBrand"
        assert 'project_id' in data['project']
        return data['project']['project_id']
    
    def test_get_project_by_id(self, authenticated_client):
        """GET /api/projects/{id} should return specific project"""
        # First create a project
        project_data = {
            "name": "PYTEST_ROUTER_GetById",
            "website_url": "https://getbyid.com",
            "brand_name": "GetByIdBrand"
        }
        create_response = authenticated_client.post(f"{BASE_URL}/api/projects", json=project_data)
        project_id = create_response.json()['project']['project_id']
        
        # Then get it by ID
        response = authenticated_client.get(f"{BASE_URL}/api/projects/{project_id}")
        assert response.status_code == 200
        assert response.json()['project']['project_id'] == project_id
    
    def test_update_project(self, authenticated_client):
        """PUT /api/projects/{id} should update project"""
        # Create project
        project_data = {
            "name": "PYTEST_ROUTER_ToUpdate",
            "website_url": "https://toupdate.com",
            "brand_name": "ToUpdateBrand"
        }
        create_response = authenticated_client.post(f"{BASE_URL}/api/projects", json=project_data)
        project_id = create_response.json()['project']['project_id']
        
        # Update project
        update_data = {"name": "PYTEST_ROUTER_Updated"}
        response = authenticated_client.put(f"{BASE_URL}/api/projects/{project_id}", json=update_data)
        assert response.status_code == 200
        assert response.json()['project']['name'] == "PYTEST_ROUTER_Updated"
        assert 'updated_at' in response.json()['project']
    
    def test_delete_project(self, authenticated_client):
        """DELETE /api/projects/{id} should delete project"""
        # Create project
        project_data = {
            "name": "PYTEST_ROUTER_ToDelete",
            "website_url": "https://todelete.com",
            "brand_name": "ToDeleteBrand"
        }
        create_response = authenticated_client.post(f"{BASE_URL}/api/projects", json=project_data)
        project_id = create_response.json()['project']['project_id']
        
        # Delete project
        response = authenticated_client.delete(f"{BASE_URL}/api/projects/{project_id}")
        assert response.status_code == 200
        assert response.json()['message'] == "Projet supprimé"
        
        # Verify deleted
        get_response = authenticated_client.get(f"{BASE_URL}/api/projects/{project_id}")
        assert get_response.status_code == 404
    
    def test_get_project_stats(self, authenticated_client):
        """GET /api/projects/{id}/stats should return project stats"""
        # Create project
        project_data = {
            "name": "PYTEST_ROUTER_Stats",
            "website_url": "https://stats.com",
            "brand_name": "StatsBrand"
        }
        create_response = authenticated_client.post(f"{BASE_URL}/api/projects", json=project_data)
        project_id = create_response.json()['project']['project_id']
        
        # Get stats
        response = authenticated_client.get(f"{BASE_URL}/api/projects/{project_id}/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert 'project_id' in data
        assert 'total_analyses' in data
        assert 'completed_analyses' in data


class TestDashboardRouter:
    """Tests for /api/dashboard/* endpoints from dashboard.py router"""
    
    def test_dashboard_stats_requires_auth(self, api_client):
        """GET /api/dashboard/stats should return 401 without auth"""
        clean_session = requests.Session()
        response = clean_session.get(f"{BASE_URL}/api/dashboard/stats")
        assert response.status_code == 401
    
    def test_dashboard_stats_returns_data(self, authenticated_client):
        """GET /api/dashboard/stats should return dashboard data"""
        response = authenticated_client.get(f"{BASE_URL}/api/dashboard/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert 'subscription' in data
        assert 'analyses' in data
        assert 'projects' in data
        assert 'average_score' in data
        assert data['subscription']['plan'] == 'pro'
    
    def test_dashboard_quick_stats_returns_data(self, authenticated_client):
        """GET /api/dashboard/quick-stats should return quick stats"""
        response = authenticated_client.get(f"{BASE_URL}/api/dashboard/quick-stats")
        assert response.status_code == 200
        
        data = response.json()
        assert 'current_score' in data
        assert 'grade' in data
        assert 'score_change' in data
        assert 'unread_notifications' in data
        assert 'plan' in data
    
    def test_dashboard_recent_activity_returns_activities(self, authenticated_client):
        """GET /api/dashboard/recent-activity should return activities"""
        response = authenticated_client.get(f"{BASE_URL}/api/dashboard/recent-activity")
        assert response.status_code == 200
        
        data = response.json()
        assert 'activities' in data
        assert isinstance(data['activities'], list)


class TestOrganizationsRouter:
    """Tests for /api/organizations/* endpoints from organizations.py router"""
    
    def test_organizations_requires_auth(self, api_client):
        """GET /api/organizations should return 401 without auth"""
        clean_session = requests.Session()
        response = clean_session.get(f"{BASE_URL}/api/organizations")
        assert response.status_code == 401
    
    def test_get_organizations_returns_list(self, authenticated_client):
        """GET /api/organizations should return organizations list"""
        response = authenticated_client.get(f"{BASE_URL}/api/organizations")
        assert response.status_code == 200
        
        data = response.json()
        assert 'organizations' in data
        assert isinstance(data['organizations'], list)
    
    def test_create_organization(self, authenticated_client):
        """POST /api/organizations should create organization"""
        org_data = {
            "name": "PYTEST_ROUTER_Organization",
            "website_url": "https://pytest-org.com",
            "industry": "Technology",
            "size": "11-50"
        }
        
        response = authenticated_client.post(f"{BASE_URL}/api/organizations", json=org_data)
        assert response.status_code == 200
        
        data = response.json()
        assert 'organization' in data
        assert data['organization']['name'] == "PYTEST_ROUTER_Organization"
        assert 'organization_id' in data['organization']
        assert len(data['organization']['members']) == 1
        assert data['organization']['members'][0]['role'] == 'owner'
    
    def test_get_organization_by_id(self, authenticated_client):
        """GET /api/organizations/{id} should return organization"""
        # Get the organization created in previous test
        list_response = authenticated_client.get(f"{BASE_URL}/api/organizations")
        orgs = list_response.json()['organizations']
        if orgs:
            org_id = orgs[0]['organization_id']
            response = authenticated_client.get(f"{BASE_URL}/api/organizations/{org_id}")
            assert response.status_code == 200
            assert response.json()['organization']['organization_id'] == org_id
    
    def test_update_organization(self, authenticated_client):
        """PUT /api/organizations/{id} should update organization"""
        # Get existing organization
        list_response = authenticated_client.get(f"{BASE_URL}/api/organizations")
        orgs = list_response.json()['organizations']
        if orgs:
            org_id = orgs[0]['organization_id']
            update_data = {"name": "PYTEST_ROUTER_Updated_Org"}
            response = authenticated_client.put(f"{BASE_URL}/api/organizations/{org_id}", json=update_data)
            assert response.status_code == 200
            assert 'updated_at' in response.json()['organization']


class TestOnboardingRouter:
    """Tests for /api/onboarding/* endpoints from onboarding.py router"""
    
    def test_onboarding_tips_dashboard(self, api_client):
        """GET /api/onboarding/tips/dashboard should return tips"""
        response = api_client.get(f"{BASE_URL}/api/onboarding/tips/dashboard")
        assert response.status_code == 200
        
        data = response.json()
        assert 'tips' in data
        assert isinstance(data['tips'], list)
        assert len(data['tips']) > 0
    
    def test_onboarding_tips_analysis(self, api_client):
        """GET /api/onboarding/tips/analysis should return tips"""
        response = api_client.get(f"{BASE_URL}/api/onboarding/tips/analysis")
        assert response.status_code == 200
        
        data = response.json()
        assert 'tips' in data
        assert len(data['tips']) > 0
    
    def test_onboarding_tips_article_optimizer(self, api_client):
        """GET /api/onboarding/tips/article_optimizer should return tips"""
        response = api_client.get(f"{BASE_URL}/api/onboarding/tips/article_optimizer")
        assert response.status_code == 200
        
        data = response.json()
        assert 'tips' in data
        assert len(data['tips']) > 0
    
    def test_onboarding_tips_competitors(self, api_client):
        """GET /api/onboarding/tips/competitors should return tips"""
        response = api_client.get(f"{BASE_URL}/api/onboarding/tips/competitors")
        assert response.status_code == 200
        
        data = response.json()
        assert 'tips' in data
        assert len(data['tips']) > 0
    
    def test_onboarding_tips_unknown_feature(self, api_client):
        """GET /api/onboarding/tips/{unknown} should return empty list"""
        response = api_client.get(f"{BASE_URL}/api/onboarding/tips/unknown_feature")
        assert response.status_code == 200
        
        data = response.json()
        assert 'tips' in data
        assert data['tips'] == []
    
    def test_onboarding_status_requires_auth(self, api_client):
        """GET /api/onboarding/status should require auth"""
        clean_session = requests.Session()
        response = clean_session.get(f"{BASE_URL}/api/onboarding/status")
        assert response.status_code == 401
    
    def test_onboarding_status_returns_data(self, authenticated_client):
        """GET /api/onboarding/status should return onboarding data"""
        response = authenticated_client.get(f"{BASE_URL}/api/onboarding/status")
        assert response.status_code == 200
        
        data = response.json()
        assert 'onboarding' in data
        assert 'steps' in data
        assert 'progress' in data
        assert 'show_onboarding' in data
        assert 'current_step' in data['onboarding']


class TestCleanup:
    """Cleanup test data after tests"""
    
    def test_cleanup_test_data(self):
        """Clean up all test data created during tests"""
        result = subprocess.run([
            'mongosh', '--quiet', '--eval', '''
use('test_database');
var deleted_users = db.users.deleteMany({email: /test\\.router_test\\./});
var deleted_sessions = db.user_sessions.deleteMany({session_token: /test_router_sess_/});
var deleted_subs = db.subscriptions.deleteMany({subscription_id: /sub_router_pytest_/});
var deleted_projects = db.projects.deleteMany({name: /PYTEST_ROUTER/});
var deleted_orgs = db.organizations.deleteMany({name: /PYTEST_ROUTER/});
var deleted_onboarding = db.user_onboarding.deleteMany({user_id: /test-router-/});
print('Cleaned up test data');
'''
        ], capture_output=True, text=True)
        
        assert 'Cleaned up' in result.stdout
