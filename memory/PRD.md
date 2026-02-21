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

### Integrations
- ✅ Emergent Google OAuth (SSO)
- ✅ Emergent LLM Key (OpenAI GPT-5.2, Claude, Gemini)
- ✅ Stripe Checkout (payment processing)
- ✅ MongoDB (data storage)

## Prioritized Backlog

### P0 - Critical (Next Sprint)
- [ ] Microsoft SSO integration
- [ ] LinkedIn SSO integration
- [ ] Magic Link email authentication
- [ ] Email notifications (welcome, analysis complete)

### P1 - High Priority
- [ ] Competitor comparison detailed view
- [ ] PDF report generation
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
Auth: Emergent Google OAuth
AI: Emergent LLM Key (GPT-5.2, Claude, Gemini)
Payments: Stripe
```

## Next Tasks
1. Test complete GEO analysis flow
2. Add Microsoft/LinkedIn SSO
3. Implement PDF report export
4. Add email notifications
5. Build waitlist landing page
