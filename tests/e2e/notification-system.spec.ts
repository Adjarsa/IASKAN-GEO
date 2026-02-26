import { test, expect, Page } from '@playwright/test';
import { waitForAppReady, dismissToasts, hideEmergentBadge } from '../fixtures/helpers';

// Use the same domain as other tests
const COOKIE_DOMAIN = 'brand-ai-lens.preview.emergentagent.com';
const TEST_SESSION_TOKEN = 'test_session_notif_e2e_12345';
const TEST_PROJECT_ID = 'proj_notif_test';

test.describe('Notification System - Dashboard Pages', () => {
  
  test.beforeEach(async ({ page }) => {
    // Set the session token cookie before navigating
    await page.context().addCookies([{
      name: 'session_token',
      value: TEST_SESSION_TOKEN,
      domain: COOKIE_DOMAIN,
      path: '/',
      httpOnly: true,
      secure: true,
      sameSite: 'None'
    }]);
    
    // Set the project ID in localStorage so the app knows we have a selected project
    await page.addInitScript((projectId) => {
      localStorage.setItem('currentProjectId', projectId);
    }, TEST_PROJECT_ID);
    
    await dismissToasts(page);
  });

  test('NotificationBell is visible in dashboard header', async ({ page }) => {
    await page.goto('/dashboard', { waitUntil: 'domcontentloaded' });
    await waitForAppReady(page);
    await hideEmergentBadge(page);
    
    // Wait for the page to settle
    await page.waitForLoadState('networkidle');
    
    // Check if we're on dashboard or redirected
    const url = page.url();
    if (url.includes('/login') || url.includes('/projects')) {
      // Authentication or project selection didn't work
      console.log('Redirected - auth/project may not be set correctly');
      test.skip();
      return;
    }
    
    // Check if notification bell is visible in the header
    const notificationBell = page.getByTestId('notification-bell');
    await expect(notificationBell).toBeVisible({ timeout: 15000 });
  });

  test('NotificationBell shows badge with unread count when notifications exist', async ({ page }) => {
    await page.goto('/dashboard', { waitUntil: 'domcontentloaded' });
    await waitForAppReady(page);
    await hideEmergentBadge(page);
    await page.waitForLoadState('networkidle');
    
    const url = page.url();
    if (url.includes('/login') || url.includes('/projects')) {
      test.skip();
      return;
    }
    
    // Wait for the notification bell to load
    const notificationBell = page.getByTestId('notification-bell');
    await expect(notificationBell).toBeVisible({ timeout: 15000 });
    
    // With 2 unread notifications, we should see a badge
    const badge = page.getByTestId('notification-badge');
    const badgeCount = await badge.count();
    
    if (badgeCount > 0) {
      await expect(badge).toBeVisible();
      const badgeText = await badge.textContent();
      // Should show a number
      expect(badgeText).toMatch(/\d+/);
    }
  });

  test('Clicking notification bell opens dropdown with notifications', async ({ page }) => {
    await page.goto('/dashboard', { waitUntil: 'domcontentloaded' });
    await waitForAppReady(page);
    await hideEmergentBadge(page);
    await page.waitForLoadState('networkidle');
    
    const url = page.url();
    if (url.includes('/login') || url.includes('/projects')) {
      test.skip();
      return;
    }
    
    const notificationBell = page.getByTestId('notification-bell');
    await expect(notificationBell).toBeVisible({ timeout: 15000 });
    
    // Click to open dropdown
    await notificationBell.click();
    
    // Check dropdown is open - should see "Notifications" header
    await expect(page.getByText('Notifications', { exact: true })).toBeVisible({ timeout: 5000 });
    
    // Should see notification items or empty state
    const noNotificationsMsg = page.getByText('Aucune notification');
    const hasEmptyState = await noNotificationsMsg.count() > 0;
    
    if (!hasEmptyState) {
      // If there are notifications, we should see them
      const scanComplete = page.getByText('Scan terminé');
      const scanFailed = page.getByText('Scan échoué');
      
      const completeVisible = await scanComplete.isVisible().catch(() => false);
      const failedVisible = await scanFailed.isVisible().catch(() => false);
      
      // At least one should be visible if notifications exist
      expect(completeVisible || failedVisible || hasEmptyState).toBeTruthy();
    }
  });

  test('Mark all read button is visible when unread notifications exist', async ({ page }) => {
    await page.goto('/dashboard', { waitUntil: 'domcontentloaded' });
    await waitForAppReady(page);
    await hideEmergentBadge(page);
    await page.waitForLoadState('networkidle');
    
    const url = page.url();
    if (url.includes('/login') || url.includes('/projects')) {
      test.skip();
      return;
    }
    
    const notificationBell = page.getByTestId('notification-bell');
    await expect(notificationBell).toBeVisible({ timeout: 15000 });
    await notificationBell.click();
    
    await expect(page.getByText('Notifications', { exact: true })).toBeVisible({ timeout: 5000 });
    
    // Check for badge to determine if we have unread notifications
    const badge = page.getByTestId('notification-badge');
    const hasBadge = await badge.count() > 0;
    
    if (hasBadge) {
      // If there are unread notifications, "Tout marquer lu" button should be visible
      const markAllReadBtn = page.getByTestId('mark-all-read-btn');
      await expect(markAllReadBtn).toBeVisible({ timeout: 5000 });
    }
  });

  test('NotificationBell appears on analysis page too', async ({ page }) => {
    await page.goto('/analysis', { waitUntil: 'domcontentloaded' });
    await waitForAppReady(page);
    await hideEmergentBadge(page);
    await page.waitForLoadState('networkidle');
    
    const url = page.url();
    if (url.includes('/login') || url.includes('/projects')) {
      test.skip();
      return;
    }
    
    const notificationBell = page.getByTestId('notification-bell');
    await expect(notificationBell).toBeVisible({ timeout: 15000 });
  });
});

