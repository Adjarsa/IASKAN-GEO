import { test, expect } from '@playwright/test';
import { waitForAppReady, hideEmergentBadge, dismissToasts } from '../fixtures/helpers';

const TEST_SESSION_TOKEN = 'test_session_1772018666518';
const TEST_DOMAIN = 'visibility-ai-5.preview.emergentagent.com';

test.describe('Content Generator Page', () => {
  
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
    
    // Select project first
    await page.goto('/projects');
    await waitForAppReady(page);
    await hideEmergentBadge(page);
    await page.waitForSelector('text=TEST_GEO_Project', { timeout: 15000 });
    await page.click('text=TEST_GEO_Project');
    await page.waitForURL(/\/dashboard/);
    await hideEmergentBadge(page);
  });

  test.describe('Navigation', () => {
    
    test('should display Generateur navigation entry in sidebar', async ({ page }) => {
      await expect(page.getByTestId('nav-generateur')).toBeVisible();
    });

    test('should navigate to Content Generator page from sidebar', async ({ page }) => {
      await page.getByTestId('nav-generateur').click();
      await page.waitForURL(/\/content-generator/);
      await expect(page.getByTestId('content-generator-page')).toBeVisible();
    });
  });

  test.describe('Page Structure', () => {
    
    test.beforeEach(async ({ page }) => {
      await page.goto('/content-generator');
      await waitForAppReady(page);
      await hideEmergentBadge(page);
    });

    test('should load Content Generator page correctly', async ({ page }) => {
      await expect(page.getByTestId('content-generator-page')).toBeVisible();
    });

    test('should display page title', async ({ page }) => {
      await expect(page.getByText('Generation de Contenu GEO')).toBeVisible();
    });

    test('should display page description', async ({ page }) => {
      await expect(page.getByText('Creez et optimisez du contenu pour maximiser votre visibilite dans les reponses IA')).toBeVisible();
    });

    test('should display Powered by AI badge', async ({ page }) => {
      await expect(page.getByText('Powered by AI')).toBeVisible();
    });
  });

  test.describe('Tabs Functionality', () => {
    
    test.beforeEach(async ({ page }) => {
      await page.goto('/content-generator');
      await waitForAppReady(page);
      await hideEmergentBadge(page);
    });

    test('should display all three tabs', async ({ page }) => {
      await expect(page.getByRole('tab', { name: /Generer/ })).toBeVisible();
      await expect(page.getByRole('tab', { name: /Optimiser/ })).toBeVisible();
      await expect(page.getByRole('tab', { name: /Formats GEO/ })).toBeVisible();
    });

    test('should show Generate tab by default', async ({ page }) => {
      // Generate tab should be active by default - check for Configuration section
      await expect(page.getByText('Configuration')).toBeVisible();
      await expect(page.getByText('Type de contenu')).toBeVisible();
    });

    test('should switch to Optimize tab', async ({ page }) => {
      await page.getByRole('tab', { name: /Optimiser/ }).click();
      
      // Optimize tab content
      await expect(page.getByText('Contenu Original')).toBeVisible();
      await expect(page.getByText('Contenu Optimise')).toBeVisible();
    });

    test('should switch to Formats GEO tab', async ({ page }) => {
      await page.getByRole('tab', { name: /Formats GEO/ }).click();
      
      // Formats tab content - shows format cards
      await expect(page.getByText('FAQ Optimisee')).toBeVisible();
      await expect(page.getByText('Fiche Entite')).toBeVisible();
      await expect(page.getByText('Guide Definitif')).toBeVisible();
    });
  });

  test.describe('Generate Tab - Form Elements', () => {
    
    test.beforeEach(async ({ page }) => {
      await page.goto('/content-generator');
      await waitForAppReady(page);
      await hideEmergentBadge(page);
    });

    test('should display content type selector with default Article GEO', async ({ page }) => {
      await expect(page.getByText('Article GEO')).toBeVisible();
    });

    test('should display topic input field', async ({ page }) => {
      await expect(page.getByTestId('topic-input')).toBeVisible();
      await expect(page.getByPlaceholder(/Les avantages du CRM/)).toBeVisible();
    });

    test('should display keywords input field', async ({ page }) => {
      await expect(page.getByTestId('keywords-input')).toBeVisible();
      await expect(page.getByPlaceholder(/CRM, PME, gestion client/)).toBeVisible();
    });

    test('should display generate button', async ({ page }) => {
      await expect(page.getByTestId('generate-btn')).toBeVisible();
      await expect(page.getByText('Generer le contenu')).toBeVisible();
    });

    test('should display brand name from current project', async ({ page }) => {
      await expect(page.getByText('Marque ciblee:')).toBeVisible();
      await expect(page.getByText('TEST_GEO_Brand')).toBeVisible();
    });

    test('should display empty state message before generation', async ({ page }) => {
      await expect(page.getByText('Pret a creer du contenu GEO-optimise')).toBeVisible();
    });
  });

  test.describe('Generate Tab - Content Type Selection', () => {
    
    test.beforeEach(async ({ page }) => {
      await page.goto('/content-generator');
      await waitForAppReady(page);
      await hideEmergentBadge(page);
    });

    test('should open content type dropdown', async ({ page }) => {
      // Click on the select trigger
      await page.getByRole('combobox').click();
      
      // Check dropdown options are visible
      await expect(page.getByRole('option', { name: /Article GEO/ })).toBeVisible();
      await expect(page.getByRole('option', { name: /FAQ Optimisee/ })).toBeVisible();
      await expect(page.getByRole('option', { name: /Fiche Entite/ })).toBeVisible();
      await expect(page.getByRole('option', { name: /Guide Definitif/ })).toBeVisible();
      await expect(page.getByRole('option', { name: /Comparatif/ })).toBeVisible();
    });

    test('should select FAQ content type', async ({ page }) => {
      await page.getByRole('combobox').click();
      await page.getByRole('option', { name: /FAQ Optimisee/ }).click();
      
      // Verify description changed
      await expect(page.getByText('Questions/Reponses structurees')).toBeVisible();
    });

    test('should select Entity content type', async ({ page }) => {
      await page.getByRole('combobox').click();
      await page.getByRole('option', { name: /Fiche Entite/ }).click();
      
      await expect(page.getByText('Renforcer la reconnaissance IA')).toBeVisible();
    });

    test('should select Guide content type', async ({ page }) => {
      await page.getByRole('combobox').click();
      await page.getByRole('option', { name: /Guide Definitif/ }).click();
      
      await expect(page.getByText('Contenu pilier exhaustif')).toBeVisible();
    });

    test('should select Comparison content type', async ({ page }) => {
      await page.getByRole('combobox').click();
      await page.getByRole('option', { name: /Comparatif/ }).click();
      
      await expect(page.getByText('Tableau structure')).toBeVisible();
    });
  });

  test.describe('Optimize Tab - Form Elements', () => {
    
    test.beforeEach(async ({ page }) => {
      await page.goto('/content-generator');
      await waitForAppReady(page);
      await hideEmergentBadge(page);
      await page.getByRole('tab', { name: /Optimiser/ }).click();
    });

    test('should display original content textarea', async ({ page }) => {
      await expect(page.getByTestId('original-content-input')).toBeVisible();
    });

    test('should display optimize button', async ({ page }) => {
      await expect(page.getByTestId('optimize-btn')).toBeVisible();
      await expect(page.getByText('Optimiser pour GEO')).toBeVisible();
    });

    test('should display empty state for optimized content', async ({ page }) => {
      await expect(page.getByText('Collez votre contenu existant et cliquez sur "Optimiser"')).toBeVisible();
    });

    test('should allow entering content in textarea', async ({ page }) => {
      const testContent = 'This is test content for optimization';
      await page.getByTestId('original-content-input').fill(testContent);
      await expect(page.getByTestId('original-content-input')).toHaveValue(testContent);
    });
  });

  test.describe('Formats GEO Tab - Format Cards', () => {
    
    test.beforeEach(async ({ page }) => {
      await page.goto('/content-generator');
      await waitForAppReady(page);
      await hideEmergentBadge(page);
      await page.getByRole('tab', { name: /Formats GEO/ }).click();
    });

    test('should display FAQ format card with description', async ({ page }) => {
      await expect(page.getByText('FAQ Optimisee')).toBeVisible();
      await expect(page.getByText(/Format question\/reponse que les LLMs adorent citer/)).toBeVisible();
      await expect(page.getByRole('button', { name: /Generer une FAQ/ })).toBeVisible();
    });

    test('should display Entity format card with description', async ({ page }) => {
      await expect(page.getByText('Fiche Entite')).toBeVisible();
      await expect(page.getByText(/Renforce la reconnaissance de votre marque/)).toBeVisible();
      await expect(page.getByRole('button', { name: /Creer une fiche/ })).toBeVisible();
    });

    test('should display Guide format card with description', async ({ page }) => {
      await expect(page.getByText('Guide Definitif')).toBeVisible();
      await expect(page.getByText(/Contenu pilier exhaustif/)).toBeVisible();
      await expect(page.getByRole('button', { name: /Creer un guide/ })).toBeVisible();
    });

    test('should display Comparison format card', async ({ page }) => {
      // Scroll down to see more cards
      await page.evaluate(() => window.scrollBy(0, 300));
      
      await expect(page.getByText('Comparatif Structure')).toBeVisible();
      await expect(page.getByRole('button', { name: /Creer un comparatif/ })).toBeVisible();
    });

    test('should display Article GEO format card', async ({ page }) => {
      await page.evaluate(() => window.scrollBy(0, 300));
      
      await expect(page.getByText('Article GEO').first()).toBeVisible();
      await expect(page.getByRole('button', { name: /Creer un article/ })).toBeVisible();
    });

    test('should display E-E-A-T criteria card', async ({ page }) => {
      await page.evaluate(() => window.scrollBy(0, 300));
      
      await expect(page.getByText('Criteres E-E-A-T')).toBeVisible();
      await expect(page.getByText(/Experience/)).toBeVisible();
      await expect(page.getByText(/Expertise/)).toBeVisible();
      await expect(page.getByText(/Authority/)).toBeVisible();
      await expect(page.getByText(/Trust/)).toBeVisible();
    });
  });

  test.describe('Generate Content Interaction', () => {
    
    test.beforeEach(async ({ page }) => {
      await page.goto('/content-generator');
      await waitForAppReady(page);
      await hideEmergentBadge(page);
    });

    test('should fill topic and enable generate button', async ({ page }) => {
      // Button should be disabled initially when topic is empty
      await expect(page.getByTestId('generate-btn')).toBeDisabled();
      
      // Fill in topic
      await page.getByTestId('topic-input').fill('Test topic for GEO');
      
      // Button should now be enabled
      await expect(page.getByTestId('generate-btn')).toBeEnabled();
    });

    test('should fill keywords field', async ({ page }) => {
      await page.getByTestId('keywords-input').fill('keyword1, keyword2, keyword3');
      await expect(page.getByTestId('keywords-input')).toHaveValue('keyword1, keyword2, keyword3');
    });
  });
});
