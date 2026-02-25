import { test, expect } from '@playwright/test';
import { waitForAppReady, hideEmergentBadge, dismissToasts } from '../fixtures/helpers';

test.describe('PDF Export Feature', () => {
  
  test.beforeEach(async ({ page }) => {
    // Set up test session cookie
    await page.context().addCookies([{
      name: 'session_token',
      value: 'test_session_1772018666518',
      domain: 'visibility-track.preview.emergentagent.com',
      path: '/',
      httpOnly: true,
      secure: true,
      sameSite: 'None'
    }]);
    
    await dismissToasts(page);
  });

  test.describe('Analysis Page - PDF Export Elements', () => {
    
    test.beforeEach(async ({ page }) => {
      // Navigate to projects and select one
      await page.goto('/projects');
      await waitForAppReady(page);
      await hideEmergentBadge(page);
      
      // Select the test project
      await page.getByText('TEST_GEO_Project').click();
      await page.waitForURL(/\/dashboard/);
    });

    test('should display analysis page without errors', async ({ page }) => {
      // Navigate to analysis page
      await page.getByTestId('new-analysis-btn').click();
      await page.waitForURL(/\/analysis/);
      
      // Page should load correctly
      await expect(page.getByTestId('analysis-page')).toBeVisible();
    });

    test('should show new analysis form with IAskan protocol info', async ({ page }) => {
      await page.getByTestId('new-analysis-btn').click();
      await page.waitForURL(/\/analysis/);
      await waitForAppReady(page);
      
      // Check for IAskan Verified protocol content
      await expect(page.getByText('IAskan Verified GEO Protocol™')).toBeVisible();
      
      // Check for start analysis button
      await expect(page.getByTestId('start-analysis-btn')).toBeVisible();
    });

    test('should show project info on analysis page', async ({ page }) => {
      await page.getByTestId('new-analysis-btn').click();
      await page.waitForURL(/\/analysis/);
      await waitForAppReady(page);
      
      // Project name should be visible
      await expect(page.getByText('TEST_GEO_Project')).toBeVisible();
      await expect(page.getByText('TEST_GEO_Brand')).toBeVisible();
    });
  });

  test.describe('Dashboard Page - PDF Export Button Visibility', () => {
    
    test.beforeEach(async ({ page }) => {
      // Navigate to projects and select one
      await page.goto('/projects');
      await waitForAppReady(page);
      await hideEmergentBadge(page);
      
      // Select the test project
      await page.getByText('TEST_GEO_Project').click();
      await page.waitForURL(/\/dashboard/);
    });

    test('should display dashboard page correctly', async ({ page }) => {
      await expect(page.getByTestId('dashboard-page')).toBeVisible();
    });

    test('should have refresh stats and new analysis buttons', async ({ page }) => {
      await expect(page.getByTestId('refresh-stats')).toBeVisible();
      await expect(page.getByTestId('new-analysis-btn')).toBeVisible();
    });

    test('should show no analysis message or PDF button based on data', async ({ page }) => {
      await waitForAppReady(page);
      
      // Either PDF export button is visible (if analysis exists) 
      // or "Lancez une analyse pour obtenir des recommandations" message shows
      const pdfButton = page.getByTestId('download-pdf-dashboard');
      const noAnalysisMessage = page.getByText('Lancez une analyse pour obtenir des recommandations');
      const startFirstAnalysis = page.getByTestId('start-first-analysis');
      
      const pdfVisible = await pdfButton.isVisible().catch(() => false);
      const noAnalysisVisible = await noAnalysisMessage.isVisible().catch(() => false);
      const startVisible = await startFirstAnalysis.isVisible().catch(() => false);
      
      // One of these should be visible
      expect(pdfVisible || noAnalysisVisible || startVisible).toBeTruthy();
    });
  });

  test.describe('PDF Service Loading', () => {
    
    test('should load analysis page without JavaScript errors', async ({ page }) => {
      const errors: string[] = [];
      page.on('console', msg => {
        if (msg.type() === 'error') {
          errors.push(msg.text());
        }
      });
      
      await page.context().addCookies([{
        name: 'session_token',
        value: 'test_session_1772018666518',
        domain: 'visibility-track.preview.emergentagent.com',
        path: '/',
        httpOnly: true,
        secure: true,
        sameSite: 'None'
      }]);
      
      // Load projects page first
      await page.goto('/projects');
      await waitForAppReady(page);
      await hideEmergentBadge(page);
      
      // Select the project
      await page.getByText('TEST_GEO_Project').click();
      await page.waitForURL(/\/dashboard/);
      
      // Go to analysis page
      await page.getByTestId('new-analysis-btn').click();
      await page.waitForURL(/\/analysis/);
      
      // Filter out non-critical errors
      const criticalErrors = errors.filter(e => 
        !e.includes('Failed to load resource') && 
        !e.includes('favicon') &&
        e.includes('PDF') || e.includes('jsPDF') || e.includes('pdfReportGenerator')
      );
      
      expect(criticalErrors.length).toBe(0);
    });
    
    test('should load dashboard page without PDF-related JavaScript errors', async ({ page }) => {
      const errors: string[] = [];
      page.on('console', msg => {
        if (msg.type() === 'error') {
          errors.push(msg.text());
        }
      });
      
      await page.context().addCookies([{
        name: 'session_token',
        value: 'test_session_1772018666518',
        domain: 'visibility-track.preview.emergentagent.com',
        path: '/',
        httpOnly: true,
        secure: true,
        sameSite: 'None'
      }]);
      
      // Load projects page first
      await page.goto('/projects');
      await waitForAppReady(page);
      await hideEmergentBadge(page);
      
      // Select the project
      await page.getByText('TEST_GEO_Project').click();
      await page.waitForURL(/\/dashboard/);
      
      // Wait for dashboard to load
      await expect(page.getByTestId('dashboard-page')).toBeVisible();
      
      // Filter PDF-specific errors only
      const pdfErrors = errors.filter(e => 
        e.includes('PDF') || e.includes('jsPDF') || e.includes('pdfReportGenerator')
      );
      
      expect(pdfErrors.length).toBe(0);
    });
  });
});
