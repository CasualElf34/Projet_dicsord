/**
 * LIKOO MAIN PROCESS — Electron
 * Gère la fenêtre et le cycle de vie de l'app
 */

const { app, BrowserWindow, Menu, ipcMain } = require('electron');
const path = require('path');
// electron-is-dev is now an ES module, import dynamically
let isDev = false;
(async () => {
  try {
    const esm = await import('electron-is-dev');
    isDev = esm.default;
  } catch (e) {
    console.warn('electron-is-dev import failed, assuming production', e);
  }
})();
const { spawn } = require('child_process');
const fs = require('fs');

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
  // Vérifie si Python est disponible
  const pythonPath = process.platform === 'win32' ? 'python' : 'python3';
  
  console.log('🚀 Démarrage du serveur Likoo...');
  
  serverProcess = spawn(pythonPath, [path.join(__dirname, 'server.py')], {
    cwd: __dirname,
    env: process.env,
    shell: true,
    stdio: ['ignore','pipe','pipe']
  });

  serverProcess.stdout.on('data', (data) => {
    console.log(data.toString());
  });
  serverProcess.stderr.on('data', (data) => {
    console.error(data.toString());
  });

  serverProcess.on('error', (error) => {
    console.error('❌ Erreur serveur:', error);
  });

  serverProcess.on('exit', (code) => {
    console.log(`✅ Serveur fermé avec code ${code}`);
  });
}

// ═══════════════════════════════════════════════════
// ═══════════════════════════════════════════════════
// CYCLE DE VIE DE L'APPLICATION
// ═══════════════════════════════════════════════════

app.on('ready', () => {
  // Attend un peu pour que le serveur démarre
  startServer();
  setTimeout(createWindow, 2000);
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
