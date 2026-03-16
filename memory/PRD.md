# IAskan - Plateforme GEO SaaS

## Vision Produit
IAskan est une plateforme **Generative Engine Optimization (GEO)** qui aide les entreprises à optimiser leur visibilité dans les réponses générées par l'IA (ChatGPT, Claude, Gemini, Perplexity).

## Architecture Technique

### Stack
- **Frontend**: React 18.2.0 (version verrouillée), Tailwind CSS, Shadcn/UI
- **Backend**: FastAPI, Python 3.11
- **Database**: PostgreSQL 15.16 (local, 17 tables), MongoDB (legacy fallback)
- **Task Queue**: Celery + Redis
- **AI Integration**: emergentintegrations (OpenAI, Claude, Gemini, Perplexity)
- **Paiements**: Stripe
- **Email**: Resend

### Structure des fichiers
```
/app/
├── backend/
│   ├── app/
│   │   ├── core/          # Config, Database
│   │   ├── models/        # Pydantic models
│   │   ├── routers/       # API routes modulaires
│   │   │   ├── auth.py           # ✅ Authentification (Google, Microsoft, LinkedIn SSO)
│   │   │   ├── projects.py       # ✅ CRUD projets
│   │   │   ├── dashboard.py      # ✅ Stats dashboard
│   │   │   ├── organizations.py  # ✅ Gestion organisations
│   │   │   ├── article_optimizer.py # ✅ Optimiseur articles
│   │   │   ├── admin.py          # ✅ Admin backoffice
│   │   │   ├── subscriptions.py  # ✅ Stripe integration
│   │   │   ├── semantic.py       # ✅ Recherche sémantique pgvector
│   │   │   ├── strategy.py       # ✅ GEO Strategy Engine
│   │   │   └── onboarding.py     # ✅ Onboarding utilisateur
│   │   ├── engines/       # Core GEO engines
│   │   │   ├── query/     # Query generation & variation
│   │   │   ├── semantic/  # Semantic analysis
│   │   │   ├── influence/ # Influence mapping
│   │   │   ├── gap/       # Content gap finder
│   │   │   └── optimizer/ # Article optimizer
│   │   ├── services/      # Business logic
│   │   │   ├── stripe_abstraction.py    # ✅ Stripe checkout/webhooks
│   │   │   ├── embedding_service.py     # ✅ OpenAI embeddings
│   │   │   ├── semantic_search_service.py # ✅ pgvector search
│   │   │   ├── microsoft_oauth.py       # ✅ Microsoft SSO
│   │   │   └── linkedin_oauth.py        # ✅ LinkedIn SSO
│   │   └── db/
│   │       └── vector_models.py         # ✅ Modèles pgvector
│   ├── tests/
│   │   └── test_router_endpoints.py  # 29 tests d'intégration
│   └── server.py          # Main FastAPI app (~4870 lignes)
├── frontend/
│   ├── src/
│   │   ├── components/    # UI components
│   │   │   ├── SemanticSearchPanel.jsx  # ✅ Panel recherche sémantique
│   │   │   ├── AutomaticObjectives.jsx  # ✅ Objectifs automatiques
│   │   │   ├── ImpactSimulator.jsx      # ✅ Simulateur d'impact
│   │   │   └── StrategyPanel.jsx        # ✅ Panel stratégie GEO
│   │   ├── pages/
│   │   │   ├── CheckoutSuccessPage.jsx  # ✅ Succès paiement Stripe
│   │   │   └── ...
│   │   └── services/      # Frontend services
│   └── package.json
└── memory/
    └── PRD.md
```

## Fonctionnalités Implémentées

### Phase 1 - MVP (Complété)
- [x] Authentification (Google SSO)
- [x] Gestion de projets
- [x] Scan GEO multi-IA (ChatGPT, Claude, Gemini, Perplexity)
- [x] Scoring R.A.T.E™
- [x] Dashboard avec métriques
- [x] Rapports PDF
- [x] Notifications en temps réel
- [x] Scans programmés

### Phase 2 - Features Avancées (En cours - Mars 2026)

- [x] **Migration PostgreSQL** (Nouveau!)
  - Base de données PostgreSQL locale configurée
  - 17 tables créées (users, projects, analyses, subscriptions, etc.)
  - SQLAlchemy ORM avec modèles complets
  - Services de base de données (UserService, ProjectService, etc.)
  - Prêt pour migration vers Supabase en production
  - Credentials Supabase sauvegardés

