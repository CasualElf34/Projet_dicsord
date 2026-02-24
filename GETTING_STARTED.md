# 🚀 LIKOO v2 — Setup Complet

Une application **Discord-like** moderne avec authentification, base de données et chat temps réel!

## ✨ Nouvelles Fonctionnalités v2

✅ **Base de données SQLite** — Persistance des données  
✅ **Authentification JWT** — Login/Register sécurisé  
✅ **WebSocket** — Chat temps réel (Socket.io)  
✅ **Electron** — App desktop native  
✅ **Système de tags** — Pseudo unique avec numéro (ex: Zara#4521)  
✅ **Multi-serveurs** — Créé tes propres serveurs  

---

## 📋 Installation Rapide

### **1. Prérequis**

- **Python 3.8+** — [Télécharger](https://www.python.org)
- **Node.js 14+** — [Télécharger](https://nodejs.org)
- **Git** (optionnel)

### **2. Installation des dépendances Python**

```bash
cd c:\Users\maelg\Desktop\Projet_dicsord
pip install -r requirements.txt
```

### **3. Installation des dépendances Node.js**

```bash
npm install
```

---

## 🎮 Lancer l'Application

### **Option 1: App Desktop Electron (Recommandé)**

```bash
npm start
```

L'app se lancera automatiquement!

### **Option 2: Dev Mode (avec hot-reload)**

```bash
npm run dev
```

Ça lance le serveur Flask + Electron en parallèle.

### **Option 3: Serveur seul (Testing API)**

```bash
python server.py
```

Puis ouvre http://localhost:5000

---

## 🔐 Premier Lancement

1. **L'app s'ouvre** → Page de login/register
2. **Crée un compte:**
   - Pseudo (unique)
   - Email
   - Mot de passe (min 6 caractères)
   - Choisis ton avatar (emoji ou upload d'une image/gif)
3. **C'est fait!** Tu accèdes à l'app Likoo

---

## 📁 Structure du Projet

```
Projet_dicsord/
├── 🖥️ FRONTEND
│   ├── index_source.html    # Page principale
│   ├── auth.html            # Page de login/register
│   ├── style.css            # Styles CSS
│   ├── app.js               # Logique frontend (880 lignes)
│   └── auth-middleware.js   # Authentification JS
│
├── 🔧 BACKEND (Python)
│   ├── server.py            # Serveur Flask + SocketIO
│   ├── models.py            # Modèles SQLAlchemy
│   ├── likoo.db             # Base de données SQLite (créée auto)
│   └── requirements.txt      # Dépendances Python
│
├── 🎯 ELECTRON (Desktop)
│   ├── main.js              # Processus principal Electron
│   ├── preload.js           # Script d'accès aux APIs
│   └── package.json         # Config npm + Electron
│
├── 📖 DOCUMENTATION
│   ├── README.md            # Ce fichier
│   ├── API.md               # Doc API (à venir)
│   └── DEPLOYMENT.md        # Déploiement prod (à venir)
```

---

## 🌐 API Endpoints

### **Authentification**

```
POST   /api/auth/register      Créer un compte
POST   /api/auth/login         Se connecter
GET    /api/auth/me            Récupère l'utilisateur actif
```

### **Serveurs**

```
GET    /api/servers            Liste tes serveurs
POST   /api/servers            Crée un serveur
GET    /api/servers/<id>       Détails d'un serveur
```

### **Canaux**

```
GET    /api/servers/<id>/channels       Liste les canaux
POST   /api/servers/<id>/channels       Crée un canal
```

### **Messages**

```
GET    /api/channels/<id>/messages      Historique
```

### **WebSocket Events**

```
emit('join_channel', {channel_id})
emit('send_message', {channel_id, content, user_id})
emit('user_status_change', {user_id, status})
listen('new_message')
listen('user_typing')
listen('user_status_changed')
```

---

## 🔑 Authentification JWT

Les tokens JWT sont:
- **Valides 30 jours**
- **Stockés** dans `localStorage`
- **Envoyés** dans le header `Authorization: Bearer <token>`

```javascript
// Exemple d'appel API avec JWT
const token = localStorage.getItem('likoo_token');

fetch('http://localhost:5000/api/servers', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
```

---

## 📦 Build pour Production

### **Créer un exécutable Windows**

```bash
npm run build:win
```

Génère un `.exe` dans `dist/`

### **Créer un DMG macOS**

```bash
npm run build:mac
```

### **Créer un AppImage Linux**

```bash
npm run build:linux
```

---

## 🐛 Troubleshooting

### **Erreur: Python non trouvé**

```bash
# Vérifier Python
python --version

# Ou ajouter Python au PATH (Windows)
# Réinstaller Python en cochant "Add Python to PATH"
```

### **Erreur: npm dependencies**

```bash
# Réinstaller les dépendances
rm -r node_modules package-lock.json
npm install
```

### **Erreur: Port 5000 déjà utilisé**

```bash
# Utiliser un autre port
PORT=3000 python server.py
```

### **Erreur: CORS**

Si les requêtes CORS échouent, vérifier que l'URL correspond:
- Dev: `http://localhost:5000`
- Production: Utiliser les vraies URLs

---

## 💡 Prochaines Étapes

- [ ] Ajouter MongoDB pour plus de scalabilité
- [ ] Notifications push (Desktop)
- [ ] Appels vocaux WebRTC
- [ ] Partage d'écran
- [ ] Intégration avec Spotify
- [ ] Badges et roles personnalisés
- [ ] Panels personnalisables
- [ ] Thème light mode
- [ ] Slash commands
- [ ] Bots API

---

## 📚 Ressources

- [Flask Documentation](https://flask.palletsprojects.com)
- [Socket.IO Guide](https://socket.io)
- [Electron Docs](https://www.electronjs.org)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org)
- [JWT.io](https://jwt.io)

---

## 🤝 Support

Pour les problèmes:
1. Vérifier les logs du terminal
2. Vérifier la console navigateur (F12)
3. Vérifier que le serveur est en cours d'exécution
4. Vérifier `likoo.db` existe et n'est pas corrompu

---

## 📄 Licence

MIT — Utilise librement!

---

**Créé avec ❤️ en 2026**

Prêt à lancer ta Likoo? 🚀

```bash
npm start
```

---

## 🎯 Commandes Rapides

```bash
# Démarrer l'app
npm start

# Dev mode avec hot-reload
npm run dev

# Juste le serveur
npm run server

# Juste Electron
npm run electron

# Build Windows
npm run build:win

# Installer les dépendances
npm install
pip install -r requirements.txt
```

---

**Bon développement! 💜**
