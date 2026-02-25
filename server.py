"""
LIKOO SERVER v2 — Flask + SQLAlchemy + WebSocket + Auth
Serveur moderne avec base de données et chat temps réel
"""

from flask import Flask, render_template, jsonify, request, session
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from functools import wraps
import os
from pathlib import Path
import secrets
import string
import uuid
import json
from google.oauth2 import id_token
from google.auth.transport import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from models import db, User, Server, Channel, Message, FriendRequest, DirectMessage, ServerMember, Role

# ═══════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════

BASE_DIR = Path(__file__).resolve().parent
# set template and static directories to project root so html/css/js are found
app = Flask(
    __name__,
    template_folder=str(BASE_DIR),
    static_folder=str(BASE_DIR),
    static_url_path='',
    instance_path=str(BASE_DIR / 'instance')
)

# Config Database
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{BASE_DIR}/likoo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Config JWT
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET', 'dev-secret-key-change-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=30)

# Config Session
app.config['SECRET_KEY'] = secrets.token_hex(32)

# Initialisation
db.init_app(app)
jwt = JWTManager(app)
socketio = SocketIO(app, cors_allowed_origins="*")
CORS(app)

# ═══════════════════════════════════════════════════
# CONTEXT INITIALIZATION
# ═══════════════════════════════════════════════════

@app.before_request
def before_request():
    """Crée les tables si elles n'existent pas"""
    with app.app_context():
        db.create_all()

# ═══════════════════════════════════════════════════
# UTILITAIRES
# ═══════════════════════════════════════════════════

def generate_tag():
    """Génère un tag unique pour l'utilisateur (4 chiffres)"""
    import random
    return ''.join(random.choices(string.digits, k=4))

# ═══════════════════════════════════════════════════
# AUTHENTIFICATION - ROUTES
# ═══════════════════════════════════════════════════

# (before_request already defined above)
@app.route('/api/auth/register', methods=['POST'])
def register():
    """Crée un nouvel utilisateur"""
    data = request.json
    
    # Validation
    if not data.get('username') or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Champs manquants'}), 400
    
    # Vérifie si l'utilisateur existe
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Pseudo déjà utilisé'}), 409
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email déjà utilisé'}), 409
    
    # Crée l'utilisateur
    avatar_val = data.get('avatar', '👤')
    # if client sent a data URI for an image we should save it like upload_avatar
    if isinstance(avatar_val, str) and avatar_val.startswith('data:'):
        try:
            header, b64 = avatar_val.split(',', 1)
            import base64, re
            m = re.match(r'data:(image/[^;]+);base64', header)
            if m:
                mime = m.group(1)
                ext = mime.split('/')[-1]
                if ext == 'jpeg':
                    ext = 'jpg'
                filename = f"{uuid.uuid4()}.{ext}"
                avatars_dir = BASE_DIR / 'avatars'
                avatars_dir.mkdir(exist_ok=True)
                file_path = avatars_dir / filename
                with open(file_path, 'wb') as f:
                    f.write(base64.b64decode(b64))
                avatar_val = f"/avatars/{filename}"
        except Exception as ex:
            # if anything goes wrong we just fall back to default
            avatar_val = '👤'
    user = User(
        username=data['username'],
        email=data['email'],
        avatar=avatar_val,
        tag=generate_tag()
    )
    user.set_password(data['password'])
    
    db.session.add(user)
    db.session.commit()
    
    # Crée le JWT
    access_token = create_access_token(identity=user.id)
    
    return jsonify({
        'message': 'Utilisateur créé',
        'user': user.to_dict(),
        'access_token': access_token
    }), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Authentifie un utilisateur"""
    data = request.json
    
    if not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Pseudo et mot de passe requis'}), 400
    
    user = User.query.filter_by(username=data['username']).first()
    
    if not user or not user.check_password(data['password']):
        return jsonify({'error': 'Identifiants incorrects'}), 401
    
    # Update status
    user.status = 'online'
    db.session.commit()
    
    access_token = create_access_token(identity=user.id)
    
    return jsonify({
        'message': 'Connecté',
        'user': user.to_dict(),
        'access_token': access_token
    }), 200

# ─────────────────────────────────────────────
# GOOGLE OAUTH LOGIN
# ─────────────────────────────────────────────

@app.route('/api/auth/google', methods=['POST'])
def google_login():
    """Authentifie un utilisateur via Google OAuth"""
    try:
        data = request.json
        token = data.get('token')
        
        if not token:
            return jsonify({'error': 'Token Google manquant'}), 400
        
        GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
        idinfo = None
        
        # ──── Méthode 1: Vérifier avec verify_oauth2_token ────
        try:
            idinfo = id_token.verify_oauth2_token(token, requests.Request(), GOOGLE_CLIENT_ID)
        except Exception as e:
            pass
        
        # ──── Méthode 2: Appel HTTP à Google tokeninfo ────
        if not idinfo:
            try:
                import requests as req
                resp = req.get(f'https://www.googleapis.com/oauth2/v1/tokeninfo?access_token={token}', timeout=5)
                if resp.status_code == 200:
                    idinfo = resp.json()
            except:
                pass
        
        # ──── Méthode 3: Parser directement le JWT (mode dev) ────
        if not idinfo:
            try:
                import base64
                parts = token.split('.')
                if len(parts) == 3:
                    payload = parts[1]
                    payload += '=' * (4 - len(payload) % 4)
                    idinfo = json.loads(base64.urlsafe_b64decode(payload))
                else:
                    return jsonify({'error': 'Format de token invalide'}), 401
            except Exception as e:
                return jsonify({'error': f'Impossible de valider le token: {str(e)}'}), 401
        
        if not idinfo:
            return jsonify({'error': 'Token Google invalide'}), 401
        
        email = idinfo.get('email')
        name = idinfo.get('name', idinfo.get('email', 'User'))
        picture = idinfo.get('picture', '👤')
        
        if not email:
            return jsonify({'error': 'Email non trouvé dans le token Google'}), 400
        
        # Chercher ou créer l'utilisateur
        user = User.query.filter_by(email=email).first()
        
        if not user:
            # Créer un nouvel utilisateur
            username = name.replace(' ', '_').lower()
            # S'assurer que le username est unique
            base_username = username
            counter = 1
            while User.query.filter_by(username=username).first():
                username = f"{base_username}_{counter}"
                counter += 1
            
            user = User(
                username=username,
                email=email,
                avatar=picture if picture != '👤' else picture,
                tag=generate_tag()
            )
            # Les utilisateurs Google n'ont pas de mot de passe
            user.set_password(secrets.token_urlsafe(16))
            
            db.session.add(user)
            db.session.commit()
        
        # Update status
        user.status = 'online'
        db.session.commit()
        
        # Créer le JWT
        access_token = create_access_token(identity=user.id)
        
        return jsonify({
            'message': 'Connecté via Google',
            'user': user.to_dict(),
            'access_token': access_token
        }), 200
        
    except Exception as e:
        print(f"Erreur Google OAuth: {str(e)}")
        return jsonify({'error': f'Erreur d\'authentification Google: {str(e)}'}), 500

@app.route('/api/auth/me', methods=['GET'])
@jwt_required()
def get_me():
    """Récupère l'utilisateur actuel"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'Utilisateur non trouvé'}), 404
    
    return jsonify(user.to_dict()), 200


