#!/usr/bin/env python3
"""
SETUP — Installation et Configuration de Likoo
Crée la base de données et les dossiers nécessaires
"""

import os
import sys
from pathlib import Path

def setup():
    """Configure l'environnement"""
    print("""
LIKOO v2 SETUP
Configuration de l'environnement
    """)
    
    base_dir = Path(__file__).parent
    
    # Crée les dossiers
    print("Création des repertoires...")
    (base_dir / 'assets').mkdir(exist_ok=True)
    (base_dir / 'logs').mkdir(exist_ok=True)
    (base_dir / 'data').mkdir(exist_ok=True)
    
    # Crée la base de données
    print("Initialisation de la base de donnees...")
    os.chdir(base_dir)
    
    try:
        from models import db
        from server import app
        
        with app.app_context():
            db.create_all()
            print("[OK] Base de donnees creee")
    except ImportError as e:
        print(f"[WARNING] Installation des dependances requise: {e}")
        print("Executer: pip install -r requirements.txt")
    except Exception as e:
        print(f"[ERROR] Erreur: {e}")
        return False
    
    # Fichier .env
    env_file = base_dir / '.env.example'
    if not env_file.exists():
        env_content = """# Configuration Likoo
DEBUG=True
PORT=5000
JWT_SECRET=your-secret-key-change-in-production
DATABASE_URL=sqlite:///likoo.db
FLASK_ENV=development
"""
        env_file.write_text(env_content)
        print("[OK] Fichier .env.example cree")
    
    print("""
SETUP TERMINE!
    
Prochaines etapes:

1. Installer les dependances:
   pip install -r requirements.txt
   npm install

2. Lancer l'application:
   npm start

3. Ouvrir http://localhost:5000

4. Creer ton compte et c'est parti!

Pour plus d'infos: voir GETTING_STARTED.md
    """)
    
    return True

if __name__ == '__main__':
    if not setup():
        sys.exit(1)
