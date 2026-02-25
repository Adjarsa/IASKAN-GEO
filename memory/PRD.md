# IAskan - GEO SaaS Platform PRD

## Original Problem Statement
Créer IAskan, la plateforme SaaS ultime de Generative Engine Optimization (GEO) permettant aux entreprises d'être visibles dans les réponses d'IA (ChatGPT, Gemini, Perplexity, Claude, etc.).

## Product Vision
IAskan est la première plateforme GEO pour l'Europe, permettant aux entreprises de mesurer et optimiser leur visibilité dans les réponses des moteurs IA.

## User Personas
1. **Marketing Director B2B** - Cherche à mesurer et améliorer la visibilité de sa marque dans les IA
2. **Agence SEO/GEO** - Offre des services d'optimisation GEO à ses clients
3. **Consultant Digital** - Utilise IAskan pour auditer et recommander des améliorations
4. **E-commerce Manager** - Veut être recommandé par les IA pour ses produits

## Core Requirements (Static)
- Score GEO propriétaire R.A.T.E™ (Relevance, Authority, Truthfulness, Endorsement)
- Analyse multi-IA (ChatGPT, Claude, Gemini, Perplexity)
- Benchmark concurrentiel
- Recommandations actionnables
- Rapports détaillés
- Abonnements (Starter 79€, Pro 149€, Business 349€)
- SSO Enterprise-grade

## What's Been Implemented

### IAskan Verified GEO Protocol™ v2.0
- Multi-runs (3x): Chaque requête exécutée 3 fois avec variations pour la stabilité
- Générateur de requêtes multi-dimensions: 30% transactionnel, 25% comparatif, 20% informationnel, 15% local, 10% exploratoire
- Analyse sémantique 4 couches: Présence → Rôle → Crédibilité → Conversion
- Indices avancés: Stability Index™, Dominance Index™, Trust Gap™, Opportunity Score™
- Score R.A.T.E™ ajusté: Relevance 30%, Authority 25%, Truth 20%, Endorsement 25%
- Contrôle anti-hallucination: Vérification automatique de la cohérence
- Grade système: A/B/C/D/F basé sur le score global

### Backend (FastAPI + MongoDB)
- Authentication system with Emergent Google OAuth
- Session management with 7-day expiry
- User management (users, user_sessions)
- Subscription system (trial + 3 plans)
- Projects CRUD operations
- GEO Analysis engine V2 with IAskan Verified Protocol™
- R.A.T.E scoring algorithm (enhanced)
- Recommendations generation (enhanced with metrics)
- Stripe checkout integration
- Dashboard statistics API
- Payment webhooks
- PDF Report Generation
- **NEW: Visibility Tracking API** (/api/visibility/{project_id})
- **NEW: Content Audit API** (/api/content-audit/{project_id})

### Frontend (React + Tailwind CSS)
- Landing page with IAskan Verified GEO Protocol™ section
- Login page with SSO buttons (Google, Microsoft, LinkedIn)
- Dashboard with indices IAskan Verified™ display
- Analysis page V2 with protocol features
- Projects management (CRUD)
- Recommendations page with filtering
- Pricing page with Stripe checkout
- Settings page (account, subscription, security)
- Competitor Comparison page (benchmark)
- History Charts page (évolution)
- **NEW: Visibility Page** - Tracking de présence dans les moteurs IA
- **NEW: Content Audit Page** - Score de citabilité et analyse de structure
- French language UI
- Responsive design
- Protected routes

### Integrations
- Emergent Google OAuth (SSO)
- Microsoft OAuth2 SSO (requires MICROSOFT_CLIENT_ID & MICROSOFT_CLIENT_SECRET)
- LinkedIn OAuth2 SSO (requires LINKEDIN_CLIENT_ID & LINKEDIN_CLIENT_SECRET)
- Emergent LLM Key (OpenAI GPT-5.2, Claude, Gemini)
- Stripe Checkout (payment processing)
- MongoDB (data storage)
- FPDF2 (PDF generation)
- Authlib (OAuth2 client)
- Resend (email service - requires RESEND_API_KEY)

