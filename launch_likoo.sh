#!/bin/bash
# ════════════════════════════════════════════════
# LIKOO LAUNCHER — Unix/Linux/Mac Script
# Lance Likoo comme une vraie application
# ════════════════════════════════════════════════

echo ""
echo "╔════════════════════════════════════════════╗"
echo "║     LIKOO — Application Desktop v1.0        ║"
echo "║  Une alternative Discord-like stylisée      ║"
echo "╚════════════════════════════════════════════╝"
echo ""

# Vérifie si Python est installé
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 n'est pas installé"
    echo "Installer via: sudo apt install python3 python3-pip"
    exit 1
fi

# Vérifie si Flask est installé
python3 -c "import flask" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "📦 Installation des dépendances..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "❌ Erreur lors de l'installation"
        exit 1
    fi
fi

echo "✅ Tous les prérequis sont ok"
echo ""
echo "🚀 Démarrage de Likoo..."
echo ""

# Lance l'application
python3 app_launcher.py

if [ $? -ne 0 ]; then
    echo "❌ Erreur au lancement"
    exit 1
fi
