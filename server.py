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

from models import db, User, Server, Channel, Message, FriendRequest, DirectMessage

# ═══════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════

BASE_DIR = Path(__file__).resolve().parent
# set template and static directories to project root so html/css/js are found
app = Flask(
    __name__,
    template_folder=str(BASE_DIR),
    static_folder=str(BASE_DIR),
    static_url_path=''
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
    db.session.commit()
    return jsonify(user.to_dict()), 200

# ═══════════════════════════════════════════════════
# SERVEURS - ROUTES
# ═══════════════════════════════════════════════════

@app.route('/api/servers', methods=['GET'])
@jwt_required()
def get_servers():
    """Récupère les serveurs de l'utilisateur"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    seen = set()
    result = []
    for srv in user.servers + user.owned_servers:
        if srv.id not in seen:
            seen.add(srv.id)
            result.append(srv)
    return jsonify([srv.to_dict() for srv in result]), 200

@app.route('/api/servers', methods=['POST'])
@jwt_required()
def create_server():
    """Crée un nouveau serveur"""
    user_id = get_jwt_identity()
    data = request.json
    
    server = Server(
        name=data.get('name', 'Nouveau Serveur'),
        icon=data.get('icon', '🎪'),
        owner_id=user_id,
        description=data.get('description', '')
    )
    
    db.session.add(server)
    db.session.commit()

    # Ajouter l'owner comme membre + créer un canal par défaut
    user = User.query.get(user_id)
    if user not in server.members:
        server.members.append(user)
    default_channel = Channel(
        name='général',
        server_id=server.id,
        type='text',
        description='Salon principal'
    )
    db.session.add(default_channel)
    db.session.commit()

    return jsonify(server.to_dict()), 201

@app.route('/api/servers/<server_id>', methods=['GET'])
@jwt_required()
def get_server(server_id):
    """Récupère les détails d'un serveur"""
    server = Server.query.get(server_id)
    
    if not server:
        return jsonify({'error': 'Serveur non trouvé'}), 404
    
    return jsonify(server.to_dict()), 200

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
def handle_connect():
    """Connexion WebSocket"""
    print(f"🔗 Client connecté: {request.sid}")
    emit('connect_response', {'message': 'Connecté au serveur'})

@socketio.on('join_user_room')
def handle_join_user_room(data):
    """Rejoint la room personnelle pour recevoir les notifs (demandes d'ami, etc.)"""
    user_id = data.get('user_id')
    if user_id:
        join_room(f'user_{user_id}')

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
    if not sender_id or not receiver_id or not content:
        return
    sender = User.query.get(sender_id)
    receiver = User.query.get(receiver_id)
    if not sender or not receiver:
        return
    msg = DirectMessage(sender_id=sender_id, receiver_id=receiver_id, content=content)
    db.session.add(msg)
    db.session.commit()
    # Envoyer au destinataire (s'il est connecté)
    socketio.emit('new_dm', msg.to_dict(), room=f'user_{receiver_id}')
    # Confirmer à l'envoyeur
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
    
    socketio.run(app, host='0.0.0.0', port=port, debug=debug)