# ─────────────────────────────────────────────
# AVATAR UPLOAD
# ─────────────────────────────────────────────
@app.route('/api/auth/avatar', methods=['POST'])
@jwt_required()
def upload_avatar():
    """Permet à l'utilisateur connecté d'uploader une image/gif comme avatar."""
    if 'avatar' not in request.files:
        return jsonify({'error': "Aucun fichier envoyé"}), 400
    file = request.files['avatar']
    if file.filename == '':
        return jsonify({'error': "Nom de fichier vide"}), 400
    allowed = {'png','jpg','jpeg','gif','webp'}
    ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    if ext not in allowed:
        return jsonify({'error': 'Type de fichier non supporté'}), 400
    # sauvegarde dans un dossier avatars à la racine du projet
    avatars_dir = BASE_DIR / 'avatars'
    avatars_dir.mkdir(exist_ok=True)
    filename = f"{uuid.uuid4()}.{ext}"
    file_path = avatars_dir / filename
    file.save(str(file_path))
    user = User.query.get(get_jwt_identity())
    # on stocke le chemin relatif qui sera servi par Flask (static_url_path='')
    user.avatar = f"/avatars/{filename}"
    db.session.commit()
    
    # Notifier tous les serveurs où cet utilisateur est membre
    servers = db.session.query(Server).join(ServerMember).filter(ServerMember.user_id == user.id).all()
    for server in servers:
        socketio.emit('user_avatar_updated', {
            'user_id': user.id,
            'username': user.username,
            'avatar': user.avatar
        }, room=f'server_{server.id}')
    
    return jsonify({'avatar': user.avatar}), 200


# permet de modifier le profil (pseudo / avatar)
@app.route('/api/auth/me', methods=['PATCH'])
@jwt_required()
def update_me():
    user = User.query.get(get_jwt_identity())
    if not user:
        return jsonify({'error': 'Utilisateur non trouvé'}), 404
    data = request.json or {}
    if 'username' in data:
        user.username = data['username']
    if 'avatar' in data:
        user.avatar = data['avatar']
    if 'status' in data:
        user.status = data['status']
    db.session.commit()
    return jsonify(user.to_dict()), 200

