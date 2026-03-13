# IAskan - Guide de Déploiement Railway

## Architecture du Déploiement

IAskan est composé de plusieurs services qui doivent être déployés séparément sur Railway :

1. **Backend API** (FastAPI)
2. **Frontend** (React)
3. **Celery Worker** (Traitement asynchrone)
4. **Celery Beat** (Scheduler - optionnel)
5. **Redis** (File d'attente des tâches)
6. **PostgreSQL** (Base de données)

## Configuration Railway

### Option 1 : Déploiement Monorepo (Recommandé)

1. **Créer un nouveau projet** sur Railway
2. **Ajouter les services** :

#### Service Backend
- Root Directory: `backend`
- Start Command: `python -m uvicorn server:app --host 0.0.0.0 --port $PORT`
- Variables d'environnement requises :
  ```
  DATABASE_URL=postgresql://...
  REDIS_URL=redis://...
  EMERGENT_LLM_KEY=sk-emergent-...
  STRIPE_API_KEY=sk_test_...
  RESEND_API_KEY=re_...
  USE_POSTGRES=true
  ```

#### Service Frontend
- Root Directory: `frontend`
- Build Command: `yarn build`
- Start Command: `npx serve -s build -l $PORT`
- Variables d'environnement requises :
  ```
  REACT_APP_BACKEND_URL=https://votre-backend.railway.app
  ```

#### Service Celery Worker
- Root Directory: `backend`
- Start Command: `celery -A app.core.celery_app worker --loglevel=info`
- Variables d'environnement : Mêmes que le backend

### Option 2 : Utiliser start.sh

Définissez la variable `SERVICE` pour chaque service :
- `SERVICE=backend`
- `SERVICE=frontend`
- `SERVICE=celery-worker`
- `SERVICE=celery-beat`

## Services Additionnels

### PostgreSQL
- Utilisez le plugin PostgreSQL de Railway
- Ou connectez-vous à Supabase/Railway externe

### Redis
- Utilisez le plugin Redis de Railway
- Copiez `REDIS_URL` vers les services backend et celery

## Variables d'Environnement

| Variable | Service | Description |
|----------|---------|-------------|
| `DATABASE_URL` | Backend, Celery | URL PostgreSQL |
| `REDIS_URL` | Backend, Celery | URL Redis |
| `EMERGENT_LLM_KEY` | Backend | Clé API pour LLMs |
| `STRIPE_API_KEY` | Backend | Clé Stripe |
| `RESEND_API_KEY` | Backend | Clé Resend pour emails |
| `REACT_APP_BACKEND_URL` | Frontend | URL du backend |
| `USE_POSTGRES` | Backend | Activer PostgreSQL |

## Étapes de Déploiement

1. **Fork/Push le code** sur GitHub
2. **Créer un projet Railway** et connecter le repo
3. **Ajouter PostgreSQL** via le plugin Railway
4. **Ajouter Redis** via le plugin Railway
5. **Configurer les variables** d'environnement
6. **Déployer les services** dans l'ordre :
   - PostgreSQL et Redis (automatique)
   - Backend
   - Celery Worker
   - Frontend

## Healthcheck

Le backend expose un endpoint `/api/health` pour vérifier l'état du service.

## Troubleshooting

### Erreur "Railpack n'a pas pu déterminer comment construire"
- Vérifiez que `start.sh` est présent à la racine
- Ou configurez `nixpacks.toml` avec le bon chemin

### Erreur de connexion PostgreSQL
- Vérifiez `DATABASE_URL` est correctement formatée
- Assurez-vous que le service PostgreSQL est démarré

### Erreur Celery
- Vérifiez que Redis est accessible
- Confirmez que `REDIS_URL` est configurée
