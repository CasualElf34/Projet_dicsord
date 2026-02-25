/**
 * LIKOO MAIN PROCESS — Electron
 * Gère la fenêtre et le cycle de vie de l'app
 */

let app, BrowserWindow, Menu, ipcMain;
try {
  const electron = require('electron');
  console.log('Electron loaded:', { app: !!electron.app, BrowserWindow: !!electron.BrowserWindow });
  app = electron.app;
  BrowserWindow = electron.BrowserWindow;
  Menu = electron.Menu;
  ipcMain = electron.ipcMain;
  console.log('Destructured:', { app: !!app, BrowserWindow: !!BrowserWindow });
} catch(e) {
  console.error('Electron loading error:', e);
  process.exit(1);
}

const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');

function loadEnvFromFile() {
  if (process.env.GOOGLE_CLIENT_ID) return;
  const envPath = path.join(__dirname, '.env');
  if (!fs.existsSync(envPath)) return;

  const content = fs.readFileSync(envPath, 'utf8');
  content.split(/\r?\n/).forEach((line) => {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) return;
    const idx = trimmed.indexOf('=');
    if (idx === -1) return;
    const key = trimmed.slice(0, idx).trim();
    let value = trimmed.slice(idx + 1).trim();
    value = value.replace(/^"|"$/g, '').replace(/^'|'$/g, '');
    if (!process.env[key]) process.env[key] = value;
  });
}

loadEnvFromFile();

// electron-is-dev simple - assume dev because we're not packaged
let isDev = true; // Force dev mode for now

let mainWindow;
let serverProcess;

// ═══════════════════════════════════════════════════
// CRÉATION DE LA FENÊTRE
// ═══════════════════════════════════════════════════

