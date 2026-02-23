/**
 * PRELOAD SCRIPT — Electron
 * Expose les APIs IPC sécurisées au processus de rendu
 */

const { contextBridge, ipcRenderer } = require('electron');

// Expose les APIs sûres au contexte du renderer
contextBridge.exposeInMainWorld('electron', {
  ipc: {
    send: (channel, data) => ipcRenderer.send(channel, data),
    on: (channel, func) => ipcRenderer.on(channel, (event, ...args) => func(...args)),
    off: (channel, func) => ipcRenderer.removeListener(channel, func)
  }
});

contextBridge.exposeInMainWorld('electronAPI', {
  // Gestion de la fenêtre
  minimizeWindow: () => ipcRenderer.send('minimize-window'),
  maximizeWindow: () => ipcRenderer.send('maximize-window'),
  closeWindow: () => ipcRenderer.send('close-window'),
  
  // Info app
  getAppVersion: (callback) => ipcRenderer.once('app-version', callback),
  
  // Événements
  on: (channel, func) => {
    ipcRenderer.on(channel, (event, ...args) => func(...args));
  },
  off: (channel, func) => {
    ipcRenderer.removeListener(channel, func);
  },
  send: (channel, data) => {
    ipcRenderer.send(channel, data);
  }
});

