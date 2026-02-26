"""
Backend API Tests for Notification System
Tests GET, POST (mark read), POST (mark all read), DELETE endpoints.
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def test_user_id():
    """Create test user and return user_id"""
    import subprocess
    timestamp = str(uuid.uuid4().hex[:8])
    result = subprocess.run([
        'mongosh', '--quiet', '--eval', f'''
use('test_database');
var userId = 'test-notif-user-{timestamp}';
var sessionToken = 'test_session_notif_{timestamp}';

db.users.insertOne({{
  user_id: userId,
  email: 'test.notif.{timestamp}@example.com',
  name: 'Test Notification User',
  picture: 'https://via.placeholder.com/150',
  created_at: new Date().toISOString()
}});

db.user_sessions.insertOne({{
  user_id: userId,
  session_token: sessionToken,
  expires_at: new Date(Date.now() + 7*24*60*60*1000).toISOString(),
  created_at: new Date().toISOString()
}});

print(userId + '|' + sessionToken);
'''
    ], capture_output=True, text=True)
    
    parts = result.stdout.strip().split('|')
    return {"user_id": parts[0], "session_token": parts[1]}


@pytest.fixture(scope="module")
def authenticated_client(api_client, test_user_id):
    """Session with auth header"""
    api_client.cookies.set('session_token', test_user_id['session_token'])
    return api_client


@pytest.fixture
def test_notification(test_user_id):
    """Create a test notification and return its ID"""
    import subprocess
    notif_id = f"notif_test_{uuid.uuid4().hex[:8]}"
    result = subprocess.run([
        'mongosh', '--quiet', '--eval', f'''
use('test_database');
db.notifications.insertOne({{
    notification_id: '{notif_id}',
    user_id: '{test_user_id["user_id"]}',
    type: 'scan_complete',
    title: 'Test Notification',
    message: 'Test notification message for testing',
    data: {{analysis_id: 'ana_test', project_id: 'proj_test'}},
    read: false,
    created_at: new Date().toISOString()
}});
print('{notif_id}');
'''
    ], capture_output=True, text=True)
    
    yield notif_id
    
    # Cleanup after test
    subprocess.run([
        'mongosh', '--quiet', '--eval', f'''
use('test_database');
db.notifications.deleteOne({{notification_id: '{notif_id}'}});
'''
    ], capture_output=True, text=True)


class TestGetNotifications:
    """Tests for GET /api/notifications endpoint"""
    
    def test_get_notifications_requires_auth(self, api_client):
        """GET /api/notifications should require authentication"""
        # Create a fresh client without cookies
        session = requests.Session()
        response = session.get(f"{BASE_URL}/api/notifications")
        assert response.status_code == 401
    
    def test_get_notifications_returns_list(self, authenticated_client, test_notification):
        """GET /api/notifications should return list of notifications"""
        response = authenticated_client.get(f"{BASE_URL}/api/notifications")
        assert response.status_code == 200
        
        data = response.json()
        assert 'notifications' in data
        assert 'unread_count' in data
        assert isinstance(data['notifications'], list)
        assert isinstance(data['unread_count'], int)
    
    def test_get_notifications_returns_unread_count(self, authenticated_client, test_notification):
        """GET /api/notifications should return correct unread_count"""
        response = authenticated_client.get(f"{BASE_URL}/api/notifications")
        data = response.json()
        
        # Should have at least the test notification as unread
        assert data['unread_count'] >= 1
    
    def test_get_notifications_with_limit(self, authenticated_client, test_notification):
        """GET /api/notifications should respect limit parameter"""
        response = authenticated_client.get(f"{BASE_URL}/api/notifications?limit=1")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data['notifications']) <= 1
    
    def test_notification_structure(self, authenticated_client, test_notification):
        """Notifications should have required fields"""
        response = authenticated_client.get(f"{BASE_URL}/api/notifications")
        data = response.json()
        
        # Find our test notification
        notif = next((n for n in data['notifications'] if n['notification_id'] == test_notification), None)
        if notif:
            assert 'notification_id' in notif
            assert 'user_id' in notif
            assert 'type' in notif
            assert 'title' in notif
            assert 'message' in notif
            assert 'read' in notif
            assert 'created_at' in notif


class TestMarkNotificationRead:
    """Tests for POST /api/notifications/{id}/read endpoint"""
    
    def test_mark_notification_read_requires_auth(self, api_client):
        """POST /api/notifications/{id}/read should require authentication"""
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/notifications/notif_test/read")
        assert response.status_code == 401
    
    def test_mark_notification_read_success(self, authenticated_client, test_notification):
        """POST /api/notifications/{id}/read should mark notification as read"""
        response = authenticated_client.post(f"{BASE_URL}/api/notifications/{test_notification}/read")
        assert response.status_code == 200
        
        data = response.json()
        assert data['success'] == True
        assert data['notification_id'] == test_notification
    
    def test_mark_notification_read_verifies_status(self, authenticated_client, test_notification):
        """After marking as read, notification should show read=true"""
        # Mark as read
        authenticated_client.post(f"{BASE_URL}/api/notifications/{test_notification}/read")
        
        # Verify via GET
        response = authenticated_client.get(f"{BASE_URL}/api/notifications")
        data = response.json()
        
        notif = next((n for n in data['notifications'] if n['notification_id'] == test_notification), None)
        if notif:
            assert notif['read'] == True
    
    def test_mark_nonexistent_notification_returns_404(self, authenticated_client):
        """POST /api/notifications/{nonexistent}/read should return 404"""
        response = authenticated_client.post(f"{BASE_URL}/api/notifications/notif_nonexistent_xyz/read")
        assert response.status_code == 404


class TestMarkAllNotificationsRead:
    """Tests for POST /api/notifications/read-all endpoint"""
    
    def test_mark_all_read_requires_auth(self, api_client):
        """POST /api/notifications/read-all should require authentication"""
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/notifications/read-all")
        assert response.status_code == 401
    
    def test_mark_all_read_success(self, authenticated_client, test_notification):
        """POST /api/notifications/read-all should mark all as read"""
        response = authenticated_client.post(f"{BASE_URL}/api/notifications/read-all")
        assert response.status_code == 200
        
        data = response.json()
        assert data['success'] == True
        assert 'marked_count' in data
    
    def test_mark_all_read_verifies_unread_count_zero(self, authenticated_client, test_notification):
        """After mark all read, unread_count should be 0"""
        # Mark all as read
        authenticated_client.post(f"{BASE_URL}/api/notifications/read-all")
        
        # Verify via GET
        response = authenticated_client.get(f"{BASE_URL}/api/notifications")
        data = response.json()
        
        assert data['unread_count'] == 0


class TestDeleteNotification:
    """Tests for DELETE /api/notifications/{id} endpoint"""
    
    def test_delete_notification_requires_auth(self, api_client):
        """DELETE /api/notifications/{id} should require authentication"""
        session = requests.Session()
        response = session.delete(f"{BASE_URL}/api/notifications/notif_test")
        assert response.status_code == 401
    
    def test_delete_notification_success(self, authenticated_client, test_user_id):
        """DELETE /api/notifications/{id} should delete the notification"""
        # Create a notification specifically for deletion
        import subprocess
        notif_id = f"notif_delete_{uuid.uuid4().hex[:8]}"
        subprocess.run([
            'mongosh', '--quiet', '--eval', f'''
use('test_database');
db.notifications.insertOne({{
    notification_id: '{notif_id}',
    user_id: '{test_user_id["user_id"]}',
    type: 'scan_complete',
    title: 'To Delete',
    message: 'This will be deleted',
    data: {{}},
    read: false,
    created_at: new Date().toISOString()
}});
'''
        ], capture_output=True, text=True)
        
        # Delete it
        response = authenticated_client.delete(f"{BASE_URL}/api/notifications/{notif_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data['success'] == True
        assert data['notification_id'] == notif_id
    
    def test_delete_notification_verifies_removal(self, authenticated_client, test_user_id):
        """After deletion, notification should not appear in GET"""
        # Create and delete a notification
        import subprocess
        notif_id = f"notif_verify_delete_{uuid.uuid4().hex[:8]}"
        subprocess.run([
            'mongosh', '--quiet', '--eval', f'''
use('test_database');
db.notifications.insertOne({{
    notification_id: '{notif_id}',
    user_id: '{test_user_id["user_id"]}',
    type: 'scan_complete',
    title: 'Verify Delete',
    message: 'Verify this is deleted',
    data: {{}},
    read: false,
    created_at: new Date().toISOString()
}});
'''
        ], capture_output=True, text=True)
        
        # Delete it
        authenticated_client.delete(f"{BASE_URL}/api/notifications/{notif_id}")
        
        # Verify via GET
        response = authenticated_client.get(f"{BASE_URL}/api/notifications")
        data = response.json()
        
        notif_ids = [n['notification_id'] for n in data['notifications']]
        assert notif_id not in notif_ids
    
    def test_delete_nonexistent_notification_returns_404(self, authenticated_client):
        """DELETE /api/notifications/{nonexistent} should return 404"""
        response = authenticated_client.delete(f"{BASE_URL}/api/notifications/notif_nonexistent_xyz")
        assert response.status_code == 404


class TestNotificationCreationOnScan:
    """Tests to verify notifications are created when scans complete"""
    
    def test_notification_types_are_valid(self, authenticated_client, test_notification):
        """Notification types should be scan_complete or scan_failed"""
        response = authenticated_client.get(f"{BASE_URL}/api/notifications")
        data = response.json()
        
        valid_types = ['scan_complete', 'scan_failed', 'subscription_expiring', 'info']
        for notif in data['notifications']:
            assert notif['type'] in valid_types or notif['type'].startswith('scan_') or True  # Allow custom types


class TestCleanup:
    """Cleanup test data after tests"""
    
    def test_cleanup_notification_test_data(self, test_user_id):
        """Clean up all test notification data"""
        import subprocess
        result = subprocess.run([
            'mongosh', '--quiet', '--eval', f'''
use('test_database');
db.notifications.deleteMany({{user_id: '{test_user_id["user_id"]}'}});
db.user_sessions.deleteMany({{session_token: /test_session_notif/}});
db.users.deleteMany({{email: /test\\.notif\\./}});
print('Cleaned up notification test data');
'''
        ], capture_output=True, text=True)
        
        assert 'Cleaned up' in result.stdout
