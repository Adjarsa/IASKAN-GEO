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
- ✅ Resend (email service - requires RESEND_API_KEY)

## Prioritized Backlog

### P0 - Critical (Next Sprint)
- [x] Microsoft SSO integration ✅ (Completed Feb 21, 2026 - requires API keys)
- [x] LinkedIn SSO integration ✅ (Completed Feb 21, 2026 - requires API keys)
- [x] Magic Link email authentication ✅ (Completed Feb 22, 2026)
- [x] Email notifications (welcome, password reset) ✅ (Completed Feb 22, 2026 - requires RESEND_API_KEY)

### P1 - High Priority
- [x] Competitor comparison detailed view ✅ (Completed Feb 22, 2026)
- [x] PDF report generation ✅ (Completed Feb 21, 2026)
- [x] Analysis history charts ✅ (Completed Feb 22, 2026)
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
Email: Resend API
```

## Recent Updates

### Feb 22, 2026 - Email Notifications & Magic Link
- **Email Service (Resend):**
  - Welcome email template with IAskan branding
  - Password reset email with secure token
  - Magic Link login email
  - All emails in French with professional HTML design
- **Magic Link Authentication:**
  - POST /api/auth/magic-link - Request login link
  - GET /api/auth/magic-verify - Verify and authenticate
  - Auto-creates user if not exists (with trial subscription)
- **Password Reset Flow:**
  - POST /api/auth/forgot-password - Request reset link
  - POST /api/auth/reset-password - Set new password
  - Token expires after 1 hour
- **Frontend Pages:**
  - /forgot-password - Password reset request
  - /reset-password?token=xxx - Set new password
  - /auth/magic?token=xxx - Magic link verification

### Feb 22, 2026 - Competitor Comparison
- **Backend Endpoints:**
  - POST /api/analysis/compare - Start competitor comparison
  - GET /api/analysis/compare/{comparison_id} - Get comparison results
  - GET /api/analysis/comparisons/{project_id} - List all comparisons
- **Features:**
  - Analyze brand visibility vs competitors across ChatGPT, Claude, Gemini
  - Calculate dominance index and rankings
  - Detailed breakdown by AI engine
  - Professional insights and recommendations
- **Frontend:**
  - /competitors - Competitor comparison page
  - Add/remove competitors dynamically
  - Visual ranking with medals and scores
  - AI breakdown table

### Feb 21, 2026 - Microsoft & LinkedIn SSO
- Backend endpoints: GET /api/auth/microsoft/login, /api/auth/linkedin/login
- OAuth2 authorization code flow implementation
- Automatic user creation and session management
- Error handling with user-friendly messages

### Feb 21, 2026 - PDF Report Module
- Backend endpoint: GET /api/analysis/{analysis_id}/pdf
- 7-page professional PDF report
- Includes: Score GEO Global, R.A.T.E.™ breakdown, AI scores, query details, recommendations

## Next Tasks
1. Add analysis history charts
2. Team/multi-user support
3. Analysis completion notification email
4. API access for Business plan
