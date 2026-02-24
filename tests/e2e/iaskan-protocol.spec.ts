import { test, expect } from '@playwright/test';
import { waitForAppReady, hideEmergentBadge } from '../fixtures/helpers';

test.describe('IAskan Verified GEO Protocol™ Features', () => {
  
  test.describe('Landing Page - Protocol Section', () => {
    
    test('should display IAskan Verified GEO Protocol™ section with title', async ({ page }) => {
      await page.goto('/');
      await waitForAppReady(page);
      
      // Scroll to protocol section
      await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight * 0.25));
      
      // Check main protocol heading
      await expect(page.getByRole('heading', { name: /IAskan Verified GEO Protocol/i })).toBeVisible();
      
      // Check "Méthodologie Certifiée" badge
      await expect(page.getByText('Méthodologie Certifiée')).toBeVisible();
    });

    test('should display 4 pillars of the protocol (Multi-Runs, Multi-IA, 4 Couches, Anti-Hallucination)', async ({ page }) => {
      await page.goto('/');
      await waitForAppReady(page);
      
      // Scroll to 4 pillars section
      await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight * 0.25));
      
      // Multi-Runs pillar
      await expect(page.getByText('Multi-Runs')).toBeVisible();
      await expect(page.getByText('3x par requête')).toBeVisible();
      
      // Multi-IA pillar
      await expect(page.getByText('Multi-IA')).toBeVisible();
      await expect(page.getByText('4 moteurs')).toBeVisible();
      
      // 4 Couches pillar
      await expect(page.getByText('4 Couches')).toBeVisible();
      await expect(page.getByText('Analyse sémantique')).toBeVisible();
      
      // Anti-Hallucination pillar
      await expect(page.getByText('Anti-Hallucination')).toBeVisible();
      await expect(page.getByText('Vérification auto')).toBeVisible();
    });

    test('should display Indices Exclusifs IAskan™ section', async ({ page }) => {
      await page.goto('/');
      await waitForAppReady(page);
      
      // Scroll to indices section
      await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight * 0.35));
      
      // Main heading
      await expect(page.getByText('Indices Exclusifs IAskan™')).toBeVisible();
      
      // All 4 indices should be visible
      await expect(page.getByText('Stability Index™')).toBeVisible();
      await expect(page.getByText('Dominance Index™')).toBeVisible();
      await expect(page.getByText('Trust Gap™')).toBeVisible();
      await expect(page.getByText('Opportunity Score™')).toBeVisible();
    });

    test('should display indices demo values on landing page', async ({ page }) => {
      await page.goto('/');
      await waitForAppReady(page);
      
      // Scroll to indices section
      await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight * 0.35));
      
      // Demo values from LandingPage.jsx: 87%, 72%, +15, 63%
      await expect(page.getByText('87%').first()).toBeVisible();
      await expect(page.getByText('72%').first()).toBeVisible();
      await expect(page.getByText('+15')).toBeVisible();
      await expect(page.getByText('63%').first()).toBeVisible();
      
      // Descriptions
      await expect(page.getByText('Cohérence des réponses IA')).toBeVisible();
      await expect(page.getByText('Position vs concurrents')).toBeVisible();
      await expect(page.getByText('Écart de confiance')).toBeVisible();
      await expect(page.getByText("Potentiel d'amélioration")).toBeVisible();
    });
  });

  test.describe('API Health Check', () => {
    
    test('should return healthy status from health endpoint', async ({ request }) => {
      const response = await request.get('/api/health');
      expect(response.status()).toBe(200);
      
      const data = await response.json();
      expect(data.status).toBe('healthy');
      expect(data.timestamp).toBeDefined();
    });
  });
});