- [x] **Optimiseur d'Article GEO** (Nouveau!)
  - Analyse d'URL ou contenu
  - Scores: Structure, Autorité, Citabilité, Fraîcheur
  - Diagnostics détaillés
  - Plan d'action 30/60/90 jours
  - Stratégie de distribution
  - Export Markdown
  - **Simulateur d'Impact intégré** (Mars 2026)
  
- [x] **Organisations/Workspaces** (Nouveau!)
  - Création d'organisations
  - Invitations par email
  - Rôles: owner, admin, member, viewer
  - Gestion des membres

- [x] **Admin Backoffice** (Nouveau!)
  - Statistiques plateforme
  - Gestion utilisateurs
  - Mise à jour plans
  - Reset quotas
  - Logs admin
  - Tableau de bord avec graphiques (recharts)

- [x] **GEO Strategy Engine** (Mars 2026)
  - Génération de recommandations par catégorie (content, authority, technical, engagement)
  - Plan d'action en 3 phases
  - Quick wins identifiés
  - Système de tracking d'implémentation
  - **Objectifs Automatiques** - Plan d'amélioration pour atteindre la note supérieure

- [x] **Recherche Sémantique pgvector** (Mars 2026)
  - Service d'embedding OpenAI (text-embedding-3-small)
  - Modèles vectoriels : QueryEmbedding, ContentEmbedding, ResponseEmbedding
  - Recherche de requêtes/contenus similaires
  - Identification des lacunes de contenu
  - Clustering sémantique des requêtes
  - Interface frontend SemanticSearchPanel intégrée

- [x] **Onboarding Guidé** (Nouveau!)
  - Tutoriel interactif en 6 étapes
  - Illustrations animées
  - Progression sauvegardée
  - Tooltips contextuels
  - Bouton d'aide flottant

