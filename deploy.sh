#!/bin/bash
# ════════════════════════════════════════════════
# LIKOO DEPLOYMENT SCRIPT
# Déploie Likoo en production sur un serveur Linux
# ════════════════════════════════════════════════

set -e

echo "🚀 LIKOO DEPLOYMENT SCRIPT v2"
echo "================================"

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
DEPLOY_DIR="/opt/likoo"
SERVICE_NAME="likoo"
DOMAIN="${1:-localhost}"

# ════════════════════════════════════════════════
# VÉRIFICATIONS
# ════════════════════════════════════════════════

echo -e "${YELLOW}✓ Vérification des prérequis...${NC}"

# Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 non installé${NC}"
    echo "apt install python3 python3-pip python3-venv"
    exit 1
fi

# Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}✗ Node.js non installé${NC}"
    echo "curl -sL https://deb.nodesource.com/setup_16.x | sudo -E bash -"
    echo "apt install -y nodejs"
    exit 1
fi

# Systemd
if ! command -v systemctl &> /dev/null; then
    echo -e "${RED}✗ systemd non disponible${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Tous les prérequis sont ok${NC}"

# ════════════════════════════════════════════════
# DÉPLOIEMENT
# ════════════════════════════════════════════════

echo -e "${YELLOW}📁 Préparation du répertoire de déploiement...${NC}"

# Crée le répertoire
sudo mkdir -p "$DEPLOY_DIR"
sudo chown "$USER:$USER" "$DEPLOY_DIR"

# Copie les fichiers
cp -r ./* "$DEPLOY_DIR/"

cd "$DEPLOY_DIR"

# Python venv
echo -e "${YELLOW}🐍 Configuration Python...${NC}"
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Node modules
echo -e "${YELLOW}📦 Installation npm...${NC}"
npm install
npm run build:linux

# ════════════════════════════════════════════════
# SYSTEMD SERVICE
# ════════════════════════════════════════════════

echo -e "${YELLOW}⚙️  Configuration du service systemd...${NC}"

sudo tee "/etc/systemd/system/${SERVICE_NAME}.service" > /dev/null << EOF
[Unit]
Description=Likoo Application Server
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$DEPLOY_DIR
Environment="PATH=$DEPLOY_DIR/venv/bin"
ExecStart=$DEPLOY_DIR/venv/bin/python server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"
sudo systemctl start "$SERVICE_NAME"

# ════════════════════════════════════════════════
# NGINX REVERSE PROXY
# ════════════════════════════════════════════════

echo -e "${YELLOW}🌐 Configuration Nginx...${NC}"

if command -v nginx &> /dev/null; then
    sudo tee "/etc/nginx/sites-available/likoo" > /dev/null << EOF
server {
    listen 80;
    server_name $DOMAIN;

    location / {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /socket.io {
        proxy_pass http://localhost:5000/socket.io;
        proxy_http_version 1.1;
        proxy_buffering off;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
}
EOF

    sudo ln -sf /etc/nginx/sites-available/likoo /etc/nginx/sites-enabled/likoo
    sudo rm -f /etc/nginx/sites-enabled/default
    sudo nginx -t && sudo systemctl reload nginx
fi

# ════════════════════════════════════════════════
# HTTPS (OPTIONAL)
# ════════════════════════════════════════════════

if command -v certbot &> /dev/null; then
    echo -e "${YELLOW}🔒 Configuration HTTPS...${NC}"
    sudo certbot --nginx -d "$DOMAIN"
fi

# ════════════════════════════════════════════════
# RÉSUMÉ
# ════════════════════════════════════════════════

echo ""
echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✅ DEPLOYMENT TERMINÉ!               ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"

echo -e "${YELLOW}📍 Informations:${NC}"
echo "   Répertoire: $DEPLOY_DIR"
echo "   Service: $SERVICE_NAME"
echo "   URL: http://$DOMAIN"
echo ""

echo -e "${YELLOW}🛠️  Commandes utiles:${NC}"
echo "   Status:   sudo systemctl status $SERVICE_NAME"
echo "   Logs:     sudo journalctl -u $SERVICE_NAME -f"
echo "   Restart:  sudo systemctl restart $SERVICE_NAME"
echo "   Stop:     sudo systemctl stop $SERVICE_NAME"
echo ""

echo -e "${GREEN}🚀 Likoo est en production!${NC}"
