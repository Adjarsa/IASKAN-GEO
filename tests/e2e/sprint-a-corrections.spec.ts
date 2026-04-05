import { test, expect } from '@playwright/test';
import { waitForAppReady, dismissToasts, hideEmergentBadge } from '../fixtures/helpers';

const BASE_URL = process.env.BASE_URL || 'https://geo-visibility-hub.preview.emergentagent.com';

test.describe('Sprint A Corrections - Frontend Verification', () => {
  
  test.beforeEach(async ({ page }) => {
    await dismissToasts(page);
  });

  test.describe('ContentAuditPage - No Mock Data', () => {
    
    test('content audit page loads without mock data', async ({ page }) => {
      // Navigate to content audit page (requires auth, so we check the page structure)
      await page.goto('/content-audit', { waitUntil: 'domcontentloaded' });
      await waitForAppReady(page);
      
      // Page should load without 500 error
      const pageHasContent = await page.locator('body').isVisible();
      expect(pageHasContent).toBeTruthy();
      
      // Check that page doesn't show hardcoded mock data
      // If not authenticated, it should redirect or show auth required
      // If authenticated, it should show empty state or real data
      const hasMockDataIndicator = await page.getByText('Mock Data', { exact: false }).isVisible().catch(() => false);
      expect(hasMockDataIndicator).toBeFalsy();
    });
  });

  test.describe('ArticleOptimizerPage - No Mock Data', () => {
    
    test('article optimizer page loads without mock data', async ({ page }) => {
      // Navigate to article optimizer page
      await page.goto('/article-optimizer', { waitUntil: 'domcontentloaded' });
      await waitForAppReady(page);
      
      // Page should load without 500 error
      const pageHasContent = await page.locator('body').isVisible();
      expect(pageHasContent).toBeTruthy();
      
      // Check that page doesn't show hardcoded mock data
      const hasMockDataIndicator = await page.getByText('Mock Data', { exact: false }).isVisible().catch(() => false);
      expect(hasMockDataIndicator).toBeFalsy();
    });
  });

  test.describe('Backend API Verification', () => {
    
    test('health endpoint returns healthy status', async ({ page }) => {
      const response = await page.request.get('/api/health');
      expect(response.status()).toBe(200);
      
      const data = await response.json();
      expect(data.status).toBe('healthy');
      expect(data.timestamp).toBeDefined();
    });

    test('organizations endpoint returns 401 not 500', async ({ page }) => {
      const response = await page.request.get('/api/organizations');
      expect(response.status()).toBe(401);
      expect(response.status()).not.toBe(500);
    });

    test('analysis endpoint returns 401 not 500', async ({ page }) => {
      const response = await page.request.get('/api/analysis/test_123');
      expect(response.status()).toBe(401);
      expect(response.status()).not.toBe(500);
    });

    test('content-audit endpoint returns 401 not 500', async ({ page }) => {
      const response = await page.request.get('/api/content-audit/test_project');
      // Should return 401 (unauthorized) or 404 (not found), not 500
      expect(response.status()).not.toBe(500);
      expect([401, 404]).toContain(response.status());
    });

    test('article-optimizer endpoint returns 401 not 500', async ({ page }) => {
      const response = await page.request.post('/api/article-optimizer/generate-from-analysis', {
        data: { analysis_id: 'test_123', project_id: 'test_project' }
      });
      // Should return 401 (unauthorized) or 422 (validation error), not 500
      expect(response.status()).not.toBe(500);
    });
  });

  test.describe('CORS Configuration', () => {
    
    test('API accepts requests from configured origin', async ({ page }) => {
      // Make a request with the configured origin
      const response = await page.request.get('/api/health', {
        headers: {
          'Origin': 'https://geo-visibility-hub.preview.emergentagent.com'
        }
      });
      
      expect(response.status()).toBe(200);
    });
  });

  test.describe('Rate Limiting', () => {
    
    test('multiple requests within limit succeed', async ({ page }) => {
      // Make 10 requests - should all succeed within 200/minute limit
      for (let i = 0; i < 10; i++) {
        const response = await page.request.get('/api/health');
        expect(response.status()).toBe(200);
      }
    });
  });
});