function createWindow() {
  // Crée la fenêtre du navigateur
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 900,
    minHeight: 600,
    frame: false,                     // hide native frame so we can style our own
    backgroundColor: '#18191c',       // dark theme color matching CSS
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      enableRemoteModule: false,
      preload: path.join(__dirname, 'preload.js')
    },
    icon: path.join(__dirname, 'assets', 'icon.png')
  });

  // Charge l'URL en dev ou le fichier en prod
  const startUrl = isDev
    ? 'http://localhost:5000'
    : `file://${path.join(__dirname, '../build/index.html')}`;

  mainWindow.loadURL(startUrl);

  // Ouvre les devtools uniquement si on passe explicitement la variable
  // d'environnement OPEN_DEVTOOLS ou si on est en mode développement et
  // que l'utilisateur a besoin de déboguer.
  // Par défaut on ne les affiche pas pour éviter l'ouverture automatique.
  if ((isDev && process.env.OPEN_DEVTOOLS==='1') || process.env.OPEN_DEVTOOLS==='1') {
    mainWindow.webContents.openDevTools();
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// ═══════════════════════════════════════════════════
// DÉMARRAGE DU SERVEUR PYTHON
// ═══════════════════════════════════════════════════

function startServer() {
  // Serveur Python tourne déjà - ne rien faire ici
  console.log('✅ Serveur Python externe détecté');
}

// ═══════════════════════════════════════════════════
// ═══════════════════════════════════════════════════
// CYCLE DE VIE DE L'APPLICATION
// ═══════════════════════════════════════════════════

app.on('ready', () => {
  // Electron permissions for media devices (camera, microphone, screen sharing)
  const { session } = require('electron');
  session.defaultSession.setPermissionRequestHandler((webContents, permission, callback) => {
    // Allow camera, microphone, and screen capture permissions
    if (permission === 'media' || permission === 'camera' || permission === 'microphone' || permission === 'display-capture') {
      callback(true);
    } else {
      callback(false);
    }
  });

  // Attend plus longtemps pour que le serveur démarre bien
  startServer();
  setTimeout(createWindow, 4000);
  createMenu();
  
  // Setup window control IPC handlers
  ipcMain.on('window:minimize', () => {
    if (mainWindow) mainWindow.minimize();
  });
  
  ipcMain.on('window:maximize', () => {
    if (mainWindow) {
      if (mainWindow.isMaximized()) {
        mainWindow.unmaximize();
      } else {
        mainWindow.maximize();
      }
    }
  });
  
  ipcMain.on('window:close', () => {
    if (mainWindow) mainWindow.close();
  });
});

app.on('window-all-closed', () => {
  // Termine le processus serveur
  if (serverProcess) {
    serverProcess.kill();
  }
  
  // Sur macOS, reste actif jusqu'à l'arrêt explicite
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  // Sur macOS, recréé la fenêtre quand on clique sur l'icône
  if (mainWindow === null) {
    createWindow();
  }
});

// ═══════════════════════════════════════════════════
// MENU
// ═══════════════════════════════════════════════════

function createMenu() {
  const template = [
    {
      label: 'Likoo',
      submenu: [
        {
          label: 'À propos de Likoo',
          click: () => {
            const { dialog } = require('electron');
            dialog.showMessageBox(mainWindow, {
              type: 'info',
              title: 'À propos de Likoo',
              message: 'Likoo v1.0.0',
              detail: 'Une alternative Discord-like stylisée.\n\nTechnologies: Electron, Flask, SQLite, WebSocket'
            });
          }
        },
        { type: 'separator' },
        {
          label: 'Paramètres',
          accelerator: 'CmdOrCtrl+,',
          click: () => {
            console.log('Paramètres...');
          }
        },
        { type: 'separator' },
        {
          label: 'Quitter',
          accelerator: 'CmdOrCtrl+Q',
          click: () => {
            if (serverProcess) serverProcess.kill();
            app.quit();
          }
        }
      ]
    },
    {
      label: 'Édition',
      submenu: [
        { role: 'undo' },
        { role: 'redo' },
        { type: 'separator' },
        { role: 'cut' },
        { role: 'copy' },
        { role: 'paste' }
      ]
    },
    {
      label: 'Affichage',
      submenu: [
        { role: 'reload' },
        { role: 'forceReload' },
        { role: 'toggleDevTools' },
        { type: 'separator' },
        { role: 'resetZoom' },
        { role: 'zoomIn' },
        { role: 'zoomOut' },
        { type: 'separator' },
        { role: 'togglefullscreen' }
      ]
    },
    {
      label: 'Aide',
      submenu: [
        {
          label: 'Documentation',
          click: async () => {
            const { shell } = require('electron');
            await shell.openExternal('https://github.com/yourusername/likoo');
          }
        }
      ]
    }
  ];

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}

// ═══════════════════════════════════════════════════
// GOOGLE OAUTH HANDLER - Simplified
// ═══════════════════════════════════════════════════

const { shell } = require('electron');

ipcMain.handle('google-oauth', async (event) => {
  return new Promise((resolve, reject) => {
    const GOOGLE_CLIENT_ID = process.env.GOOGLE_CLIENT_ID;
    if (!GOOGLE_CLIENT_ID) {
      reject(new Error('GOOGLE_CLIENT_ID missing'));
      return;
    }

    const state = Math.random().toString(36).substring(2, 15);
    
    // Use the redirect_uri that is registered in Google Console
    const authUrl = `https://accounts.google.com/o/oauth2/v2/auth?` +
      `client_id=${GOOGLE_CLIENT_ID}&` +
      `redirect_uri=http://localhost:5000/oauth/google/callback&` +
      `response_type=code&` +
      `scope=openid email profile&` +
      `state=${state}`;

    shell.openExternal(authUrl);

    // Poll for token
    const checkInterval = setInterval(async () => {
      try {
        const response = await fetch(`http://localhost:5000/api/auth/google/token?state=${state}`);
        const data = await response.json();
        
        if (data.token) {
          clearInterval(checkInterval);
          clearTimeout(timeout);
          resolve({ token: data.token });
        }
      } catch (error) {
        // Continue polling
      }
    }, 1000);

    // Timeout after 5 minutes
    const timeout = setTimeout(() => {
      clearInterval(checkInterval);
      reject(new Error('Timeout - Auth cancelled'));
    }, 300000);
  });
});

// ═══════════════════════════════════════════════════
// IPC HANDLERS
// ═══════════════════════════════════════════════════

ipcMain.on('app-version', (event) => {
  event.reply('app-version', {
    version: app.getVersion(),
    node: process.versions.node,
    chrome: process.versions.chrome,
    electron: process.versions.electron
  });
});

ipcMain.on('minimize-window', () => {
  if (mainWindow) mainWindow.minimize();
});

ipcMain.on('maximize-window', () => {
  if (mainWindow) {
    if (mainWindow.isMaximized()) {
      mainWindow.unmaximize();
    } else {
      mainWindow.maximize();
    }
  }
});

ipcMain.on('close-window', () => {
  if (mainWindow) mainWindow.close();
});

// ═══════════════════════════════════════════════════
// GESTION D'ERREURS
// ═══════════════════════════════════════════════════

process.on('uncaughtException', (error) => {
  console.error('Erreur non capturée:', error);
});
