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

## What's Been Implemented (Feb 21, 2026)

### Backend (FastAPI + MongoDB)
- ✅ Authentication system with Emergent Google OAuth
- ✅ Session management with 7-day expiry
- ✅ User management (users, user_sessions)
- ✅ Subscription system (trial + 3 plans)
- ✅ Projects CRUD operations
- ✅ GEO Analysis engine with multi-AI support
- ✅ R.A.T.E scoring algorithm
- ✅ Recommendations generation
- ✅ Stripe checkout integration
- ✅ Dashboard statistics API
- ✅ Payment webhooks

### Frontend (React + Tailwind CSS)
- ✅ Landing page (hero, features, pricing, CTA)
- ✅ Login page with SSO buttons (Google, Microsoft, LinkedIn)
- ✅ Dashboard with score display and subscription info
- ✅ Analysis page with project selection and results
- ✅ Projects management (CRUD)
- ✅ Recommendations page with filtering
- ✅ Pricing page with Stripe checkout
- ✅ Settings page (account, subscription, security)
- ✅ French language UI
- ✅ Premium dark theme "Cyber Slate"
- ✅ Responsive design
- ✅ Protected routes
- ✅ PDF Report Generation (Rapport détaillé avec Score GEO, R.A.T.E.™, AI Scores, Requêtes, Recommandations)

### Integrations
- ✅ Emergent Google OAuth (SSO)
- ✅ Microsoft OAuth2 SSO (requires MICROSOFT_CLIENT_ID & MICROSOFT_CLIENT_SECRET)
- ✅ LinkedIn OAuth2 SSO (requires LINKEDIN_CLIENT_ID & LINKEDIN_CLIENT_SECRET)
- ✅ Emergent LLM Key (OpenAI GPT-5.2, Claude, Gemini)
- ✅ Stripe Checkout (payment processing)
- ✅ MongoDB (data storage)
- ✅ FPDF2 (PDF generation)
- ✅ Authlib (OAuth2 client)

## Prioritized Backlog

### P0 - Critical (Next Sprint)
- [x] Microsoft SSO integration ✅ (Completed Feb 21, 2026 - requires API keys)
- [x] LinkedIn SSO integration ✅ (Completed Feb 21, 2026 - requires API keys)
- [ ] Magic Link email authentication
- [ ] Email notifications (welcome, analysis complete)

### P1 - High Priority
- [ ] Competitor comparison detailed view
- [x] PDF report generation ✅ (Completed Feb 21, 2026)
- [ ] Analysis history charts
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
```

## Recent Updates (Feb 21, 2026)

### Microsoft & LinkedIn SSO Added
- Backend endpoints: GET /api/auth/microsoft/login, /api/auth/linkedin/login
- OAuth2 authorization code flow implementation
- Automatic user creation and session management
- Error handling with user-friendly messages
- Requires API keys configuration (MICROSOFT_CLIENT_ID, MICROSOFT_CLIENT_SECRET, LINKEDIN_CLIENT_ID, LINKEDIN_CLIENT_SECRET)

### PDF Report Module Added
- Backend endpoint: GET /api/analysis/{analysis_id}/pdf
- 7-page professional PDF report
- Includes: Score GEO Global, R.A.T.E.™ breakdown, AI scores, query details, recommendations, synthesis
- Frontend download button on analysis results page
- Unicode support for French characters

## Next Tasks
1. Implement Magic Link authentication
2. Add email notifications
3. Build competitor comparison view
4. Add analysis history charts
5. Team/multi-user support
