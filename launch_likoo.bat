@echo off
REM ════════════════════════════════════════════════
REM LIKOO LAUNCHER — Windows Batch Script
REM Lance Likoo comme une vraie application
REM ════════════════════════════════════════════════

title LIKOO — Application Desktop

echo.
echo ╔════════════════════════════════════════════╗
echo ║     LIKOO — Application Desktop v1.0        ║
echo ║  Une alternative Discord-like stylisée      ║
echo ╚════════════════════════════════════════════╝
echo.

REM Vérifie si Python est installé
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python n'est pas installé ou pas dans le PATH
    echo Télécharger Python depuis: https://www.python.org
    pause
    exit /b 1
)

REM Vérifie si les dépendances sont installées
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo 📦 Installation des dépendances...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ❌ Erreur lors de l'installation
        pause
        exit /b 1
    )
)

echo ✅ Tous les prérequis sont ok
echo.
echo 🚀 Démarrage de Likoo...
echo.

REM Lance l'application
python app_launcher.py

if errorlevel 1 (
    echo ❌ Erreur au lancement
    pause
    exit /b 1
)
