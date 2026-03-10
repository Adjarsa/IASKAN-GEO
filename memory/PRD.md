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
│   │   ├── routers/       # API routes (organizations, article_optimizer, admin)
│   │   ├── engines/       # Core GEO engines
│   │   │   ├── query/     # Query generation & variation
│   │   │   ├── semantic/  # Semantic analysis
│   │   │   ├── influence/ # Influence mapping
│   │   │   ├── gap/       # Content gap finder
│   │   │   └── optimizer/ # Article optimizer
│   │   └── services/      # Business logic
│   ├── tests/
│   └── server.py          # Main FastAPI app (monolithique - à refactorer)
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

## Notes Critiques

⚠️ **NE PAS UPGRADER REACT** - Version 18.2.0 verrouillée (bug `insertBefore`)

⚠️ **server.py** - Fichier monolithique de 5700+ lignes, refactoring prioritaire

⚠️ **Tests en attente** - PDF download, URL truncation, timeout backend

## Changelog

### 2026-03-10
- Ajout Optimiseur d'Article GEO (frontend + backend)
- Ajout système Organisations/Workspaces
- Ajout Admin Backoffice
- Création architecture modulaire `/app/backend/app/`
- Nouveaux engines: Query, Semantic, Influence, Gap, Optimizer
- Mise à jour plans d'abonnement avec nouvelles features

### Sessions précédentes
- Logo et branding IAskan
- Analyse concurrentielle améliorée
- Notifications en temps réel
- Scans programmés
- PDF reports
