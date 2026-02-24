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

## What's Been Implemented (Feb 24, 2026)

### IAskan Verified GEO Protocol™ v2.0 (NEW!)
- ✅ **Multi-runs (3x)**: Chaque requête exécutée 3 fois avec variations pour la stabilité
- ✅ **Générateur de requêtes multi-dimensions**: 30% transactionnel, 25% comparatif, 20% informationnel, 15% local, 10% exploratoire
- ✅ **Analyse sémantique 4 couches**: Présence → Rôle → Crédibilité → Conversion
- ✅ **Indices avancés**: Stability Index™, Dominance Index™, Trust Gap™, Opportunity Score™
- ✅ **Score R.A.T.E™ ajusté**: Relevance 30%, Authority 25%, Truth 20%, Endorsement 25%
- ✅ **Contrôle anti-hallucination**: Vérification automatique de la cohérence
- ✅ **Grade système**: A/B/C/D/F basé sur le score global

### Backend (FastAPI + MongoDB)
- ✅ Authentication system with Emergent Google OAuth
- ✅ Session management with 7-day expiry
- ✅ User management (users, user_sessions)
- ✅ Subscription system (trial + 3 plans)
- ✅ Projects CRUD operations
- ✅ **GEO Analysis engine V2 with IAskan Verified Protocol™**
- ✅ R.A.T.E scoring algorithm (enhanced)
- ✅ Recommendations generation (enhanced with metrics)
- ✅ Stripe checkout integration
- ✅ Dashboard statistics API
- ✅ Payment webhooks
- ✅ PDF Report Generation

### Frontend (React + Tailwind CSS)
- ✅ Landing page with IAskan Verified GEO Protocol™ section
- ✅ Login page with SSO buttons (Google, Microsoft, LinkedIn)
- ✅ Dashboard with indices IAskan Verified™ display
- ✅ **Analysis page V2** with protocol features:
  - Protocol badge and certification display
  - Advanced indices visualization (Stability, Dominance, Trust Gap, Opportunity)
  - Query type breakdown
  - Multi-run stability indicators
  - Grade display (A/B/C/D/F)
- ✅ Projects management (CRUD)
- ✅ Recommendations page with filtering
- ✅ Pricing page with Stripe checkout
- ✅ Settings page (account, subscription, security)
- ✅ French language UI
- ✅ Responsive design
- ✅ Protected routes

### Integrations
- ✅ Emergent Google OAuth (SSO)
- ✅ Microsoft OAuth2 SSO (requires MICROSOFT_CLIENT_ID & MICROSOFT_CLIENT_SECRET)
- ✅ LinkedIn OAuth2 SSO (requires LINKEDIN_CLIENT_ID & LINKEDIN_CLIENT_SECRET)
- ✅ Emergent LLM Key (OpenAI GPT-5.2, Claude, Gemini)
- ✅ Stripe Checkout (payment processing)
- ✅ MongoDB (data storage)
- ✅ FPDF2 (PDF generation)
- ✅ Authlib (OAuth2 client)
- ✅ Resend (email service - requires RESEND_API_KEY)

## Technical Architecture
```
Frontend: React 19 + Tailwind CSS + Framer Motion
Backend: FastAPI + Motor (async MongoDB)
Database: MongoDB
Auth: Emergent Google OAuth + Microsoft OAuth2 + LinkedIn OAuth2
AI: Emergent LLM Key (GPT-5.2, Claude, Gemini)
Payments: Stripe
PDF: FPDF2 with DejaVu Unicode fonts
OAuth: Authlib for Microsoft/LinkedIn
Email: Resend API
```

## IAskan Verified GEO Protocol™ Methodology

### Query Distribution
- 30% Transactional (acheter, prix, commander)
- 25% Comparative (vs, comparaison, meilleur)
- 20% Informational (qu'est-ce que, comment)
- 15% Local (près de moi, en France)
- 10% Exploratory (recommandations, suggestions)

### Analysis Layers
1. **Presence**: Brand mention detection, position analysis
2. **Role**: Top recommendation, shortlist, comparison, mention, cited, discouraged
3. **Credibility**: Numbers, statistics, testimonials, certifications, facts, sources
4. **Conversion**: CTA, urgency, benefits, trust, social proof

### Indices
- **Stability Index™**: Consistency of AI responses across multi-runs
- **Dominance Index™**: Position vs competitors in AI responses
- **Trust Gap™**: Credibility gap vs competitors
- **Opportunity Score™**: Potential for improvement

## Prioritized Backlog

### P0 - Critical (Completed)
- [x] IAskan Verified GEO Protocol™ implementation ✅ (Feb 24, 2026)
- [x] Microsoft SSO integration ✅ (requires API keys)
- [x] LinkedIn SSO integration ✅ (requires API keys)
- [x] Magic Link email authentication ✅
- [x] Email notifications ✅ (requires RESEND_API_KEY)

### P1 - High Priority
- [x] Competitor comparison detailed view ✅
- [x] PDF report generation ✅
- [x] Analysis history charts ✅
- [ ] Team/multi-user support

### P2 - Medium Priority
- [ ] API access for Business plan
- [ ] GEO article generation
- [ ] Waitlist system for launch
- [ ] Referral program
- [ ] Fix Recharts dimension warning (minor)

### P3 - Low Priority
- [ ] Mobile app
- [ ] Slack integration
- [ ] Custom branding
- [ ] White-label option

## Recent Updates

### Feb 24, 2026 - IAskan Verified GEO Protocol™ v2.0
- **Complete methodology implementation**:
  - Multi-runs (3x per query with variations)
  - Multi-dimension query generation
  - 4-layer semantic analysis
  - Advanced indices calculation
  - Anti-hallucination checks
  - Enhanced recommendations with metrics impacted
- **Frontend updates**:
  - New IAskan Verified GEO Protocol™ section on landing page
  - Advanced indices display on dashboard and analysis pages
  - Query type breakdown visualization
  - Grade system (A/B/C/D/F)
  - Protocol badge and certification

### Feb 22-23, 2026 - Bug Fixes
- Fixed React DOM `insertBefore` error (Portal provider solution)
- Fixed HTML nesting/hydration errors
- Improved text contrast for readability

## Next Tasks
1. Team/multi-user support
2. Analysis completion notification email
3. API access for Business plan
4. Mobile optimization
5. Recharts dimension warning fix (low priority)

## Key Files Modified
- `/app/backend/server.py` - IAskan Verified GEO Protocol™ engine
- `/app/frontend/src/pages/AnalysisPage.jsx` - Analysis V2 with indices
- `/app/frontend/src/pages/DashboardPage.jsx` - Indices display
- `/app/frontend/src/pages/LandingPage.jsx` - Protocol section
