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
- Visibility Tracking API (/api/visibility/{project_id})
- Content Audit API (/api/content-audit/{project_id})
- **NEW: Content Generation API** (/api/content/generate)
- **NEW: Content Reformulation API** (/api/content/reformulate)

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
- Visibility Page - Tracking de présence dans les moteurs IA
- Content Audit Page - Score de citabilité et analyse de structure
- **NEW: Content Generator Page** - Génération et optimisation de contenu GEO
- French language UI
- Responsive design
- Protected routes

### Integrations
- Emergent Google OAuth (SSO)
- Microsoft OAuth2 SSO (requires MICROSOFT_CLIENT_ID & MICROSOFT_CLIENT_SECRET)
- LinkedIn OAuth2 SSO (requires LINKEDIN_CLIENT_ID & LINKEDIN_CLIENT_SECRET)
- Emergent LLM Key (OpenAI GPT-4o, Claude, Gemini)
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
AI: Emergent LLM Key (GPT-4o, Claude, Gemini)
Payments: Stripe
PDF: FPDF2 with DejaVu Unicode fonts
OAuth: Authlib for Microsoft/LinkedIn
Email: Resend API
```

**⚠️ CRITICAL: React 18.2.0 - DO NOT UPGRADE TO REACT 19**
React was downgraded from v19 to v18.2.0 to fix a critical `insertBefore` crash caused by Radix UI compatibility issues.

## NEW Content Generation Features (Feb 25, 2026)

### Génération de Contenu GEO (/content-generator)
**Onglet "Générer"**
- Sélection du type de contenu (Article, FAQ, Fiche Entité, Guide, Comparatif)
- Input sujet et mots-clés
- Génération par IA avec score GEO et conseils
- Export Markdown et copie presse-papiers

**Onglet "Optimiser"**
- Coller du contenu existant
- Reformulation GEO automatique
- Liste des améliorations appliquées
- Comparaison avant/après

**Onglet "Formats GEO"**
- Templates pour FAQ optimisées (format Q/R adoré par les LLMs)
- Fiches d'entité (Knowledge Graph)
- Guides définitifs (contenu pilier)
- Comparatifs structurés (tableaux)
- Articles E-E-A-T

### API Endpoints
- `POST /api/content/generate` - Génère du contenu GEO selon le type
- `POST /api/content/reformulate` - Optimise du contenu existant

## Previous GEO Features (Feb 25, 2026)

### Visibilité Générative (/visibility)
- Tracking de présence dans ChatGPT, Perplexity, Gemini, Claude
- Score de citation par moteur génératif
- Position dans les réponses (1er, 2e, 3e...)
- Distribution des positions
- Visibilité par thématique

### Audit de Contenu (/content-audit)
- Score de citabilité des pages
- Analyse de structure (formats LLM-friendly)
- Couverture Schema.org
- Détection des lacunes de contenu
- Recommandations de structure

## Prioritized Backlog

### P0 - Critical (Completed)
- [x] IAskan Verified GEO Protocol™ implementation
- [x] Visibility Page implementation
- [x] Content Audit Page implementation
- [x] Content Generator Page implementation

### P1 - High Priority
- [x] Competitor comparison detailed view
- [x] PDF report generation
- [x] Analysis history charts
- [x] Fix Recharts dimension warning
- [ ] Microsoft SSO integration (requires API keys)
- [ ] LinkedIn SSO integration (requires API keys)
- [ ] Team/multi-user support

### P2 - Medium Priority
- [ ] Stripe subscription management complète
- [ ] API access for Business plan
- [ ] GEO article generation avec images
- [ ] Waitlist system for launch
- [ ] Referral program

### P3 - Low Priority
- [ ] Mobile app
- [ ] Slack integration
- [ ] Custom branding
- [ ] White-label option

## Recent Updates

### Feb 26, 2026 - Free Trial Configuration Update
- **Nouvelle configuration FREE** :
  - 10 prompts × 3 variations × 3 runs × 1 IA = **90 requêtes analysées**
  - 1 scan offert par essai gratuit
  - ChatGPT uniquement
  - Quota mensuel = 90 requêtes
- **Structure des plans mise à jour** :
  - FREE: 10 prompts, 3 variations, 3 runs, 1 IA (90 requêtes)
  - Starter (79€): 15 prompts, 2 variations, 3 runs, 1 IA (10 scans/mois)
  - Pro (149€): 20 prompts, 3 variations, 3 runs, 4 IA (30 scans/mois)
  - Business (349€): 30 prompts, 3 variations, 3 runs, 4 IA (illimité)
- **Affichage dans l'UI** :
  - Page d'analyse : détail du calcul (10 × 3 × 3 = 90 requêtes)
  - Page pricing mise à jour avec nouvelles features

### Feb 26, 2026 - Email Verification System
- **Vérification email obligatoire** à la création de compte :
  - Email de vérification automatique via Resend avec design IAskan
  - Token sécurisé avec expiration 24h
  - Blocage de l'essai gratuit tant que l'email n'est pas vérifié
- **Endpoints API** :
  - `POST /api/auth/verify-email` - Vérifie le token
  - `POST /api/auth/resend-verification` - Renvoie l'email (rate limit: 3/heure)
  - `GET /api/auth/verification-status` - Statut de vérification
- **Composants frontend** :
  - `VerifyEmailPage.jsx` - Page de vérification avec états (loading/success/error)
  - `EmailVerificationBanner.jsx` - Bannière dans le dashboard pour relancer l'email
- **Base de données** :
  - Collection `email_verification_tokens` pour les tokens
  - Champ `email_verified` dans users

### Feb 26, 2026 - Background Analysis Notification System
- **Système de notifications pour analyses en arrière-plan** :
  - Notification in-app créée automatiquement quand une analyse se termine (succès ou échec)
  - Email envoyé à l'utilisateur quand un scan est terminé (via Resend)
  - Badge visuel avec compteur de notifications non lues
  - Polling automatique toutes les 30 secondes
- **Endpoints API Notifications** :
  - `GET /api/notifications` - Liste des notifications (supports limit, unread_only params)
  - `POST /api/notifications/{id}/read` - Marquer une notification comme lue
  - `POST /api/notifications/read-all` - Marquer toutes comme lues
  - `DELETE /api/notifications/{id}` - Supprimer une notification
- **Frontend NotificationBell Component** :
  - Icône cloche dans le header du dashboard
  - Badge rouge avec compteur pour les non lues
  - Menu dropdown avec liste des notifications
  - Navigation vers l'analyse au clic
  - Actions : marquer lu, tout marquer lu, supprimer
- **Types de notifications** : `scan_complete`, `scan_failed`
- **Fichiers créés/modifiés** :
  - `backend/server.py` : Ajout appels `create_notification()` et `send_scan_complete_email()` dans `run_analysis_v2()`
  - `frontend/src/components/NotificationBell.jsx` : Nouveau composant
  - `frontend/src/components/layout/DashboardLayout.jsx` : Intégration NotificationBell
- **Tests** : 18/18 backend, 9/9 frontend E2E (100% pass rate)

### Feb 26, 2026 - Anti-Abuse System for Free Trial
- **1 essai gratuit sécurisé** avec protection multi-niveaux :
  - Blocage par **email** (email déjà utilisé)
  - Blocage par **IP** (même connexion)
  - Blocage par **fingerprint navigateur** (même appareil)
  - Blocage par **domaine analysé** (même site)
- **Blocage des emails temporaires** : Liste de 100+ domaines jetables bloqués (tempmail, mailinator, yopmail, etc.)
- **Tracking des utilisations** : Collection MongoDB `free_trial_usage`
- **Fingerprint navigateur** : Intégration FingerprintJS pour identifier les appareils
- **Endpoints API** :
  - `POST /api/analysis/check-eligibility` - Vérifie l'éligibilité avant analyse
  - `POST /api/analysis/start` - Inclut maintenant la vérification anti-abus
- **Fichiers créés/modifiés** :
  - `backend/server.py` : Fonctions `check_free_trial_eligibility()`, `record_free_trial_usage()`, `is_temporary_email()`, `get_client_ip()`
  - `frontend/src/hooks/useFingerprint.js` : Hook React pour le fingerprint
  - `frontend/src/pages/AnalysisPage.jsx` : Affichage des erreurs d'éligibilité
  - `frontend/src/App.js` : Envoi du fingerprint à l'authentification

### Feb 26, 2026 - Logo, Website Link & Dynamic Competitors
- **Logo & Website Display**:
  - Ajout automatique du favicon/logo via Google Favicon Service
  - Affichage du logo et du lien du site dans le header du Dashboard
  - Nouveau champ `logo_url` dans le modèle Project
- **Analyse Concurrentielle Dynamique**:
  - Nouvelle fonction `identify_competitors_from_analysis()` pour identifier les concurrents depuis les réponses IA
  - Nouveau champ `discovered_competitors` dans le modèle Project
  - Séparation visuelle entre "Concurrents Découverts par l'IA" et "Concurrents Définis"
  - Affichage du nombre de mentions et sources IA pour chaque concurrent découvert
  - Mise à jour du PDF et de la prévisualisation pour afficher les deux types de concurrents
- **Fichiers modifiés**:
  - `backend/server.py`: Nouvelles fonctions `get_favicon_url()`, `extract_competitors_from_response()`, `identify_competitors_from_analysis()`
  - `frontend/src/pages/DashboardPage.jsx`: Affichage logo + lien site
  - `frontend/src/components/ReportPreviewModal.jsx`: Section Concurrence améliorée
  - `frontend/src/services/pdfReportGenerator.js`: Section Concurrence avec concurrents découverts

### Feb 25, 2026 - PDF Export Report Implementation
- **NEW: Professional PDF Report Generator** (/app/frontend/src/services/pdfReportGenerator.js)
  - 10 sections complètes basées sur le modèle utilisateur:
    1. Introduction - Scores globaux, méthodologie, résumé exécutif
    2. Localisation - Zone géographique ciblée (France)
    3. Requêtes - Distribution par type et exemples de requêtes testées
    4. Citations IA - Performance par moteur IA et analyse des rôles
    5. Contenu - Analyse on-page, microdonnées Schema.org
    6. Technique - HTTPS, mobile, vitesse, robots.txt, sitemap, etc.
    7. Confiance - Score E-E-A-T et indicateurs de confiance
    8. Concurrence - Benchmark concurrentiel et analyse des écarts
    9. Requêtes IA - Détail des réponses par requête
    10. Plan d'Action - Recommandations prioritaires
  - Couleurs IAskan (violet #7C3AED, cyan #06B6D4)
  - Génération côté client avec jsPDF + jspdf-autotable
  - Bouton export sur la page d'analyse et le dashboard
  - Design professionnel avec header gradient et scores visuels
- **NEW: Report Preview Modal** (/app/frontend/src/components/ReportPreviewModal.jsx)
  - Prévisualisation complète des 10 sections avant téléchargement
  - Navigation par onglets pour parcourir les sections
  - Bouton de téléchargement intégré dans la modal
  - Interface utilisateur intuitive avec sidebar de navigation
- **Dépendances ajoutées**: jspdf, jspdf-autotable, html2canvas
- **Composants créés**:
  - PDFExportButton.jsx - Bouton d'export réutilisable
  - ReportPreviewModal.jsx - Modal de prévisualisation avec 10 sections
- **Pages mises à jour**:
  - AnalysisPage.jsx - Bouton "Prévisualiser" + "Exporter PDF" + carte PDF
  - DashboardPage.jsx - Boutons "Prévisualiser" + "PDF" dans le header

### Feb 25, 2026 - Content Generation Implementation
- **NEW: Content Generator Page** (/content-generator)
  - 3 onglets: Générer, Optimiser, Formats GEO
  - 5 types de contenu: Article, FAQ, Fiche Entité, Guide, Comparatif
  - Génération IA via Emergent LLM Key (GPT-4o)
  - Optimisation de contenu existant
  - Score GEO et conseils d'utilisation
  - Export Markdown
- **API Content Generation**
  - POST /api/content/generate
  - POST /api/content/reformulate
- **Navigation mise à jour** avec entrée "Générateur"
- **Tests**: 80/80 frontend, 13/13 nouveaux tests backend

### Feb 25, 2026 - GEO Features Implementation
- Visibility Page (/visibility)
- Content Audit Page (/content-audit)
- Fix Recharts dimension warning
- Navigation update

## Known Issues
- Microsoft/LinkedIn SSO nécessite des clés API (actuellement vides)
- LLM budget doit être rechargé régulièrement

## Key Files
- `/app/backend/server.py` - Main API server with GEO Protocol™ engine
- `/app/frontend/src/services/pdfReportGenerator.js` - **PDF Report Generator (10 sections)**
- `/app/frontend/src/components/ReportPreviewModal.jsx` - **NEW: Preview Modal with navigation**
- `/app/frontend/src/components/PDFExportButton.jsx` - PDF Export Components
- `/app/frontend/src/pages/ContentGeneratorPage.jsx` - Content generation page
- `/app/frontend/src/pages/VisibilityPage.jsx` - Visibility tracking page
- `/app/frontend/src/pages/ContentAuditPage.jsx` - Content audit page
- `/app/frontend/src/pages/AnalysisPage.jsx` - Analysis V2 with indices + PDF export + preview
- `/app/frontend/src/pages/DashboardPage.jsx` - Main dashboard + PDF export + preview
- `/app/frontend/src/components/layout/DashboardLayout.jsx` - Sidebar navigation

## Test Reports
- `/app/test_reports/iteration_6.json` - Latest test report (100% pass rate for new features)
