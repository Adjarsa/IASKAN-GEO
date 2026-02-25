import { test, expect } from '@playwright/test';
import { waitForAppReady, hideEmergentBadge, dismissToasts } from '../fixtures/helpers';

const TEST_SESSION_TOKEN = 'test_session_1772018666518';
const TEST_DOMAIN = 'visibility-ai-5.preview.emergentagent.com';

test.describe('GEO Features - Visibility & Content Audit', () => {
  
  test.beforeEach(async ({ page }) => {
    // Set up test session cookie
    await page.context().addCookies([{
      name: 'session_token',
      value: TEST_SESSION_TOKEN,
      domain: TEST_DOMAIN,
      path: '/',
      httpOnly: true,
      secure: true,
      sameSite: 'None'
    }]);
    
    await dismissToasts(page);
  });

  test.describe('Navigation Updates', () => {
    
    test('should display new navigation entries in sidebar', async ({ page }) => {
      // First select a project
      await page.goto('/projects');
      await waitForAppReady(page);
      await hideEmergentBadge(page);
      
      // Click on the test project
      await page.getByText('TEST_GEO_Project').click();
      await page.waitForURL(/\/dashboard/);
      await hideEmergentBadge(page);
      
      // Check for new navigation entries
      await expect(page.getByTestId('nav-visibilite')).toBeVisible();
      await expect(page.getByTestId('nav-audit contenu')).toBeVisible();
      await expect(page.getByTestId('nav-generateur')).toBeVisible();
      await expect(page.getByTestId('nav-benchmark')).toBeVisible();
    });

    test('should navigate to Visibility page from sidebar', async ({ page }) => {
      await page.goto('/projects');
      await waitForAppReady(page);
      await hideEmergentBadge(page);
      
      await page.getByText('TEST_GEO_Project').click();
      await page.waitForURL(/\/dashboard/);
      await hideEmergentBadge(page);
      
      // Click on Visibilite nav item
      await page.getByTestId('nav-visibilite').click();
      await page.waitForURL(/\/visibility/);
      await expect(page.getByTestId('visibility-page')).toBeVisible();
    });

    test('should navigate to Content Audit page from sidebar', async ({ page }) => {
      await page.goto('/projects');
      await waitForAppReady(page);
      await hideEmergentBadge(page);
      
      await page.getByText('TEST_GEO_Project').click();
      await page.waitForURL(/\/dashboard/);
      await hideEmergentBadge(page);
      
      // Click on Audit Contenu nav item
      await page.getByTestId('nav-audit contenu').click();
      await page.waitForURL(/\/content-audit/);
      await expect(page.getByTestId('content-audit-page')).toBeVisible();
    });

    test('should navigate to Content Generator page from sidebar', async ({ page }) => {
      await page.goto('/projects');
      await waitForAppReady(page);
      await hideEmergentBadge(page);
      
      await page.getByText('TEST_GEO_Project').click();
      await page.waitForURL(/\/dashboard/);
      await hideEmergentBadge(page);
      
      // Click on Generateur nav item
      await page.getByTestId('nav-generateur').click();
      await page.waitForURL(/\/content-generator/);
      await expect(page.getByTestId('content-generator-page')).toBeVisible();
    });
  });

  test.describe('Visibility Page', () => {
    
    test.beforeEach(async ({ page }) => {
      // Select project first
      await page.goto('/projects');
      await waitForAppReady(page);
      await hideEmergentBadge(page);
      await page.getByText('TEST_GEO_Project').click();
      await page.waitForURL(/\/dashboard/);
    });

    test('should load Visibility page correctly', async ({ page }) => {
      await page.goto('/visibility');
      await waitForAppReady(page);
      await hideEmergentBadge(page);
      
      await expect(page.getByTestId('visibility-page')).toBeVisible();
    });

    test('should display page title and description', async ({ page }) => {
      await page.goto('/visibility');
      await waitForAppReady(page);
      await hideEmergentBadge(page);
      
      await expect(page.getByText('Visibilite Generative')).toBeVisible();
      await expect(page.getByText('Tracking de presence dans les reponses des moteurs IA generatifs')).toBeVisible();
    });

    test('should display global visibility score', async ({ page }) => {
      await page.goto('/visibility');
      await waitForAppReady(page);
      await hideEmergentBadge(page);
      
      // Should show global visibility score section
      await expect(page.getByText('Score de Visibilite Globale')).toBeVisible();
    });

    test('should have refresh button', async ({ page }) => {
      await page.goto('/visibility');
      await waitForAppReady(page);
      await hideEmergentBadge(page);
      
      await expect(page.getByTestId('refresh-visibility')).toBeVisible();
    });

    test('should display AI engines breakdown section', async ({ page }) => {
      await page.goto('/visibility');
      await waitForAppReady(page);
      await hideEmergentBadge(page);
      
      // Check for AI engines section (data may be empty without analysis)
      await expect(page.getByText('Score par moteur generatif')).toBeVisible();
    });

    test('should display position distribution', async ({ page }) => {
      await page.goto('/visibility');
      await waitForAppReady(page);
      await hideEmergentBadge(page);
      
      await expect(page.getByText('Distribution des positions')).toBeVisible();
    });

    test('should display thematic visibility section', async ({ page }) => {
      await page.goto('/visibility');
      await waitForAppReady(page);
      await hideEmergentBadge(page);
      
      await expect(page.getByText('Visibilite par thematique')).toBeVisible();
    });

    test('should display IAskan Verified badge', async ({ page }) => {
      await page.goto('/visibility');
      await waitForAppReady(page);
      await hideEmergentBadge(page);
      
      await expect(page.getByText('IAskan Verified')).toBeVisible();
    });
  });

  test.describe('Content Audit Page', () => {
    
    test.beforeEach(async ({ page }) => {
      // Select project first
      await page.goto('/projects');
      await waitForAppReady(page);
      await hideEmergentBadge(page);
      await page.getByText('TEST_GEO_Project').click();
      await page.waitForURL(/\/dashboard/);
    });

    test('should load Content Audit page correctly', async ({ page }) => {
      await page.goto('/content-audit');
      await waitForAppReady(page);
      await hideEmergentBadge(page);
      
      await expect(page.getByTestId('content-audit-page')).toBeVisible();
    });

    test('should display page title and description', async ({ page }) => {
      await page.goto('/content-audit');
      await waitForAppReady(page);
      await hideEmergentBadge(page);
      
      await expect(page.getByText('Audit de Contenu')).toBeVisible();
      await expect(page.getByText('Analysez la citabilite de vos pages par les moteurs IA generatifs')).toBeVisible();
    });

    test('should display citability score card', async ({ page }) => {
      await page.goto('/content-audit');
      await waitForAppReady(page);
      await hideEmergentBadge(page);
      
      await expect(page.getByText('Score Citabilite')).toBeVisible();
    });

    test('should display structure score card', async ({ page }) => {
      await page.goto('/content-audit');
      await waitForAppReady(page);
      await hideEmergentBadge(page);
      
      // Use exact match for Structure card label
      await expect(page.getByText('Structure', { exact: true }).first()).toBeVisible();
    });

    test('should display schema.org coverage card', async ({ page }) => {
      await page.goto('/content-audit');
      await waitForAppReady(page);
      await hideEmergentBadge(page);
      
      await expect(page.getByText('Schema.org')).toBeVisible();
    });

    test('should have refresh button', async ({ page }) => {
      await page.goto('/content-audit');
      await waitForAppReady(page);
      await hideEmergentBadge(page);
      
      await expect(page.getByTestId('refresh-audit')).toBeVisible();
    });

    test('should display content gaps section', async ({ page }) => {
      await page.goto('/content-audit');
      await waitForAppReady(page);
      await hideEmergentBadge(page);
      
      await expect(page.getByText('Lacunes detectees - Opportunites manquees')).toBeVisible();
    });

    test('should display page analysis section', async ({ page }) => {
      await page.goto('/content-audit');
      await waitForAppReady(page);
      await hideEmergentBadge(page);
      
      await expect(page.getByText('Analyse page par page')).toBeVisible();
    });

    test('should display structure recommendations section', async ({ page }) => {
      await page.goto('/content-audit');
      await waitForAppReady(page);
      await hideEmergentBadge(page);
      
      await expect(page.getByText('Recommandations de structure')).toBeVisible();
    });

    test('should display citability info box', async ({ page }) => {
      await page.goto('/content-audit');
      await waitForAppReady(page);
      await hideEmergentBadge(page);
      
      await expect(page.getByText("Qu'est-ce que la citabilite ?")).toBeVisible();
    });
  });
});
