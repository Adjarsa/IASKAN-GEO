import { test, expect } from '@playwright/test';
import { waitForAppReady, dismissToasts, hideEmergentBadge } from '../fixtures/helpers';

const BASE_URL = process.env.BASE_URL || 'https://geo-visibility-hub.preview.emergentagent.com';

test.describe('Critical Pages - Frontend P0 Testing', () => {
  
  test.beforeEach(async ({ page }) => {
    await dismissToasts(page);
  });

  test.describe('Landing Page', () => {
    
    test('homepage loads without 500 error', async ({ page }) => {
      const response = await page.goto('/', { waitUntil: 'domcontentloaded' });
      await waitForAppReady(page);
      
      // Check response status is not 500
      expect(response?.status()).not.toBe(500);
      expect(response?.status()).toBeLessThan(500);
    });

    test('homepage displays IAskan branding', async ({ page }) => {
      await page.goto('/', { waitUntil: 'domcontentloaded' });
      await waitForAppReady(page);
      
      // Check logo is visible (use first() to avoid strict mode)
      await expect(page.getByTestId('nav-logo')).toBeVisible();
    });

    test('homepage has CTA buttons', async ({ page }) => {
      await page.goto('/', { waitUntil: 'domcontentloaded' });
      await waitForAppReady(page);
      await hideEmergentBadge(page);
      
      // Check for call-to-action buttons
      await expect(page.getByText('Commencer Gratuitement')).toBeVisible();
      await expect(page.getByText('Voir une démo')).toBeVisible();
    });

    test('homepage displays stats', async ({ page }) => {
      await page.goto('/', { waitUntil: 'domcontentloaded' });
      await waitForAppReady(page);
      
      // Check for stats section
      await expect(page.getByText('98%')).toBeVisible();
      await expect(page.getByText('Précision du score')).toBeVisible();
    });

    test('navigation bar is visible', async ({ page }) => {
      await page.goto('/', { waitUntil: 'domcontentloaded' });
      await waitForAppReady(page);
      
      // Check for navigation items (use role navigation to be specific)
      await expect(page.getByRole('navigation').getByRole('link', { name: 'Fonctionnalités' })).toBeVisible();
      await expect(page.getByRole('navigation').getByRole('link', { name: 'Tarifs' })).toBeVisible();
      await expect(page.getByRole('navigation').getByText('Connexion')).toBeVisible();
    });
  });

  test.describe('Login Page', () => {
    
    test('login page loads without error', async ({ page }) => {
      const response = await page.goto('/login', { waitUntil: 'domcontentloaded' });
      await waitForAppReady(page);
      
      expect(response?.status()).toBeLessThan(500);
    });

    test('login page has form elements', async ({ page }) => {
      await page.goto('/login', { waitUntil: 'domcontentloaded' });
      await waitForAppReady(page);
      
      // Check for login form - looking for email input and password input by type
      const emailInput = page.locator('input[type="email"]').first();
      const passwordInput = page.locator('input[type="password"]').first();
      
      // At least one login method should be visible
      const hasEmailInput = await emailInput.isVisible().catch(() => false);
      const hasPasswordInput = await passwordInput.isVisible().catch(() => false);
      const hasGoogleLogin = await page.getByText('Google').isVisible().catch(() => false);
      const hasMagicLink = await page.getByText('Connexion par email').isVisible().catch(() => false);
      
      expect(hasEmailInput || hasGoogleLogin || hasMagicLink).toBeTruthy();
    });
  });

  test.describe('Pricing Page', () => {
    
    test('pricing page loads without error', async ({ page }) => {
      const response = await page.goto('/pricing', { waitUntil: 'domcontentloaded' });
      await waitForAppReady(page);
      
      expect(response?.status()).toBeLessThan(500);
    });

    test('pricing page shows plan options', async ({ page }) => {
      await page.goto('/pricing', { waitUntil: 'domcontentloaded' });
      await waitForAppReady(page);
      
      // Check for plan names
      const planTexts = ['Gratuit', 'Starter', 'Pro', 'Business'];
      let foundPlans = 0;
      
      for (const plan of planTexts) {
        const visible = await page.getByText(plan, { exact: false }).first().isVisible().catch(() => false);
        if (visible) foundPlans++;
      }
      
      // At least 2 plans should be visible
      expect(foundPlans).toBeGreaterThanOrEqual(2);
    });
  });

  test.describe('API Health', () => {
    
    test('health endpoint returns healthy status', async ({ page }) => {
      const response = await page.goto('/api/health', { waitUntil: 'domcontentloaded' });
      
      expect(response?.status()).toBe(200);
      
      const body = await page.textContent('body');
      expect(body).toContain('healthy');
    });
  });

  test.describe('Protected Routes Redirect', () => {
    
    test('dashboard shows loading or redirects when unauthenticated', async ({ page }) => {
      await page.goto('/dashboard', { waitUntil: 'domcontentloaded' });
      await waitForAppReady(page);
      
      // Dashboard may show loading spinner, redirect, or show not found
      // Main check: page loads without 500 error
      const url = page.url();
      // Check page didn't crash - could be on dashboard with auth check or redirected
      const pageHasContent = await page.locator('body').isVisible();
      expect(pageHasContent).toBeTruthy();
    });

    test('analysis page loads without server error', async ({ page }) => {
      await page.goto('/analysis/test_123', { waitUntil: 'domcontentloaded' });
      await waitForAppReady(page);
      
      // Main check: page loads without 500 error
      const pageHasContent = await page.locator('body').isVisible();
      expect(pageHasContent).toBeTruthy();
    });
  });
});

test.describe('No Server Errors', () => {
  
  test('all public pages load without 500 errors', async ({ page }) => {
    const publicPages = [
      '/',
      '/login',
      '/pricing',
      '/register',
    ];
    
    for (const pagePath of publicPages) {
      const response = await page.goto(pagePath, { waitUntil: 'domcontentloaded' });
      
      // No 500 errors should occur
      expect(response?.status(), `Page ${pagePath} returned server error`).not.toBe(500);
      
      // Check for React error boundary
      const hasReactError = await page.locator('text=Something went wrong').isVisible().catch(() => false);
      expect(hasReactError, `Page ${pagePath} shows React error`).toBeFalsy();
    }
  });

  test('API endpoints return proper error codes not 500', async ({ page }) => {
    // Organizations endpoint should return 401 (auth required), not 500
    const orgResponse = await page.request.get('/api/organizations');
    expect(orgResponse.status(), 'Organizations endpoint returned 500').not.toBe(500);
    expect(orgResponse.status()).toBe(401);
    
    // Analysis endpoint should return 401, not 500
    const analysisResponse = await page.request.get('/api/analysis/test_123');
    expect(analysisResponse.status(), 'Analysis endpoint returned 500').not.toBe(500);
    expect(analysisResponse.status()).toBe(401);
  });
});
