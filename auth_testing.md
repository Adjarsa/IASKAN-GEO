# Auth-Gated App Testing Playbook for IAskan

## Step 1: Create Test User & Session

```bash
mongosh --eval "
use('test_database');
var userId = 'test-user-' + Date.now();
var sessionToken = 'test_session_' + Date.now();
db.users.insertOne({
  user_id: userId,
  email: 'test.user.' + Date.now() + '@example.com',
  name: 'Test User',
  picture: 'https://via.placeholder.com/150',
  created_at: new Date()
});
db.user_sessions.insertOne({
  user_id: userId,
  session_token: sessionToken,
  expires_at: new Date(Date.now() + 7*24*60*60*1000),
  created_at: new Date()
});
db.subscriptions.insertOne({
  subscription_id: 'sub_test_' + Date.now(),
  user_id: userId,
  plan: 'pro',
  status: 'active',
  queries_limit: 600,
  queries_used: 0,
  current_period_start: new Date(),
  current_period_end: new Date(Date.now() + 30*24*60*60*1000),
  created_at: new Date()
});
print('Session token: ' + sessionToken);
print('User ID: ' + userId);
"
```

## Step 2: Test Backend API

```bash
# Test auth endpoint
curl -X GET "https://brand-ai-lens.preview.emergentagent.com/api/auth/me" \
  -H "Authorization: Bearer YOUR_SESSION_TOKEN"

# Test projects endpoint
curl -X GET "https://brand-ai-lens.preview.emergentagent.com/api/projects" \
  -H "Authorization: Bearer YOUR_SESSION_TOKEN"

# Test subscription plans
curl -X GET "https://brand-ai-lens.preview.emergentagent.com/api/subscription/plans"

# Test dashboard stats
curl -X GET "https://brand-ai-lens.preview.emergentagent.com/api/dashboard/stats" \
  -H "Authorization: Bearer YOUR_SESSION_TOKEN"
```

## Step 3: Browser Testing

```javascript
// Set cookie and navigate
await page.context().add_cookies([{
    "name": "session_token",
    "value": "YOUR_SESSION_TOKEN",
    "domain": "geo-visibility.preview.emergentagent.com",
    "path": "/",
    "httpOnly": true,
    "secure": true,
    "sameSite": "None"
}]);
await page.goto("https://brand-ai-lens.preview.emergentagent.com/dashboard");
```

## Quick Debug

```bash
# Check data format
mongosh --eval "
use('test_database');
db.users.find().limit(2).pretty();
db.user_sessions.find().limit(2).pretty();
db.subscriptions.find().limit(2).pretty();
"

# Clean test data
mongosh --eval "
use('test_database');
db.users.deleteMany({email: /test\.user\./});
db.user_sessions.deleteMany({session_token: /test_session/});
db.subscriptions.deleteMany({subscription_id: /sub_test/});
"
```

## Checklist

- [ ] User document has user_id field (custom UUID, MongoDB's _id is separate)
- [ ] Session user_id matches user's user_id exactly
- [ ] All queries use `{"_id": 0}` projection to exclude MongoDB's _id
- [ ] Backend queries use user_id (not _id or id)
- [ ] API returns user data with user_id field (not 401/404)
- [ ] Browser loads dashboard (not login page)
- [ ] CRUD operations work on projects

## Success Indicators

✅ /api/auth/me returns user data
✅ Dashboard loads without redirect
✅ Projects CRUD operations work
✅ Analysis can be started

## Failure Indicators

❌ "User not found" errors
❌ 401 Unauthorized responses
❌ Redirect to login page