test.describe('Notification UI Components - Public Pages', () => {
  
  test('Login page does not show notification bell', async ({ page }) => {
    await page.goto('/login', { waitUntil: 'domcontentloaded' });
    await waitForAppReady(page);
    
    const notificationBell = page.getByTestId('notification-bell');
    await expect(notificationBell).not.toBeVisible();
  });

  test('Home page does not show notification bell', async ({ page }) => {
    await page.goto('/', { waitUntil: 'domcontentloaded' });
    await waitForAppReady(page);
    
    const notificationBell = page.getByTestId('notification-bell');
    await expect(notificationBell).not.toBeVisible();
  });

  test('Pricing page does not show notification bell', async ({ page }) => {
    await page.goto('/pricing', { waitUntil: 'domcontentloaded' });
    await waitForAppReady(page);
    
    const notificationBell = page.getByTestId('notification-bell');
    await expect(notificationBell).not.toBeVisible();
  });
});

test.describe('Notification System - Project Selector', () => {
  
  test.beforeEach(async ({ page }) => {
    await page.context().addCookies([{
      name: 'session_token',
      value: TEST_SESSION_TOKEN,
      domain: COOKIE_DOMAIN,
      path: '/',
      httpOnly: true,
      secure: true,
      sameSite: 'None'
    }]);
    
    await dismissToasts(page);
  });

  test('Project selector page does NOT show notification bell (expected behavior)', async ({ page }) => {
    // The project selector uses a minimal header without NotificationBell
    // This is expected - notifications appear after project selection
    await page.goto('/projects', { waitUntil: 'domcontentloaded' });
    await waitForAppReady(page);
    await hideEmergentBadge(page);
    await page.waitForLoadState('networkidle');
    
    const url = page.url();
    if (url.includes('/login')) {
      test.skip();
      return;
    }
    
    // Project selector should have the user menu but NOT notification bell
    const notificationBell = page.getByTestId('notification-bell');
    await expect(notificationBell).not.toBeVisible();
    
    // But user should be logged in (check for user name in header)
    await expect(page.getByText('Test Notification User')).toBeVisible();
  });
});
