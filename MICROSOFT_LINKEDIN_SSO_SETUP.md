# Configuration Microsoft & LinkedIn SSO pour IAskan

Ce guide explique comment configurer l'authentification Microsoft (Azure AD) et LinkedIn pour IAskan.

## 1. Microsoft SSO (Azure AD)

### Étape 1: Créer une application Azure AD

1. Accédez au [Azure Portal](https://portal.azure.com)
2. Allez dans **Azure Active Directory** > **App registrations** > **New registration**
3. Configurez :
   - **Name**: `IAskan`
   - **Supported account types**: "Accounts in any organizational directory and personal Microsoft accounts"
   - **Redirect URI**: 
     - Type: Web
     - URL: `https://api.iaskan.com/api/auth/microsoft/callback`

### Étape 2: Obtenir les credentials

1. Sur la page de l'application, notez :
   - **Application (client) ID** → `MICROSOFT_CLIENT_ID`
   - **Directory (tenant) ID** (optionnel pour multi-tenant)

2. Allez dans **Certificates & secrets** > **New client secret**
   - Description: `IAskan Production`
   - Expires: 24 months
   - Copiez la **Value** → `MICROSOFT_CLIENT_SECRET`

### Étape 3: Configurer les permissions

1. Allez dans **API permissions** > **Add a permission**
2. Sélectionnez **Microsoft Graph** > **Delegated permissions**
3. Ajoutez :
   - `openid`
   - `email`
   - `profile`
   - `User.Read`

### Variables d'environnement

```env
MICROSOFT_CLIENT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
MICROSOFT_CLIENT_SECRET=votre-secret-ici
MICROSOFT_TENANT_ID=common  # ou votre tenant ID spécifique
```

---

## 2. LinkedIn SSO

### Étape 1: Créer une application LinkedIn

1. Accédez à [LinkedIn Developers](https://www.linkedin.com/developers/apps)
2. Cliquez sur **Create app**
3. Remplissez :
   - **App name**: `IAskan`
   - **LinkedIn Page**: Sélectionnez votre page entreprise
   - **App logo**: Uploadez le logo IAskan
   - **Legal agreement**: Acceptez

### Étape 2: Configurer OAuth 2.0

1. Allez dans l'onglet **Auth**
2. Dans **OAuth 2.0 settings**, ajoutez le redirect URL :
   - `https://api.iaskan.com/api/auth/linkedin/callback`

3. Notez :
   - **Client ID** → `LINKEDIN_CLIENT_ID`
   - **Client Secret** → `LINKEDIN_CLIENT_SECRET`

### Étape 3: Demander les produits

1. Allez dans l'onglet **Products**
2. Demandez l'accès à :
   - **Sign In with LinkedIn using OpenID Connect** (requis)

### Variables d'environnement

```env
LINKEDIN_CLIENT_ID=xxxxxxxxx
LINKEDIN_CLIENT_SECRET=xxxxxxxxxxxxxxxx
```

---

## 3. Mise à jour de l'environnement Railway

1. Dans Railway, allez dans votre service backend
2. Ouvrez **Variables**
3. Ajoutez les 4 variables (Microsoft + LinkedIn)
4. Redéployez le service

---

## 4. Test

### Microsoft
```bash
curl https://api.iaskan.com/api/auth/providers
# Devrait retourner: {"microsoft": true, ...}
```

### LinkedIn
```bash
curl https://api.iaskan.com/api/auth/providers
# Devrait retourner: {"linkedin": true, ...}
```

---

## Dépannage

### Erreur "Microsoft OAuth non configuré"
- Vérifiez que `MICROSOFT_CLIENT_ID` et `MICROSOFT_CLIENT_SECRET` sont définis

### Erreur "token_exchange_failed"
- Vérifiez que le redirect URI dans Azure correspond exactement à celui de l'API
- Vérifiez que le client secret n'a pas expiré

### Erreur "userinfo_failed" (LinkedIn)
- Assurez-vous que le produit "Sign In with LinkedIn using OpenID Connect" est approuvé
- Cette approbation peut prendre quelques jours

### Erreur "invalid_state"
- Les cookies de session ne fonctionnent pas correctement
- Vérifiez la configuration CORS et les cookies cross-domain