## Technical Architecture
```
Frontend: React 18.2.0 + Tailwind CSS + Framer Motion
Backend: FastAPI + Motor (async MongoDB)
Database: MongoDB
Auth: Emergent Google OAuth + Microsoft OAuth2 + LinkedIn OAuth2
AI: Emergent LLM Key (GPT-5.2, Claude, Gemini)
Payments: Stripe
PDF: FPDF2 with DejaVu Unicode fonts
OAuth: Authlib for Microsoft/LinkedIn
Email: Resend API
```

**⚠️ CRITICAL: React 18.2.0 - DO NOT UPGRADE TO REACT 19**
React was downgraded from v19 to v18.2.0 to fix a critical `insertBefore` crash caused by Radix UI compatibility issues.

## NEW GEO Features (Feb 25, 2026)

### Visibilité Générative (/visibility)
- Tracking de présence dans ChatGPT, Perplexity, Gemini, Claude
- Score de citation par moteur génératif
- Position dans les réponses (1er, 2e, 3e...)
- Fréquence d'apparition par thématique/requête
- Distribution des positions (graphique)
- Requêtes récentes analysées

### Audit de Contenu (/content-audit)
- Score de "citabilité" des pages (probabilité d'être cité par un LLM)
- Détection des lacunes (sujets où vous devriez être cité mais ne l'êtes pas)
- Analyse de la structure (formats privilégiés par les LLMs)
- Vérification des données structurées / schema.org
- Recommandations de structure page par page
- Impact potentiel des améliorations

### Benchmark Concurrentiel (existant, amélioré)
- Qui est cité à votre place et pourquoi
- Comparaison de visibilité GEO par thématique
- Sources préférées des LLMs dans votre secteur
- Gap analysis (opportunités non couvertes)

## Prioritized Backlog

### P0 - Critical (Completed)
- [x] IAskan Verified GEO Protocol™ implementation
- [x] Microsoft SSO integration (requires API keys)
- [x] LinkedIn SSO integration (requires API keys)
- [x] Magic Link email authentication
- [x] Email notifications (requires RESEND_API_KEY)
- [x] Visibility Page implementation
- [x] Content Audit Page implementation

### P1 - High Priority
- [x] Competitor comparison detailed view
- [x] PDF report generation
- [x] Analysis history charts
- [x] Fix Recharts dimension warning
- [ ] Team/multi-user support

### P2 - Medium Priority
- [ ] API access for Business plan
- [ ] GEO article generation
- [ ] Waitlist system for launch
- [ ] Referral program

### P3 - Low Priority
- [ ] Mobile app
- [ ] Slack integration
- [ ] Custom branding
- [ ] White-label option

## Recent Updates

### Feb 25, 2026 - GEO Features Implementation
- **NEW: Visibility Page** (/visibility)
  - Tracking de présence dans les moteurs IA génératives
  - Score par moteur (ChatGPT, Claude, Gemini, Perplexity)
  - Distribution des positions
  - Visibilité par thématique
  - Requêtes récentes analysées
- **NEW: Content Audit Page** (/content-audit)
  - Score de citabilité global
  - Score de structure
  - Couverture Schema.org
  - Détection des lacunes de contenu
  - Analyse page par page
  - Recommandations de structure
- **Navigation mise à jour** avec les nouvelles entrées
- **Fix Recharts** - Ajout de min-h-[Xpx] pour éviter le warning de dimensions

### Feb 24, 2026 - UX Improvements
- Added visual loading indicators with progress bars
- Added 5-second timeout on auth checks
- Improved loading states with animated spinners
- Enhanced analysis "running" state with step-by-step progress

## Known Issues
- None critical

## Key Files
- `/app/backend/server.py` - Main API server with GEO Protocol™ engine
- `/app/frontend/src/pages/VisibilityPage.jsx` - Visibility tracking page
- `/app/frontend/src/pages/ContentAuditPage.jsx` - Content audit page
- `/app/frontend/src/pages/AnalysisPage.jsx` - Analysis V2 with indices
- `/app/frontend/src/pages/DashboardPage.jsx` - Main dashboard
- `/app/frontend/src/components/layout/DashboardLayout.jsx` - Sidebar navigation

## Test Reports
- `/app/test_reports/iteration_5.json` - Latest test report (100% pass rate)
