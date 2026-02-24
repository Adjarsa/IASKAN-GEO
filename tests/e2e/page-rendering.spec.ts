import { test, expect } from '@playwright/test';
import { waitForAppReady, hideEmergentBadge } from '../fixtures/helpers';

test.describe('Page Rendering - Bug Fix Verification', () => {
  
  test.describe('Landing Page', () => {
    test('should load without React hydration errors', async ({ page }) => {
      // Collect console errors
      const errors: string[] = [];
      page.on('console', msg => {
        if (msg.type() === 'error') {
          errors.push(msg.text());
        }
      });
      
      await page.goto('/');
      await waitForAppReady(page);
      await hideEmergentBadge(page);
      
      // Verify page loaded
      await expect(page.getByTestId('nav-logo')).toBeVisible();
      await expect(page.getByTestId('hero-cta')).toBeVisible();
      await expect(page.getByTestId('nav-login')).toBeVisible();
      
      // Check for React hydration errors
      const hydrationErrors = errors.filter(e => 
        e.includes('insertBefore') || 
        e.includes('hydrat') || 
        e.includes('cannot be a descendant') ||
        e.includes('cannot be a child')
      );
      expect(hydrationErrors, 'Should have no React hydration errors').toHaveLength(0);
    });

    test('should display all hero section elements correctly', async ({ page }) => {
      await page.goto('/');
      await waitForAppReady(page);
      
      // Check hero elements
      await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
      await expect(page.getByText('IAskan analyse votre visibilité')).toBeVisible();
      await expect(page.getByTestId('hero-cta')).toBeVisible();
      await expect(page.getByTestId('hero-demo')).toBeVisible();
      
      // Check navigation
      await expect(page.getByTestId('nav-cta')).toBeVisible();
    });

    test('should have clickable navigation links', async ({ page }) => {
      await page.goto('/');
      await waitForAppReady(page);
      await hideEmergentBadge(page);
      
      // Test login link navigation
      const loginLink = page.getByTestId('nav-login');
      await expect(loginLink).toBeVisible();
      await loginLink.click();
      
      // Verify navigation to login page
      await expect(page).toHaveURL(/\/login/);
    });
  });

  test.describe('Login Page', () => {
    test('should load without React DOM errors', async ({ page }) => {
      const errors: string[] = [];
      page.on('console', msg => {
        if (msg.type() === 'error') {
          errors.push(msg.text());
        }
      });
      
      await page.goto('/login');
      await waitForAppReady(page);
      await hideEmergentBadge(page);
      
      // Verify page loaded
      await expect(page.getByTestId('login-google')).toBeVisible();
      await expect(page.getByTestId('login-microsoft')).toBeVisible();
      await expect(page.getByTestId('login-linkedin')).toBeVisible();
      
      // Check for React DOM errors
      const domErrors = errors.filter(e => 
        e.includes('insertBefore') || 
        e.includes('NotFoundError') ||
        e.includes('cannot be a descendant') ||
        e.includes('cannot be a child')
      );
      expect(domErrors, 'Should have no React DOM errors').toHaveLength(0);
    });

    test('should display all login options', async ({ page }) => {
      await page.goto('/login');
      await waitForAppReady(page);
      
      // Check SSO buttons
      await expect(page.getByTestId('login-google')).toBeVisible();
      await expect(page.getByTestId('login-microsoft')).toBeVisible();
      await expect(page.getByTestId('login-linkedin')).toBeVisible();
      
      // Check magic link form
      await expect(page.getByTestId('magic-link-email')).toBeVisible();
      await expect(page.getByTestId('magic-link-submit')).toBeVisible();
      
      // Check forgot password link
      await expect(page.getByTestId('forgot-password-link')).toBeVisible();
    });

    test('should have working back button', async ({ page }) => {
      await page.goto('/login');
      await waitForAppReady(page);
      await hideEmergentBadge(page);
      
      // Click back to home
      const backLink = page.getByTestId('back-home');
      await expect(backLink).toBeVisible();
      await backLink.click();
      
      // Verify navigation to home
      await expect(page).toHaveURL('/');
    });

    test('should validate magic link email input', async ({ page }) => {
      await page.goto('/login');
      await waitForAppReady(page);
      
      // Fill email input
      const emailInput = page.getByTestId('magic-link-email');
      await emailInput.fill('test@example.com');
      await expect(emailInput).toHaveValue('test@example.com');
    });
  });

  test.describe('Pricing Page', () => {
    test('should load without React hydration warnings', async ({ page }) => {
      const errors: string[] = [];
      page.on('console', msg => {
        if (msg.type() === 'error') {
          errors.push(msg.text());
        }
      });
      
      await page.goto('/pricing');
      await waitForAppReady(page);
      await hideEmergentBadge(page);
      
      // Verify page loaded with pricing cards
      await expect(page.getByTestId('checkout-starter')).toBeVisible();
      await expect(page.getByTestId('checkout-pro')).toBeVisible();
      await expect(page.getByTestId('checkout-business')).toBeVisible();
      
      // Check for hydration warnings
      const hydrationErrors = errors.filter(e => 
        e.includes('hydrat') || 
        e.includes('insertBefore') ||
        e.includes('cannot be a descendant')
      );
      expect(hydrationErrors, 'Should have no hydration warnings').toHaveLength(0);
    });

    test('should display all three pricing plans', async ({ page }) => {
      await page.goto('/pricing');
      await waitForAppReady(page);
      
      // Check plan names using exact match
      await expect(page.getByRole('heading', { name: 'Starter', exact: true }).first()).toBeVisible();
      await expect(page.getByRole('heading', { name: 'Pro', exact: true }).first()).toBeVisible();
      await expect(page.getByRole('heading', { name: 'Business', exact: true }).first()).toBeVisible();
      
      // Check prices
      await expect(page.getByText('79€').first()).toBeVisible();
      await expect(page.getByText('149€').first()).toBeVisible();
      await expect(page.getByText('349€').first()).toBeVisible();
    });

    test('should have working navigation', async ({ page }) => {
      await page.goto('/pricing');
      await waitForAppReady(page);
      await hideEmergentBadge(page);
      
      // Check logo link
      const logoLink = page.getByTestId('pricing-logo');
      await expect(logoLink).toBeVisible();
      
      // Check login button
      const loginBtn = page.getByTestId('pricing-login');
      await expect(loginBtn).toBeVisible();
      await loginBtn.click();
      
      // Verify navigation to login
      await expect(page).toHaveURL(/\/login/);
    });

    test('should have clickable checkout buttons', async ({ page }) => {
      await page.goto('/pricing');
      await waitForAppReady(page);
      await hideEmergentBadge(page);
      
      // All checkout buttons should be visible and clickable
      const starterBtn = page.getByTestId('checkout-starter');
      const proBtn = page.getByTestId('checkout-pro');
      const businessBtn = page.getByTestId('checkout-business');
      
      await expect(starterBtn).toBeVisible();
      await expect(proBtn).toBeVisible();
      await expect(businessBtn).toBeVisible();
      
      // Buttons should be enabled (for non-logged in users, they redirect to login)
      await expect(starterBtn).toBeEnabled();
      await expect(proBtn).toBeEnabled();
      await expect(businessBtn).toBeEnabled();
    });
  });
});