# ═══════════════════════════════════════════════════
# SERVEURS - ROUTES
# ═══════════════════════════════════════════════════

@app.route('/api/servers', methods=['GET'])
@jwt_required()
def get_servers():
    """Récupère les serveurs de l'utilisateur"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'Utilisateur non trouvé'}), 404
        
        # Récupérer serveurs où l'utilisateur est propriétaire
        result = []
        seen = set()
        
        # Ajouter les serveurs possédés
        for srv in user.owned_servers:
            if srv.id not in seen:
                seen.add(srv.id)
                result.append(srv)
        
        # Ajouter les serveurs via les memberships
        for member in user.server_memberships:
            if member.server_id not in seen:
                seen.add(member.server_id)
                result.append(member.server_obj)
        
        return jsonify([srv.to_dict() for srv in result]), 200
    except Exception as e:
        print(f"Erreur get_servers: {str(e)}")
        return jsonify({'error': f'Erreur serveur: {str(e)}'}), 500

@app.route('/api/servers', methods=['POST'])
@jwt_required()
def create_server():
    """Crée un nouveau serveur"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'Utilisateur non authentifié'}), 401
        
        data = request.json or {}
        name = data.get('name', 'Nouveau Serveur').strip()
        icon = data.get('icon', '🎪').strip() or '🎪'
        
        if not name:
            return jsonify({'error': 'Le nom du serveur est obligatoire'}), 400
        
        server = Server(
            name=name,
            icon=icon,
            owner_id=user_id,
            description=data.get('description', '').strip()
        )
        
        db.session.add(server)
        db.session.flush()  # Get server.id without committing
        
        # Créer un channel par défaut
        default_channel = Channel(
            name='général',
            server_id=server.id,
            type='text',
            description='Salon principal'
        )
        db.session.add(default_channel)
        
        # Ajouter l'owner comme membre du serveur
        member = ServerMember(user_id=user_id, server_id=server.id)
        db.session.add(member)
        
        db.session.commit()

        return jsonify(server.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        print(f"Erreur create_server: {str(e)}")
        return jsonify({'error': f'Erreur lors de la création: {str(e)}'}), 500

@app.route('/api/servers/<server_id>', methods=['GET'])
@jwt_required()
def get_server(server_id):
    """Récupère les détails d'un serveur"""
    try:
        server = Server.query.get(server_id)
        
        if not server:
            return jsonify({'error': 'Serveur non trouvé'}), 404
        
        return jsonify(server.to_dict()), 200
    except Exception as e:
        print(f"Erreur get_server: {str(e)}")
        return jsonify({'error': f'Erreur serveur: {str(e)}'}), 500

@app.route('/api/servers/<server_id>', methods=['PATCH'])
@jwt_required()
def update_server(server_id):
    """Met à jour les infos du serveur"""
    try:
        user_id = get_jwt_identity()
        server = Server.query.get(server_id)
        
        if not server:
            return jsonify({'error': 'Serveur non trouvé'}), 404
        
        # Vérifier que l'utilisateur est le propriétaire
        if server.owner_id != user_id:
            return jsonify({'error': 'Accès refusé'}), 403
        
        data = request.json or {}
        
        if 'name' in data:
            server.name = data['name']
        if 'description' in data:
            server.description = data['description']
        if 'icon' in data:
            server.icon = data['icon']
        
        db.session.commit()
        return jsonify(server.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        print(f"Erreur update_server: {str(e)}")
        return jsonify({'error': f'Erreur lors de la mise à jour: {str(e)}'}), 500

@app.route('/api/servers/<server_id>', methods=['DELETE'])
@jwt_required()
def delete_server(server_id):
    """Supprime un serveur et tous ses contenus"""
    try:
        user_id = get_jwt_identity()
        server = Server.query.get(server_id)
        
        if not server:
            return jsonify({'error': 'Serveur non trouvé'}), 404
        
        # Vérifier que l'utilisateur est le propriétaire
        if server.owner_id != user_id:
            return jsonify({'error': 'Accès refusé'}), 403
        
        # Supprimer les channels, rôles, membres, messages
        Channel.query.filter_by(server_id=server_id).delete()
        Role.query.filter_by(server_id=server_id).delete()
        ServerMember.query.filter_by(server_id=server_id).delete()
        
        # Supprimer le serveur
        db.session.delete(server)
        db.session.commit()
        
        return jsonify({'success': True}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Erreur delete_server: {str(e)}")
        return jsonify({'error': f'Erreur lors de la suppression: {str(e)}'}), 500

@app.route('/api/servers/<server_id>/upload-icon', methods=['POST'])
@jwt_required()
def upload_server_icon(server_id):
    """Upload une image comme icône de serveur"""
    user_id = get_jwt_identity()
    server = Server.query.get(server_id)
    
    if not server:
        return jsonify({'error': 'Serveur non trouvé'}), 404
    
    # Vérifier que l'utilisateur est le propriétaire
    if server.owner_id != user_id:
        return jsonify({'error': 'Accès refusé'}), 403
    
    if 'icon' not in request.files:
        return jsonify({'error': 'Aucun fichier envoyé'}), 400
    
    file = request.files['icon']
    if file.filename == '':
        return jsonify({'error': 'Nom de fichier vide'}), 400
    
    allowed = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    if ext not in allowed:
        return jsonify({'error': 'Type de fichier non supporté'}), 400
    
    # Sauvegarder l'image
    server_icons_dir = BASE_DIR / 'server_icons'
    server_icons_dir.mkdir(exist_ok=True)
    filename = f"{uuid.uuid4()}.{ext}"
    file_path = server_icons_dir / filename
    file.save(str(file_path))
    
    server.icon_image = f"/server_icons/{filename}"
    db.session.commit()
    
    # Émettre l'événement WebSocket pour notifier les autres clients
    socketio.emit('server_icon_updated', {
        'server_id': server_id,
        'icon_image': server.icon_image
    }, room=f'server_{server_id}')
    
    return jsonify({'icon_image': server.icon_image}), 200

# ═══════════════════════════════════════════════════
# RÔLES - ROUTES
# ═══════════════════════════════════════════════════

@app.route('/api/servers/<server_id>/roles', methods=['GET'])
@jwt_required()
def get_server_roles(server_id):
    """Récupère les rôles d'un serveur"""
    try:
        server = Server.query.get(server_id)
        if not server:
            return jsonify({'error': 'Serveur non trouvé'}), 404
        
        return jsonify([r.to_dict() for r in server.roles]), 200
    except Exception as e:
        print(f"Erreur get_server_roles: {str(e)}")
        return jsonify({'error': f'Erreur: {str(e)}'}), 500

@app.route('/api/servers/<server_id>/roles', methods=['POST'])
@jwt_required()
def create_role(server_id):
    """Crée un nouveau rôle"""
    try:
        user_id = get_jwt_identity()
        server = Server.query.get(server_id)
        
        if not server:
            return jsonify({'error': 'Serveur non trouvé'}), 404
        
        # Vérifier que l'utilisateur est propriétaire
        if server.owner_id != user_id:
            return jsonify({'error': 'Accès refusé'}), 403
        
        data = request.json or {}
        name = data.get('name', 'Nouveau Rôle').strip()
        
        if not name:
            return jsonify({'error': 'Le nom du rôle est obligatoire'}), 400
        
        role = Role(
            name=name,
            server_id=server_id,
            color=data.get('color', '#94a3b8'),
            permissions=data.get('permissions', {
                'manage_server': False,
                'manage_roles': False,
                'manage_channels': False,
                'manage_members': False,
                'send_messages': True,
                'send_files': True,
                'mention_everyone': False,
                'manage_messages': False,
                'mute_members': False
            })
        )
        
        db.session.add(role)
        db.session.commit()
        
        return jsonify(role.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        print(f"Erreur create_role: {str(e)}")
        return jsonify({'error': f'Erreur: {str(e)}'}), 500

@app.route('/api/servers/<server_id>/roles/<role_id>', methods=['PATCH'])
@jwt_required()
def update_role(server_id, role_id):
    """Modifie un rôle"""
    try:
        user_id = get_jwt_identity()
        server = Server.query.get(server_id)
        
        if not server:
            return jsonify({'error': 'Serveur non trouvé'}), 404
        
        if server.owner_id != user_id:
            return jsonify({'error': 'Accès refusé'}), 403
        
        role = Role.query.filter_by(id=role_id, server_id=server_id).first()
        if not role:
            return jsonify({'error': 'Rôle non trouvé'}), 404
        
        data = request.json or {}
        if 'name' in data:
            role.name = data['name'].strip()
        if 'color' in data:
            role.color = data['color']
        if 'permissions' in data:
            role.permissions = data['permissions']
        
        db.session.commit()
        return jsonify(role.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        print(f"Erreur update_role: {str(e)}")
        return jsonify({'error': f'Erreur: {str(e)}'}), 500

@app.route('/api/servers/<server_id>/roles/<role_id>', methods=['DELETE'])
@jwt_required()
def delete_role(server_id, role_id):
    """Supprime un rôle"""
    try:
        user_id = get_jwt_identity()
        server = Server.query.get(server_id)
        
        if not server:
            return jsonify({'error': 'Serveur non trouvé'}), 404
        
        if server.owner_id != user_id:
            return jsonify({'error': 'Accès refusé'}), 403
        
        role = Role.query.filter_by(id=role_id, server_id=server_id).first()
        if not role:
            return jsonify({'error': 'Rôle non trouvé'}), 404
        
        db.session.delete(role)
        db.session.commit()
        
        return jsonify({'message': 'Rôle supprimé'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Erreur delete_role: {str(e)}")
        return jsonify({'error': f'Erreur: {str(e)}'}), 500

# ═══════════════════════════════════════════════════
# CANAUX - ROUTES
# ═══════════════════════════════════════════════════

@app.route('/api/servers/<server_id>/channels', methods=['GET'])
@jwt_required()
def get_channels(server_id):
    """Récupère les canaux d'un serveur"""
    server = Server.query.get(server_id)
    
    if not server:
        return jsonify({'error': 'Serveur non trouvé'}), 404
    
    return jsonify([ch.to_dict() for ch in server.channels]), 200

@app.route('/api/servers/<server_id>/channels', methods=['POST'])
@jwt_required()
def create_channel(server_id):
    """Crée un canal"""
    user_id = get_jwt_identity()
    server = Server.query.get(server_id)
    
    if not server:
        return jsonify({'error': 'Serveur non trouvé'}), 404
    
    if server.owner_id != user_id:
        return jsonify({'error': 'Non autorisé'}), 403
    
    data = request.json
    channel = Channel(
        name=data.get('name', 'nouveau-canal'),
        server_id=server_id,
        type=data.get('type', 'text'),
        description=data.get('description', '')
    )
    
    db.session.add(channel)
    db.session.commit()
    
    return jsonify(channel.to_dict()), 201

@app.route('/api/servers/<server_id>/members', methods=['GET'])
@jwt_required()
def get_server_members(server_id):
    """Récupère les membres d'un serveur"""
    try:
        server = Server.query.get(server_id)
        
        if not server:
            return jsonify({'error': 'Serveur non trouvé'}), 404
        
        members = ServerMember.query.filter_by(server_id=server_id).all()
        
        result = []
        for m in members:
            result.append({
                'user_id': m.user_id,
                'username': m.user.username,
                'avatar': m.user.avatar,
                'role_id': m.role_id,
                'joined_at': m.joined_at.isoformat()
            })
        
        return jsonify(result), 200
    except Exception as e:
        print(f"Erreur get_server_members: {str(e)}")
        return jsonify({'error': f'Erreur: {str(e)}'}), 500

# ═══════════════════════════════════════════════════
# MESSAGES - ROUTES (historique)
# ═══════════════════════════════════════════════════

@app.route('/api/channels/<channel_id>/messages', methods=['GET'])
@jwt_required()
def get_messages(channel_id):
    """Récupère l'historique des messages"""
    channel = Channel.query.get(channel_id)
    
    if not channel:
        return jsonify({'error': 'Canal non trouvé'}), 404
    
    messages = Message.query.filter_by(channel_id=channel_id)\
        .order_by(Message.created_at.asc()).all()
    
    return jsonify([msg.to_dict() for msg in messages]), 200

# ═══════════════════════════════════════════════════
# AMIS - ROUTES
# ═══════════════════════════════════════════════════

@app.route('/api/friends/request', methods=['POST'])
@jwt_required()
def send_friend_request():
    """Envoie une demande d'ami par username#tag"""
    user_id = get_jwt_identity()
    data = request.json
    username = data.get('username', '').strip()
    tag = data.get('tag', '').strip()

    if not username or not tag:
        return jsonify({'error': 'Username et tag requis'}), 400

    target = User.query.filter_by(username=username, tag=tag).first()
    if not target:
        return jsonify({'error': f'Utilisateur {username}#{tag} introuvable'}), 404
    if target.id == user_id:
        return jsonify({'error': 'Impossible de s\'ajouter soi-même'}), 400

    # Vérifier si une demande existe déjà
    existing = FriendRequest.query.filter(
        ((FriendRequest.sender_id == user_id) & (FriendRequest.receiver_id == target.id)) |
        ((FriendRequest.sender_id == target.id) & (FriendRequest.receiver_id == user_id))
    ).first()
    if existing:
        if existing.status == 'accepted':
            return jsonify({'error': 'Vous êtes déjà amis'}), 400
        if existing.status == 'pending':
            return jsonify({'error': 'Demande déjà envoyée'}), 400
        # Si rejeté, on permet de réessayer
        existing.status = 'pending'
        existing.sender_id = user_id
        existing.receiver_id = target.id
        db.session.commit()
        # Notifier via socket
        socketio.emit('friend_request', existing.to_dict(), room=f'user_{target.id}')
        return jsonify(existing.to_dict()), 200

    fr = FriendRequest(sender_id=user_id, receiver_id=target.id)
    db.session.add(fr)
    db.session.commit()

    # Notifier le destinataire en temps réel
    socketio.emit('friend_request', fr.to_dict(), room=f'user_{target.id}')
    return jsonify(fr.to_dict()), 201


@app.route('/api/friends/requests', methods=['GET'])
@jwt_required()
def get_friend_requests():
    """Récupère les demandes d'ami en attente reçues"""
    user_id = get_jwt_identity()
    requests_list = FriendRequest.query.filter_by(receiver_id=user_id, status='pending').all()
    return jsonify([r.to_dict() for r in requests_list]), 200


@app.route('/api/friends/requests/<request_id>/accept', methods=['POST'])
@jwt_required()
def accept_friend_request(request_id):
    """Accepte une demande d'ami"""
    user_id = get_jwt_identity()
    fr = FriendRequest.query.get(request_id)
    if not fr or fr.receiver_id != user_id:
        return jsonify({'error': 'Demande introuvable'}), 404
    fr.status = 'accepted'
    db.session.commit()
    # Notifier l'envoyeur
    socketio.emit('friend_accepted', fr.to_dict(), room=f'user_{fr.sender_id}')
    return jsonify(fr.to_dict()), 200


@app.route('/api/friends/requests/<request_id>/reject', methods=['POST'])
@jwt_required()
def reject_friend_request(request_id):
    """Rejette une demande d'ami"""
    user_id = get_jwt_identity()
    fr = FriendRequest.query.get(request_id)
    if not fr or fr.receiver_id != user_id:
        return jsonify({'error': 'Demande introuvable'}), 404
    fr.status = 'rejected'
    db.session.commit()
    return jsonify({'message': 'Demande refusée'}), 200


@app.route('/api/friends', methods=['GET'])
@jwt_required()
def get_friends():
    """Récupère la liste d'amis"""
    user_id = get_jwt_identity()
    accepted = FriendRequest.query.filter(
        ((FriendRequest.sender_id == user_id) | (FriendRequest.receiver_id == user_id)),
        FriendRequest.status == 'accepted'
    ).all()
    friends = []
    for fr in accepted:
        friend = fr.receiver if fr.sender_id == user_id else fr.sender
        friends.append(friend.to_dict())
    return jsonify(friends), 200


# ═══════════════════════════════════════════════════
# MESSAGES PRIVÉS - ROUTES
# ═══════════════════════════════════════════════════

@app.route('/api/dm/<friend_id>', methods=['GET'])
@jwt_required()
def get_dm_history(friend_id):
    """Récupère l'historique des messages privés avec un ami"""
    user_id = get_jwt_identity()
    messages = DirectMessage.query.filter(
        ((DirectMessage.sender_id == user_id) & (DirectMessage.receiver_id == friend_id)) |
        ((DirectMessage.sender_id == friend_id) & (DirectMessage.receiver_id == user_id))
    ).order_by(DirectMessage.created_at.asc()).all()
    return jsonify([m.to_dict() for m in messages]), 200


# ═══════════════════════════════════════════════════
# WEBSOCKET - CHAT TEMPS RÉEL
# ═══════════════════════════════════════════════════

@socketio.on('connect')
def handle_connect(auth=None):
    """Connexion WebSocket"""
    print(f"🔗 Client connecté: {request.sid}")
    emit('connect_response', {'message': 'Connecté au serveur'})

@socketio.on('join_user_room')
def handle_join_user_room(data):
    """Rejoint la room personnelle pour recevoir les notifs (demandes d'ami, etc.)"""
    user_id = data.get('user_id')
    if user_id:
        room_name = f'user_{user_id}'
        join_room(room_name)
        print(f'✅ Utilisateur {user_id} rejoint room: {room_name}')

@socketio.on('join_server')
def handle_join_server(data):
    """Rejoint la room d'un serveur pour recevoir les mises à jour (icône, nom, etc.)"""
    server_id = data.get('server_id')
    if server_id:
        join_room(f'server_{server_id}')

@socketio.on('disconnect')
def handle_disconnect():
    """Déconnexion WebSocket"""
    print(f"❌ Client déconnecté: {request.sid}")

@socketio.on('join_channel')
def on_join_channel(data):
    """Rejoins un canal"""
    channel_id = data['channel_id']
    join_room(f'channel_{channel_id}')
    
    emit('status', {
        'message': 'Utilisateur connecté au canal'
    }, room=f'channel_{channel_id}')
    
    print(f"✅ Client {request.sid} a rejoint le canal {channel_id}")

@socketio.on('leave_channel')
def on_leave_channel(data):
    """Quitte un canal"""
    channel_id = data['channel_id']
    leave_room(f'channel_{channel_id}')
    
    emit('status', {
        'message': 'Utilisateur a quitté le canal'
    }, room=f'channel_{channel_id}')

@socketio.on('send_message')
def on_send_message(data):
    """Envoie un message temps réel"""
    channel_id = data['channel_id']
    content = data['content']
    user_id = data.get('user_id')
    
    if not user_id or not content or not channel_id:
        return
    
    user = User.query.get(user_id)
    channel = Channel.query.get(channel_id)
    
    if not user or not channel:
        return
    
    # Sauvegarde en DB
    message = Message(
        content=content,
        author_id=user_id,
        channel_id=channel_id
    )
    
    db.session.add(message)
    db.session.commit()
    
    # Broadcast à tous les clients du canal
    emit('new_message', message.to_dict(), room=f'channel_{channel_id}')

@socketio.on('send_dm')
def on_send_dm(data):
    """Envoie un message privé"""
    sender_id = data.get('sender_id')
    receiver_id = data.get('receiver_id')
    content = data.get('content', '').strip()
    print(f'📤 on_send_dm reçu: sender={sender_id}, receiver={receiver_id}, content={content[:50]}...')
    if not sender_id or not receiver_id or not content:
        print(f'❌ on_send_dm: données manquantes')
        return
    sender = User.query.get(sender_id)
    receiver = User.query.get(receiver_id)
    if not sender or not receiver:
        print(f'❌ on_send_dm: utilisateur non trouvé')
        return
    msg = DirectMessage(sender_id=sender_id, receiver_id=receiver_id, content=content)
    db.session.add(msg)
    db.session.commit()
    print(f'✅ DM sauvegardé: id={msg.id}')
    # Envoyer au destinataire (s'il est connecté)
    print(f'📨 Emission new_dm à room: user_{receiver_id}')
    socketio.emit('new_dm', msg.to_dict(), room=f'user_{receiver_id}')
    # Confirmer à l'envoyeur
    print(f'📨 Emission new_dm à room: user_{sender_id}')
    socketio.emit('new_dm', msg.to_dict(), room=f'user_{sender_id}')


@socketio.on('typing')
def on_typing(data):
    """Notifie que quelqu'un tape"""
    channel_id = data['channel_id']
    username = data.get('username', 'Anonyme')
    
    emit('user_typing', {
        'username': username
    }, room=f'channel_{channel_id}', skip_sid=request.sid)

@socketio.on('user_status_change')
def on_status_change(data):
    """Change le statut de l'utilisateur"""
    user_id = data['user_id']
    status = data['status']
    
    user = User.query.get(user_id)
    if user:
        user.status = status
        db.session.commit()
        
        # Broadcast à tous les clients
        socketio.emit('user_status_changed', {
            'user_id': user_id,
            'status': status
        }, broadcast=True)

# ═══════════════════════════════════════════════
# WEBRTC VOICE
# ═══════════════════════════════════════════════
@socketio.on('voice_channel_join')
def on_voice_join(data):
    """Utilisateur rejoint un canal vocal"""
    user_id = data.get('user_id')
    channel_id = data.get('channel_id')
    server_id = data.get('server_id')
    room = f"voice_{channel_id}"
    join_room(room)
    
    # Notifier les autres utilisateurs du canal
    socketio.emit('voice_user_joined', {
        'user_id': user_id,
        'channel_id': channel_id
    }, room=room, skip_sid=True)

@socketio.on('voice_channel_leave')
def on_voice_leave(data):
    """Utilisateur quitte un canal vocal"""
    user_id = data.get('user_id')
    channel_id = data.get('channel_id')
    room = f"voice_{channel_id}"
    leave_room(room)
    
    # Notifier les autres utilisateurs du canal
    socketio.emit('voice_user_left', {
        'user_id': user_id,
        'channel_id': channel_id
    }, room=room)

@socketio.on('webrtc_offer')
def on_webrtc_offer(data):
    """Transmettre une offre WebRTC"""
    target_user_id = data.get('target_user_id')
    sender_user_id = data.get('sender_user_id')
    channel_id = data.get('channel_id')
    offer = data.get('offer')
    
    socketio.emit('webrtc_offer', {
        'from': sender_user_id,
        'offer': offer,
        'channel_id': channel_id
    }, to=target_user_id)

@socketio.on('webrtc_answer')
def on_webrtc_answer(data):
    """Transmettre une réponse WebRTC"""
    target_user_id = data.get('target_user_id')
    sender_user_id = data.get('sender_user_id')
    channel_id = data.get('channel_id')
    answer = data.get('answer')
    
    socketio.emit('webrtc_answer', {
        'from': sender_user_id,
        'answer': answer,
        'channel_id': channel_id
    }, to=target_user_id)

@socketio.on('webrtc_ice_candidate')
def on_webrtc_ice(data):
    """Transmettre un candidat ICE"""
    target_user_id = data.get('target_user_id')
    sender_user_id = data.get('sender_user_id')
    channel_id = data.get('channel_id')
    candidate = data.get('candidate')
    
    socketio.emit('webrtc_ice_candidate', {
        'from': sender_user_id,
        'candidate': candidate,
        'channel_id': channel_id
    }, to=target_user_id)

@socketio.on('voice_mute_changed')
def on_voice_mute_changed(data):
    """Notifier les autres utilisateurs du changement de mute"""
    channel_id = data.get('channel_id')
    user_id = data.get('user_id')
    muted = data.get('muted')
    room = f"voice_{channel_id}"
    
    socketio.emit('voice_mute_changed', {
        'user_id': user_id,
        'channel_id': channel_id,
        'muted': muted
    }, room=room, skip_sid=True)

@socketio.on('voice_deafen_changed')
def on_voice_deafen_changed(data):
    """Notifier les autres utilisateurs du changement de deafen"""
    channel_id = data.get('channel_id')
    user_id = data.get('user_id')
    deafened = data.get('deafened')
    room = f"voice_{channel_id}"
    
    socketio.emit('voice_deafen_changed', {
        'user_id': user_id,
        'channel_id': channel_id,
        'deafened': deafened
    }, room=room, skip_sid=True)

@socketio.on('voice_streaming_started')
def on_voice_streaming_started(data):
    """Notifier les autres utilisateurs qu'on partage l'écran"""
    channel_id = data.get('channel_id')
    user_id = data.get('user_id')
    name = data.get('name', 'Utilisateur')
    room = f"voice_{channel_id}"
    
    print(f"📺 {name} commence le stream vocal sur {channel_id}")
    
    socketio.emit('voice_streaming_started', {
        'user_id': user_id,
        'channel_id': channel_id,
        'name': name
    }, room=room, skip_sid=True)

@socketio.on('voice_streaming_stopped')
def on_voice_streaming_stopped(data):
    """Notifier les autres utilisateurs qu'on arrête le partage d'écran"""
    channel_id = data.get('channel_id')
    user_id = data.get('user_id')
    name = data.get('name', 'Utilisateur')
    room = f"voice_{channel_id}"
    
    print(f"⛔ {name} arrête le stream vocal sur {channel_id}")
    
    socketio.emit('voice_streaming_stopped', {
        'user_id': user_id,
        'channel_id': channel_id,
        'name': name
    }, room=room, skip_sid=True)

# ═══════════════════════════════════════════════════
# ROUTES STATIQUES
# ═══════════════════════════════════════════════════

from flask import send_from_directory, send_file

@app.route('/')
def index():
    """Sert la page HTML principale – on renvoie maintenant la version mise à jour (likoo.html).
    L'ancien fichier index_source.html est conservé pour référence mais n'est plus utilisé.
    """
    return send_from_directory(str(BASE_DIR), 'likoo.html')

# Fallback for any other file requests (css/js/images) served from root
@app.route('/<path:filename>')
def serve_file(filename):
    path = BASE_DIR / filename
    if path.exists():
        return send_file(str(path))
    return ('', 404)

@app.route('/health', methods=['GET'])
def health():
    """Vérifie la santé du serveur"""
    return jsonify({
        'status': 'ok',
        'message': 'Serveur Likoo v2 actif',
        'database': 'SQLite',
        'features': ['WebSocket', 'Authentication', 'Database']
    }), 200

# ═══════════════════════════════════════════════════
# GESTION DES ERREURS
# ═══════════════════════════════════════════════════

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Non trouvé'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Erreur serveur'}), 500

# ═══════════════════════════════════════════════════
# LANCEMENT
# ═══════════════════════════════════════════════════

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'True').lower() == 'true'
    
    banner = f"""
    =============================================
     LIKOO SERVER v2 LAUNCHED
    =============================================
     URL: http://localhost:{port}
     Database: SQLite (likoo.db)
     Features: WebSocket, JWT, Auth
     Debug: {debug}
    =============================================
    """
    print(banner)
    
    socketio.run(app, host='0.0.0.0', port=port, debug=debug, allow_unsafe_werkzeug=True)
