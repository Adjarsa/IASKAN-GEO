import { test, expect } from '@playwright/test';
import { waitForAppReady, hideEmergentBadge, dismissToasts } from '../fixtures/helpers';

test.describe('Authenticated Pages - Dashboard & Analysis', () => {
  
  test.beforeEach(async ({ page }) => {
    // Set up test session cookie
    await page.context().addCookies([{
      name: 'session_token',
      value: 'test_session_1772018666518',
      domain: 'visibility-ai-5.preview.emergentagent.com',
      path: '/',
      httpOnly: true,
      secure: true,
      sameSite: 'None'
    }]);
    
    await dismissToasts(page);
  });

  test.describe('Project Selector Page', () => {
    
    test('should load project selector for authenticated user', async ({ page }) => {
      await page.goto('/projects');
      await waitForAppReady(page);
      await hideEmergentBadge(page);
      
      // Check for project selector elements
      await expect(page.getByText('Vos Projets')).toBeVisible();
      await expect(page.getByText('Nouveau Projet')).toBeVisible();
    });

    test('should show test project in projects list', async ({ page }) => {
      await page.goto('/projects');
      await waitForAppReady(page);
      await hideEmergentBadge(page);
      
      // Check for the test project
      await expect(page.getByText('TEST_GEO_Project')).toBeVisible();
      await expect(page.getByText('TEST_GEO_Brand')).toBeVisible();
    });

    test('should navigate to dashboard when selecting a project', async ({ page }) => {
      await page.goto('/projects');
      await waitForAppReady(page);
      await hideEmergentBadge(page);
      
      // Click on the test project card
      await page.getByText('TEST_GEO_Project').click();
      
      // Should navigate to dashboard
      await page.waitForURL(/\/dashboard/);
      await expect(page.getByTestId('dashboard-page')).toBeVisible();
    });
  });

  test.describe('Dashboard Page', () => {
    
    test.beforeEach(async ({ page }) => {
      // First select a project to access dashboard
      await page.goto('/projects');
      await waitForAppReady(page);
      await hideEmergentBadge(page);
      
      // Click on the test project
      await page.getByText('TEST_GEO_Project').click();
      await page.waitForURL(/\/dashboard/);
    });

    test('should load dashboard page after selecting project', async ({ page }) => {
      await expect(page.getByTestId('dashboard-page')).toBeVisible();
    });

    test('should display brand name on dashboard', async ({ page }) => {
      await expect(page.getByRole('heading', { name: 'TEST_GEO_Brand' })).toBeVisible();
    });

    test('should have new analysis button', async ({ page }) => {
      await expect(page.getByTestId('new-analysis-btn')).toBeVisible();
    });

    test('should have refresh stats button', async ({ page }) => {
      await expect(page.getByTestId('refresh-stats')).toBeVisible();
    });

    test('should display IAskan Verified badge or no analysis message', async ({ page }) => {
      // Wait for dashboard to finish loading
      await page.waitForSelector('[data-testid="dashboard-page"]', { state: 'visible' });
      
      // Wait a bit for content to load
      await page.waitForLoadState('networkidle');
      
      // Either show indices section or no analysis message
      const noAnalysisText = page.getByText('Aucune analyse effectuée');
      const indicesBadge = page.getByText('IAskan Verified™');
      const startFirstAnalysis = page.getByTestId('start-first-analysis');
      
      // One of these should be visible (either indices, no analysis message, or start button)
      const noAnalysisVisible = await noAnalysisText.isVisible().catch(() => false);
      const badgeVisible = await indicesBadge.first().isVisible().catch(() => false);
      const startVisible = await startFirstAnalysis.isVisible().catch(() => false);
      
      expect(noAnalysisVisible || badgeVisible || startVisible).toBeTruthy();
    });
  });

  test.describe('Analysis Page Structure', () => {
    
    test.beforeEach(async ({ page }) => {
      // First select a project
      await page.goto('/projects');
      await waitForAppReady(page);
      await hideEmergentBadge(page);
      await page.getByText('TEST_GEO_Project').click();
      await page.waitForURL(/\/dashboard/);
    });

    test('should navigate to analysis page from dashboard', async ({ page }) => {
      await page.getByTestId('new-analysis-btn').click();
      await expect(page).toHaveURL(/\/analysis/);
    });
  });
});
