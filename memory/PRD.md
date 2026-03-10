# IAskan - Plateforme GEO SaaS

## Vision Produit
IAskan est une plateforme **Generative Engine Optimization (GEO)** qui aide les entreprises à optimiser leur visibilité dans les réponses générées par l'IA (ChatGPT, Claude, Gemini, Perplexity).

## Architecture Technique

### Stack
- **Frontend**: React 18.2.0 (version verrouillée), Tailwind CSS, Shadcn/UI
- **Backend**: FastAPI, Python 3.11
- **Database**: MongoDB
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
│   │   │   ├── auth.py           # ✅ Authentification complète
│   │   │   ├── projects.py       # ✅ CRUD projets
│   │   │   ├── dashboard.py      # ✅ Stats dashboard
│   │   │   ├── organizations.py  # ✅ Gestion organisations
│   │   │   ├── article_optimizer.py # ✅ Optimiseur articles
│   │   │   ├── admin.py          # ✅ Admin backoffice
│   │   │   └── onboarding.py     # ✅ Onboarding utilisateur
│   │   ├── engines/       # Core GEO engines
│   │   │   ├── query/     # Query generation & variation
│   │   │   ├── semantic/  # Semantic analysis
│   │   │   ├── influence/ # Influence mapping
│   │   │   ├── gap/       # Content gap finder
│   │   │   └── optimizer/ # Article optimizer
│   │   └── services/      # Business logic
│   ├── tests/
│   │   └── test_router_endpoints.py  # 29 tests d'intégration
│   └── server.py          # Main FastAPI app (~4870 lignes)
├── frontend/
│   ├── src/
│   │   ├── components/    # UI components
│   │   ├── pages/         # Page components
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

### Article Optimizer
- `POST /api/article-optimizer/analyze` - Analyse basique
- `POST /api/article-optimizer/analyze-with-llm` - Analyse enrichie IA
- `GET /api/article-optimizer/quota` - Vérifier quota
- `GET /api/article-optimizer/history` - Historique

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

### 2026-03-10 (Session actuelle)
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

### Sessions précédentes
- Logo et branding IAskan
- Analyse concurrentielle améliorée
- Notifications en temps réel
- Scans programmés
- PDF reports
