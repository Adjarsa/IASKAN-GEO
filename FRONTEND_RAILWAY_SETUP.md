# Déploiement Frontend IAskan sur Railway

## Étape 1 : Créer un nouveau service sur Railway

1. Allez sur [Railway](https://railway.app)
2. Dans votre projet existant, cliquez sur **"+ New"** > **"GitHub Repo"**
3. Sélectionnez le même repository
4. **IMPORTANT** : Configurez le Root Directory sur `/frontend`

## Étape 2 : Configurer les variables d'environnement

Dans Railway > votre service frontend > Variables, ajoutez :

| Variable | Valeur |
|----------|--------|
| `REACT_APP_BACKEND_URL` | `https://rare-magic-production-fb42.up.railway.app` |
| `NODE_ENV` | `production` |

## Étape 3 : Vérifier les paramètres de build

Dans Settings, vérifiez :
- **Root Directory** : `/frontend`
- **Build Command** : (laissez vide, nixpacks.toml gère tout)
- **Start Command** : (laissez vide, nixpacks.toml gère tout)

## Étape 4 : Générer un domaine

1. Allez dans **Settings** > **Networking**
2. Cliquez sur **"Generate Domain"**
3. Notez l'URL générée (ex: `iaskan-frontend-xxxx.up.railway.app`)

## Étape 5 : Mettre à jour FRONTEND_URL sur le backend

Retournez sur votre service **backend** et mettez à jour :

| Variable | Nouvelle valeur |
|----------|-----------------|
| `FRONTEND_URL` | `https://votre-frontend-xxxx.up.railway.app` |

## Étape 6 : Mettre à jour Google OAuth

Dans [Google Cloud Console](https://console.cloud.google.com/apis/credentials) :

1. Ajoutez l'origine JavaScript autorisée :
   ```
   https://votre-frontend-xxxx.up.railway.app
   ```

2. L'URI de redirection reste le même (backend) :
   ```
   https://rare-magic-production-fb42.up.railway.app/api/auth/google/callback
   ```

## Vérification

1. Accédez à votre URL frontend
2. Cliquez sur "Continuer avec Google"
3. Vous devriez être redirigé vers le dashboard après connexion

## Dépannage

### Page blanche
- Vérifiez que `REACT_APP_BACKEND_URL` est correct
- Vérifiez les logs Railway du frontend

### Erreur CORS
- Vérifiez que le backend autorise l'origine du frontend

### Erreur OAuth
- Vérifiez que `FRONTEND_URL` sur le backend pointe vers le frontend
- Vérifiez les URIs autorisées dans Google Cloud Console
