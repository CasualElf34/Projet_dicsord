# 🚀 LIKOO — Application Discord-like

Une application web moderne et stylisée inspirée de Discord avec une interface flottante customisable.

## ✨ Fonctionnalités

- 💬 Chat en temps réel
- 🖼️ Panneaux flottants draggables
- 👥 Systèmes de serveurs et canaux
- 📱 Interface responsive (desktop/mobile)
- 🎨 Thème dark mode avec gradients
- 🔊 Support pour les canaux vocaux
- 🎭 Avatars personnalisables (emoji, photo ou GIF) et statuts utilisateur

## 🛠️ Installation

### Prérequis
- Python 3.8+
- pip (gestionnaire de paquets Python)

### Étapes

1. **Cloner/télécharger le projet**
```bash
cd Projet_dicsord
```

2. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

3. **Lancer l'application**

**Windows:**
```bash
launch_likoo.bat
```

**Mac/Linux:**
```bash
bash launch_likoo.sh
```

Ou directement avec Python:
```bash
python app_launcher.py
```

L'application s'ouvrira automatiquement sur http://localhost:5000

## 📁 Structure du projet

```
Projet_dicsord/
├── index_source.html    # Page HTML principale
├── likoo.html           # Alternative HTML
├── style.css            # Styles CSS
├── app.js               # Logique frontend (880 lignes)
├── server.py            # Serveur Flask backend
├── app_launcher.py      # Launcher de l'application
├── launch_likoo.bat     # Launcher Windows
├── launch_likoo.sh      # Launcher Mac/Linux
├── requirements.txt     # Dépendances Python
└── README.md           # Ce fichier
```

## 🔌 API Backend

Le serveur Flask expose une API REST:

### Serveurs
- `GET /api/servers` - Liste tous les serveurs
- `GET /api/servers/<id>` - Récupère un serveur
- `POST /api/servers` - Crée un serveur

### Canaux
- `GET /api/servers/<id>/channels` - Liste les canaux
- `POST /api/servers/<id>/channels` - Crée un canal

### Messages
- `GET /api/channels/<id>/messages` - Récupère les messages
- `POST /api/channels/<id>/messages` - Envoie un message

### Utilisateurs
- `GET /api/users` - Liste les utilisateurs
- `GET /api/users/<id>` - Récupère un utilisateur

### Santé
- `GET /health` - Vérifie que le serveur fonctionne

## 🎯 Utilisation

1. **Démarrer l'app** via `launch_likoo.bat` (Windows) ou `launch_likoo.sh` (Mac/Linux)
2. Le navigateur s'ouvre automatiquement
3. Cliquez sur votre profil (ou ouvrez les paramètres) pour modifier votre avatar : vous pouvez choisir un emoji ou téléverser une photo/GIF.
   Vous trouverez maintenant deux onglets dans la fenêtre de paramètres : **Mon compte** (avatar, nom, statut) et **Apparence** qui permet de choisir un fond/bannière couleur prédéfinie ou une couleur personnalisée.
4. Interagir avec les panneaux flottants
5. Écrire des messages dans les canaux
6. Presser CTRL+C dans le terminal pour quitter

## 🚀 Prochaines étapes

Pour transformer ça en vrai app desktop like Discord:

### Option 1: Electron (Recommandé)
```bash
npm init -y
npm install electron --save-dev
```

### Option 2: PyQt/PySimpleGUI
Créer une fenêtre native avec Python GUI

### Option 3: Packaging
Utiliser PyInstaller pour créer un `.exe` Windows standalone

## 🎨 Customisation

- Modifier les couleurs dans `style.css` (variables CSS)
- Ajouter des serveurs/utilisateurs dans `server.py`
- Éditer la structure HTML dans `index_source.html`

## 📝 Notes

- Les données sont stockées en mémoire (volatile)
- Pour un vrai projet, utiliser une base de données (PostgreSQL, MongoDB, etc.)
- Ajouter l'authentification utilisateur
- Implémenter WebSocket pour le chat en temps réel

## 🔒 Sécurité (Production)

- Ajouter HTTPS/SSL
- Implémenter l'authentification
- Valider/nettoyer les inputs
- Utiliser une vraie base de données

## 📞 Support

Pour les questions, consulter les fichiers source ou la documentation Flask officielle.

---

**Version:** 1.0.0  
**Créé:** 2026  
**Licence:** MIT