- [x] **Emails Transactionnels** (Nouveau!)
  - Email de bienvenue (à l'inscription)
  - Email de fin de scan (avec score et recommandations)
  - Email de désabonnement (confirmation)
  - Email de rappel d'expiration
  - Templates HTML responsives avec branding IAskan

- [x] **Gestion des abonnements**
  - Endpoint de désabonnement
  - Endpoint de réactivation
  - Interface utilisateur dans Settings

- [x] **Intégration Stripe Complète** (Mars 2026)
  - Checkout sessions avec line_items dynamiques
  - Webhooks (checkout.session.completed, subscription.updated, invoice.*)
  - Gestion des abonnements (cancel, reactivate)
  - Billing portal support
  - Page CheckoutSuccessPage frontend
  - Plans: Free, Starter (79€), Pro (149€), Business (349€)

- [x] **SSO Multi-Provider** (Mars 2026)
  - Google OAuth 2.0 ✅ (configuré)
  - Microsoft Azure AD ✅ (code prêt, attente credentials)
  - LinkedIn OpenID Connect ✅ (code prêt, attente credentials)
  - Documentation setup: /app/MICROSOFT_LINKEDIN_SSO_SETUP.md

- [x] **Engines Backend Modulaires** (Nouveau!)
  - Query Generation Engine
  - Prompt Variation Engine
  - Semantic Analysis Engine
  - Influence Mapping Engine
  - Content Gap Engine
  - Article Optimizer Engine

### Phase 3 - Améliorations (Planifié)
- [ ] Refactoring complet server.py
- [ ] Queue Celery + Redis pour scans
- [ ] Cache intelligent
- [ ] Stripe webhooks complets
- [ ] Magic Link testing
- [ ] Microsoft/LinkedIn SSO

## Plans d'abonnement

| Plan | Prix | Scans | Optimisations | Projets |
|------|------|-------|---------------|---------|
| Free | 0€ | 1 | 0 | 1 |
| Starter | 79€ | 10 | 5 | 1 |
| Pro | 149€ | 50 | 30 | 5 |
| Business | 349€ | 150 | ∞ | ∞ |

## APIs Clés

### Semantic Search (Nouveau - pgvector)
- `GET /api/semantic/status` - Statut du service d'embedding
- `GET /api/semantic/stats/{project_id}` - Statistiques des embeddings
- `POST /api/semantic/search/queries` - Recherche de requêtes similaires
- `POST /api/semantic/search/content` - Recherche de contenus similaires
- `GET /api/semantic/gaps/{project_id}` - Identification des lacunes de contenu
- `GET /api/semantic/clusters/{project_id}` - Clusters sémantiques de requêtes
- `POST /api/semantic/index/query` - Indexer une requête
- `POST /api/semantic/index/content` - Indexer un contenu
- `POST /api/semantic/index/bulk` - Indexation en masse
- `DELETE /api/semantic/index/{embedding_id}` - Supprimer un embedding

### Article Optimizer
- `POST /api/article-optimizer/analyze` - Analyse basique
- `POST /api/article-optimizer/analyze-with-llm` - Analyse enrichie IA
- `GET /api/article-optimizer/quota` - Vérifier quota
- `GET /api/article-optimizer/history` - Historique
- `GET /api/article-optimizer/improvement-options` - Options d'amélioration pour simulateur
- `POST /api/article-optimizer/simulate` - Simulation d'impact

### Strategy
- `POST /api/strategy/generate` - Générer stratégie depuis scores
- `POST /api/strategy/from-analysis` - Générer depuis analyse existante
- `GET /api/strategy/recommendations/{category}` - Recommandations par catégorie
- `GET /api/strategy/objective/{score}` - Objectif automatique depuis score
- `GET /api/strategy/objective/from-analysis/{id}` - Objectif depuis analyse
- `GET /api/strategy/paths/{score}` - Tous les chemins d'amélioration
- `POST /api/strategy/progress/{project_id}/track` - Tracker recommandation
- `PUT /api/strategy/progress/{id}/status` - Mettre à jour status
- `GET /api/strategy/progress/{project_id}` - Progression projet

### Organizations
- `POST /api/organizations` - Créer organisation
- `GET /api/organizations` - Lister
- `POST /api/organizations/{id}/invite` - Inviter membre
- `DELETE /api/organizations/{id}/members/{user_id}` - Retirer membre

### Admin
- `GET /api/admin/stats` - Statistiques plateforme
- `GET /api/admin/users` - Liste utilisateurs
- `PUT /api/admin/users/{id}/subscription` - Modifier plan
- `POST /api/admin/users/{id}/reset-quota` - Reset quota

### Subscription
- `POST /api/subscription/cancel` - Annuler l'abonnement
- `POST /api/subscription/reactivate` - Réactiver l'abonnement

### Onboarding
- `GET /api/onboarding/status` - Statut onboarding utilisateur
- `POST /api/onboarding/step/{id}/complete` - Marquer étape terminée
- `POST /api/onboarding/skip` - Ignorer l'onboarding
- `GET /api/onboarding/tips/{feature}` - Astuces contextuelles

## Notes Critiques

⚠️ **NE PAS UPGRADER REACT** - Version 18.2.0 verrouillée (bug `insertBefore`)

✅ **PostgreSQL** - Base de données configurée
  - PostgreSQL local fonctionnel pour le développement
  - 17 tables créées : users, projects, analyses, subscriptions, notifications, schedules, organizations, etc.
  - SQLAlchemy ORM avec services complets
  - Prêt pour Supabase en production (credentials sauvegardés)

✅ **server.py** - Refactoring TERMINÉ
  - Réduit de 5875 à 4408 lignes (-25%, ~1467 lignes supprimées)
  - Tous les routers CRUD migrés : auth, projects, dashboard, notifications, schedules, subscriptions
  - Reste dans server.py : Analysis pipeline (logique complexe), Content generation, Visibility tracking

⚠️ **Tests en attente** - PDF download, URL truncation, timeout backend

## Architecture Backend Modulaire

```
/app/backend/
├── server.py                    # ~4412 lignes (réduit de 5875, -25%)
├── app/
│   ├── core/
│   │   ├── config.py           # Configuration centralisée (PostgreSQL + MongoDB)
│   │   └── database.py         # Connexion MongoDB (legacy)
│   ├── db/                     # [NOUVEAU] PostgreSQL avec SQLAlchemy
│   │   ├── database.py         # Connexion async PostgreSQL
│   │   ├── models.py           # 17 modèles SQLAlchemy
│   │   └── services.py         # Services CRUD (User, Project, Analysis, etc.)
│   ├── routers/
│   │   ├── auth.py             # ✅ Authentification complète (OAuth, Magic Link, etc.)
│   │   ├── projects.py         # ✅ CRUD projets + stats
│   │   ├── dashboard.py        # ✅ Stats, activité, quick-stats
│   │   ├── notifications.py    # ✅ CRUD notifications
│   │   ├── schedules.py        # ✅ Scans programmés
│   │   ├── subscriptions.py    # ✅ Abonnements & paiements Stripe
│   │   ├── organizations.py    # ✅ Gestion organisations
│   │   ├── article_optimizer.py # ✅ Optimiseur articles
│   │   ├── admin.py            # ✅ Admin backoffice
│   │   └── onboarding.py       # ✅ Onboarding utilisateur
│   ├── engines/
│   │   ├── query/              # Query generation
│   │   ├── semantic/           # Analyse sémantique
│   │   ├── influence/          # Mapping d'influence
│   │   ├── gap/                # Content gap finder
│   │   └── optimizer/          # Article optimizer
│   └── services/
│       └── email_service.py    # Service emails (Resend)
├── scripts/
│   └── init_db.py              # Script d'initialisation PostgreSQL
```

## Changelog

### 2026-03-14 - Migration MongoDB → PostgreSQL Complete
- **MIGRATION MONGODB → POSTGRESQL TERMINÉE**
  - ✅ ~40+ endpoints migrés de MongoDB vers PostgreSQL SQLAlchemy
  - ✅ Nouveaux modèles créés:
    - `CompetitorComparison` - Stockage des comparaisons concurrentielles
    - `FreeTrialUsage` - Anti-abus pour essais gratuits
  - ✅ Endpoints migrés:
    - `/api/content-audit/{project_id}` - Audit de contenu
    - `/api/analysis/{analysis_id}/pdf` - Génération PDF
    - `/api/analysis/compare` - Comparaison concurrentielle
    - `/api/analysis/check-eligibility` - Vérification éligibilité
    - `/api/comparisons/history/{project_id}` - Historique comparaisons
    - `/api/contact` - Formulaire de contact
    - Fonctions de vérification email
    - Fonctions de notifications
    - Fonctions de free trial
    - Fonction `run_scheduled_scan`
    - Fonction `run_analysis_v2`
  - ✅ Code MongoDB legacy restant: 1 appel dans bloc fallback (ne s'exécute pas car USE_POSTGRES=true)

### 2026-03-12 (Session actuelle - Refactoring Services)
- **POSTGRESQL INSTALLÉ ET FONCTIONNEL**
  - ✅ PostgreSQL 15.16 installé localement
  - ✅ Base de données `iaskan_db` créée avec 17 tables
  - ✅ Connexion vérifiée et fonctionnelle
  - ✅ Prêt pour migration vers Supabase en production

- **NOUVEAU SERVICE ANALYSIS PIPELINE** (`/app/backend/app/services/analysis_pipeline.py`)
  - ✅ `AnalysisPipelineService` - Orchestrateur principal d'analyse GEO
  - ✅ Implémente IAskan Verified GEO Protocol™ v2.1
  - ✅ 13 phases d'analyse intégrées :
    - Génération de variantes de marque
    - Enrichissement de site web
    - Génération de requêtes multi-dimension
    - Querying LLM multi-run (stabilité)
    - Calcul Stability Index
    - Calcul Advanced Indices
    - Calcul R.A.T.E. Score
    - Analyse par type de requête
    - Intelligence compétitive
    - Analyse sémantique
    - Analyse content gaps
    - Résumé mentions de marque
    - Recommandations enrichies

- **NOUVEAUX SERVICES BACKEND CRÉÉS**
  - ✅ `LLMConnector` (`/app/backend/app/services/llm_connector.py`)
    - Connexion centralisée à ChatGPT, Claude, Gemini, Perplexity
    - Méthode `query_llm()` pour requêtes individuelles
    - Méthode `query_all_llms()` pour requêtes parallèles
    - Analyse automatique: présence, rôle, crédibilité, conversion
    - Configuration LLM_CONFIG avec providers
    
  - ✅ `GEOScoringEngine` (`/app/backend/app/services/geo_scoring.py`)
    - Calcul Stability Index (cohérence multi-run)
    - Calcul Advanced Indices (dominance, trust gap, opportunity)
    - Calcul R.A.T.E. Score (Relevance, Authority, Truthfulness, Endorsement)
    - Génération de recommandations prioritisées
    
  - ✅ `CompetitiveIntelligenceEngine` (`/app/backend/app/services/competitive_intelligence.py`)
    - Détection automatique de concurrents (KNOWN_BRANDS database)
    - Extraction NLP de marques potentielles
    - Analyse competitive gap
    - Recommandations concurrentielles
    
- **TÂCHES CELERY AMÉLIORÉES** (`/app/backend/app/tasks/analysis_tasks.py`)
  - ✅ `query_single_llm` : Query LLM avec retry automatique
  - ✅ `query_all_llms_task` : Query parallèle multi-LLM
  - ✅ `run_full_analysis` : Pipeline complet avec 8 phases
    - Phase 1: Query Generation
    - Phase 2: LLM Querying
    - Phase 3: Scoring & Analysis
    - Phase 4: Competitive Intelligence
    - Phase 5: Semantic Analysis
    - Phase 6: Content Gap Analysis
    - Phase 7: Compile Results
    - Phase 8: Notifications
  - ✅ `check_scheduled_scans_task` : Exécution scans programmés
  - ✅ `cleanup_old_analyses` : Nettoyage données anciennes
  
- **TESTS BACKEND** 
  - ✅ `/app/backend/tests/test_new_services.py` - 38 tests
  - ✅ `/app/backend/tests/test_postgresql_migration.py` - 38 tests
  - ✅ `/app/backend/tests/test_analyses_endpoints.py` - 31 tests
  - ✅ Total: 80+ tests passés (100%)

### 2026-03-13 - Connexion Frontend aux Endpoints PostgreSQL
- **NOUVEAUX ROUTERS CRÉÉS**
  - ✅ `/app/backend/app/routers/analyses.py` - Liste des analyses
    - `GET /api/analyses` - Liste filtrée par projet ou utilisateur
    - `GET /api/analyses/history/{project_id}` - Données évolution pour graphiques
  - ✅ `/app/backend/app/routers/analysis.py` - Ajout endpoint détail
    - `GET /api/analysis/{analysis_id}` - Détails complets d'une analyse
- **COMPATIBILITÉ FRONTEND VÉRIFIÉE**
  - DashboardPage.jsx connecté aux nouveaux endpoints
  - Format de réponse compatible avec les attentes du frontend

### 2026-03-10 (Session précédente)
- **CELERY + REDIS IMPLÉMENTÉ**
  - ✅ Redis installé et fonctionnel (`redis://localhost:6379/0`)
  - ✅ Celery configuré avec 4 queues : analysis, llm, processing, celery
  - ✅ Worker démarré avec 2 processus concurrents
  - ✅ 4 tâches Celery créées :
    - `query_single_llm` : Query un LLM individuel
    - `query_all_llms` : Query ChatGPT, Claude, Gemini en parallèle
    - `run_full_analysis` : Pipeline d'analyse complet
    - `check_scheduled_scans_task` : Vérification des scans programmés
  - ✅ Router `/api/analysis` avec endpoints : start, status, results, history, cancel, quota
  - ✅ Beat scheduler pour tâches périodiques

- **MIGRATION ROUTERS VERS POSTGRESQL**
  - ✅ `auth.py` migré vers PostgreSQL (sessions, OAuth, Magic Link, Password Reset)
  - ✅ `projects.py` migré vers PostgreSQL (CRUD projets, stats)
  - ✅ `dashboard.py` migré vers PostgreSQL (stats, activité)
  - ✅ `notifications.py` migré vers PostgreSQL (CRUD notifications)
  - ✅ `schedules.py` migré vers PostgreSQL (scans programmés)
  - ✅ `subscriptions.py` migré vers PostgreSQL (abonnements, Stripe)
  - Tous les endpoints utilisent maintenant SQLAlchemy ORM avec PostgreSQL

- **MIGRATION POSTGRESQL COMPLÉTÉE**
  - ✅ PostgreSQL local installé et configuré
  - ✅ 17 tables créées (users, projects, analyses, subscriptions, etc.)
  - ✅ SQLAlchemy ORM avec modèles complets
  - ✅ Services de base de données (UserService, ProjectService, AnalysisService, etc.)
  - ✅ Initialisation automatique au démarrage du serveur
  - ✅ Prêt pour migration vers Supabase en production
  - ✅ Credentials Supabase sauvegardés dans .env

- **REFACTORING BACKEND COMPLET**
  - ✅ Migré `auth.py` : Session, OAuth (Google/Microsoft/LinkedIn), Magic Link, Password Reset, Email Verification
  - ✅ Migré `projects.py` : CRUD projets complet + stats
  - ✅ Migré `dashboard.py` : Stats, activité récente, quick stats
  - ✅ Migré `notifications.py` : CRUD notifications
  - ✅ Migré `schedules.py` : Scans programmés CRUD
  - ✅ Migré `subscriptions.py` : Abonnements, checkout Stripe, cancel/reactivate
  - ✅ Supprimé ~1467 lignes de code dupliqué de server.py
  - ✅ server.py réduit de 5875 à 4408 lignes (-25%)
  - ✅ Tous les 10 routers activés et testés
  
- **Routers actifs** : auth, projects, dashboard, notifications, schedules, subscriptions, organizations, article_optimizer, admin, onboarding
- **Reste dans server.py** : Analysis pipeline (complexe), Content generation, Visibility tracking

- Ajout Optimiseur d'Article GEO (frontend + backend)
- Ajout système Organisations/Workspaces
- Ajout Admin Backoffice
- **Ajout Onboarding Guidé interactif** (6 étapes avec illustrations)
- **Ajout Emails Transactionnels** (bienvenue, fin scan, désabonnement)
- **Ajout Gestion abonnements** (annulation/réactivation)
- Création architecture modulaire `/app/backend/app/`
- Nouveaux engines: Query, Semantic, Influence, Gap, Optimizer
- Composant FeatureTips pour tooltips contextuels
- Service EmailService avec templates HTML responsives
- Mise à jour plans d'abonnement avec nouvelles features

### Session 13 Mars 2026 - Déploiement Railway & Production

#### Déploiement Production ✅
- **Frontend**: https://www.iaskan.com (Railway)
- **Backend**: https://api.iaskan.com (Railway)
- **Base de données**: Supabase PostgreSQL avec pgvector

#### Accomplissements
- ✅ Déploiement monorepo sur Railway (backend + frontend)
- ✅ Configuration domaine personnalisé (iaskan.com, api.iaskan.com)
- ✅ Google OAuth natif (sans dépendance Emergent Auth)
- ✅ Migration vers Supabase PostgreSQL avec pgvector
- ✅ Abstraction layer pour portabilité (emergentintegrations → native SDKs)
- ✅ Admin Backoffice PostgreSQL (12 endpoints)
- ✅ Onglet Analyses dans Admin avec erreurs
- ✅ CORS configuré pour credentials

#### Variables d'environnement Railway (Backend)
- `DATABASE_URL` - Supabase pooler connection
- `USE_POSTGRES=true`
- `FRONTEND_URL=https://www.iaskan.com`
- `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET`
- `SESSION_SECRET_KEY`

### Sessions précédentes
- Logo et branding IAskan
- Analyse concurrentielle améliorée
- Notifications en temps réel
- Scans programmés
- PDF reports


### 2026-03-16 - Correction des bugs P0 critiques

#### Bugs corrigés
1. **GET /api/organizations - Erreur 500 (AttributeError)** ✅ CORRIGÉ
   - Cause: `AttributeError: 'User' object has no attribute 'plan'`
   - Fix: Patch `getattr(user, 'plan', 'free')` dans `backend/app/routers/organizations.py` ligne 77
   - Statut: Vérifié par testing_agent

2. **GET /api/analysis/{id} - Attributs inexistants** ✅ CORRIGÉ
   - Cause: Le router référençait des attributs inexistants sur le modèle (`indices`, `stability_data`, `analysis_summary`, etc.)
   - Fix: Suppression des attributs inexistants dans `backend/app/routers/analysis.py`
   - Statut: Vérifié par testing_agent

3. **Création d'analyse - Status enum** ✅ CORRIGÉ
   - Cause: `status="pending"` (string) au lieu de `AnalysisStatus.PENDING` (enum)
   - Fix: Correction dans `server.py` lignes 1272 et 2647 pour utiliser l'enum
   - Statut: Vérifié par testing_agent

4. **update_analysis - Conversion status** ✅ CORRIGÉ
   - Fix: Ajout de la conversion automatique string -> enum dans `backend/app/services/analysis_runner.py`
   - Amélioration du logging pour le débogage

#### Tests effectués
- Backend: 22/22 tests passés (test_critical_fixes.py)
- Frontend: 25/25 tests passés (critical-pages + page-rendering)
- Total: 47 tests passés, 0 échoués

#### Bugs restants à traiter
- P2: Sidebar scroll bug (CSS semble correct, nécessite investigation supplémentaire)
- P3: setup-first-admin endpoint 500 error
- P4: Magic Link authentication 500 error

#### Files modifiés
- `/app/backend/app/routers/organizations.py` - getattr patch
- `/app/backend/app/routers/analysis.py` - Suppression attributs inexistants
- `/app/backend/app/services/analysis_runner.py` - Conversion enum + logging
- `/app/backend/server.py` - AnalysisStatus.PENDING
