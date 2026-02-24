# 🔐 Google OAuth Configuration Guide

## Étape 1: Créer un Projet Google Cloud

1. Accédez à [Google Cloud Console](https://console.cloud.google.com/)
2. Cliquez sur le menu déroulant en haut à gauche
3. Sélectionnez "NEW PROJECT"
4. Donnez un nom à votre projet (ex: "Likoo")
5. Cliquez sur "CREATE"
6. Attendez que le projet soit créé

## Étape 2: Configurer OAuth Consent Screen

1. Dans Google Cloud Console, naviguez à **APIs & Services** > **OAuth Consent Screen**
2. Sélectionnez **External** comme type d'utilisateur
3. Cliquez sur **CREATE**
4. Remplissez les informations requises:
   - **App Name**: Likoo
   - **User Support Email**: votre email
   - **Developer Contact Information**: votre email
5. Cliquez sur **SAVE AND CONTINUE**
6. Ignorez "Scopes" et cliquez sur **SAVE AND CONTINUE**
7. Cliquez sur **SAVE AND CONTINUE** à nouveau (pas besoin d'ajouter d'utilisateurs de test en développement)

## Étape 3: Créer les Identifiants OAuth

1. Naviguez à **APIs & Services** > **Credentials**
2. Cliquez sur **CREATE CREDENTIALS** > **OAuth 2.0 Client ID**
3. Sélectionnez **Web application**
4. Donnez un nom (ex: "Likoo Web")
5. Ajoutez les **Authorized JavaScript origins**:
   - `http://localhost:5000`
   - `http://localhost:3000`
   - `http://127.0.0.1:5000`
6. Les **Authorized redirect URIs** (pour le moment, vous pouvez les laisser vides ou ajouter):
   - `http://localhost:5000/auth`
   - `http://localhost:5000/api/auth/callback`
7. Cliquez sur **CREATE**
8. Copiez votre **Client ID**

## Étape 4: Configurer les Fichiers Locaux

### 1. Créer le fichier `.env`

À la racine de votre projet, créez un fichier `.env`:

```
GOOGLE_CLIENT_ID=YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com
JWT_SECRET=dev-secret-key-change-in-production
```

Remplacez `YOUR_GOOGLE_CLIENT_ID` par le Client ID que vous avez copié.

### 2. Configurer le Client ID dans `auth.html`

Dans le fichier `auth.html`, remplacez `YOUR_GOOGLE_CLIENT_ID` par votre Client ID réel dans la ligne:

```javascript
client_id: 'YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com',
```

## Étape 5: Installer les Dépendances

Installez les packages Python requis:

```bash
pip install -r requirements.txt
```

## Étape 6: Tester la Connexion Google

1. Démarrez votre serveur Flask:
   ```bash
   python server.py
   ```

2. Ouvrez votre navigateur sur `http://localhost:5000/auth.html`

3. Cliquez sur le bouton "Connexion Google"

4. Sélectionnez votre compte Google

5. Vous devriez être automatiquement connecté et redirigé vers l'application

## 🚀 Pour la Production

Quand vous déployerez en production:

1. Mettez à jour votre **GOOGLE_CLIENT_ID** avec un nouveau créé pour votre domaine
2. Ajoutez votre domaine de production aux **Authorized JavaScript origins** dans Google Cloud Console
3. Changez le **JWT_SECRET** par une clé secrète forte et unique
4. Utilisez les variables d'environnement pour stocker ces secrets de manière sécurisée

## ✅ Vérification

- ✓ Vous pouvez vous connecter avec Google
- ✓ Un compte utilisateur est créé automatiquement
- ✓ Vous êtes redirigé vers l'application principale
- ✓ Vous pouvez vous connecter avec votre email Google

## 🐛 Dépannage

### "Token invalide"
- Assurez-vous que votre `GOOGLE_CLIENT_ID` est correct
- Vérifiez que vous avez autorisé `localhost:5000` dans les "Authorized JavaScript origins"

### CORS Error
- Assurez-vous que votre serveur Flask a `CORS` correctement configuré
- Vérifiez les logs du serveur pour plus de détails

### Hors ligne / Développement
Le système fonctionne même sans vérification stricte du token Google en développement (avec parsing JWT), mais en production, ajustez la configuration de sécurité selon vos besoins.

