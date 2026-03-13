# Configuration Google OAuth pour IAskan sur Railway

Ce guide vous explique comment configurer l'authentification Google OAuth pour votre déploiement Railway.

## Étape 1 : Créer un projet Google Cloud

1. Allez sur [Google Cloud Console](https://console.cloud.google.com/)
2. Créez un nouveau projet ou sélectionnez un projet existant
3. Notez l'ID du projet

## Étape 2 : Configurer l'écran de consentement OAuth

1. Dans le menu latéral, allez à **APIs & Services** > **OAuth consent screen**
2. Sélectionnez **External** (pour tous les utilisateurs)
3. Remplissez les informations requises :
   - **App name** : IAskan
   - **User support email** : votre email
   - **Developer contact information** : votre email
4. Cliquez sur **Save and Continue**
5. Dans **Scopes**, ajoutez :
   - `email`
   - `profile`
   - `openid`
6. Cliquez sur **Save and Continue**
7. Dans **Test users**, vous pouvez ajouter des utilisateurs de test (optionnel en mode production)
8. Cliquez sur **Save and Continue**

## Étape 3 : Créer les identifiants OAuth

1. Allez à **APIs & Services** > **Credentials**
2. Cliquez sur **+ CREATE CREDENTIALS** > **OAuth client ID**
3. Sélectionnez **Web application**
4. Configurez :
   - **Name** : IAskan Railway
   - **Authorized JavaScript origins** :
     ```
     https://rare-magic-production-fb42.up.railway.app
     ```
   - **Authorized redirect URIs** :
     ```
     https://rare-magic-production-fb42.up.railway.app/api/auth/google/callback
     ```
5. Cliquez sur **Create**
6. **IMPORTANT** : Notez le **Client ID** et le **Client Secret**

## Étape 4 : Configurer Railway

1. Allez sur votre dashboard Railway
2. Sélectionnez votre projet backend
3. Allez dans **Variables**
4. Ajoutez ces variables d'environnement :

| Variable | Valeur |
|----------|--------|
| `GOOGLE_CLIENT_ID` | `votre-client-id.apps.googleusercontent.com` |
| `GOOGLE_CLIENT_SECRET` | `votre-client-secret` |
| `FRONTEND_URL` | `https://votre-frontend.up.railway.app` (ou votre domaine custom) |

5. Railway redéploiera automatiquement votre application

## Étape 5 : Tester l'authentification

1. Vérifiez que l'endpoint `/api/auth/providers` retourne `"google": true`
2. Accédez à `https://rare-magic-production-fb42.up.railway.app/api/auth/google/login`
3. Vous devriez être redirigé vers la page de connexion Google

## Endpoints disponibles

| Endpoint | Description |
|----------|-------------|
| `GET /api/auth/providers` | Liste les providers OAuth disponibles |
| `GET /api/auth/google/login` | Initie la connexion Google |
| `GET /api/auth/google/callback` | Callback après authentification Google |
| `GET /api/auth/me` | Retourne l'utilisateur connecté |
| `POST /api/auth/logout` | Déconnexion |

## Notes importantes

- Le cookie de session est `httpOnly`, `secure` et `samesite=none`
- La session expire après 7 jours
- Les emails temporaires sont bloqués automatiquement

## Dépannage

### Erreur "Google OAuth non configuré"
→ Vérifiez que `GOOGLE_CLIENT_ID` et `GOOGLE_CLIENT_SECRET` sont bien définis dans Railway

### Erreur "invalid_state"
→ Le state OAuth a expiré. Réessayez la connexion.

### Erreur "redirect_uri_mismatch"
→ Vérifiez que l'URI de callback dans Google Cloud Console correspond exactement à :
`https://rare-magic-production-fb42.up.railway.app/api/auth/google/callback`

### Utilisateur redirigé vers /login?error=...
Vérifiez les logs Railway pour plus de détails sur l'erreur.
