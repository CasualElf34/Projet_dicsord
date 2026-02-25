"""
LIKOO APP LAUNCHER v2 — Electron-like launcher
Lance Likoo comme une vraie application desktop avec Electron
"""

import os
import sys
import subprocess
import webbrowser
import time
from pathlib import Path

class LikooApp:
    def __init__(self):
        self.port = 5000
        self.host = 'localhost'
        self.url = f'http://{self.host}:{self.port}'
        
    def check_dependencies(self):
        """Verifie que Node et npm sont installes"""
        try:
            subprocess.run(['npm', '--version'], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("[ERROR] Node.js/npm n'est pas installe")
            print("[INFO] Telecharger depuis: https://nodejs.org")
            return False
    
    def install_dependencies(self):
        """Installe les dependances npm"""
        try:
            print("[INFO] Installation des dependances npm...")
            subprocess.run(['npm', 'install'], cwd=Path(__file__).parent, check=True)
            return True
        except subprocess.CalledProcessError:
            print("[ERROR] Erreur lors de l'installation npm")
            return False
    
    def run_electron(self):
        """Lance l'app Electron"""
        try:
            print("[INFO] Lancement de Likoo avec Electron...")
            subprocess.run(['npm', 'start'], cwd=Path(__file__).parent, check=True)
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Erreur au lancement d'Electron: {e}")
            return False
        return True
    
    def run(self):
        """Lance l'application"""
        print("""
╔════════════════════════════════════════════╗
║        🎵 LIKOO v2 — Application            ║
║  Discord-like avec Authentification          ║
╚════════════════════════════════════════════╝
        """)
        
        # Vérifie les dépendances
        if not self.check_dependencies():
            sys.exit(1)
        
        # Installe les dépendances si nécessaire
        if not Path('node_modules').exists():
            if not self.install_dependencies():
                sys.exit(1)
        
        # Lance Electron
        if not self.run_electron():
            sys.exit(1)

if __name__ == '__main__':
    app = LikooApp()
    app.run()
