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

from models import db, User, Server, Channel, Message

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
# @app.route('/api/auth/register', methods=['POST']) <-- duplicate removed

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
    user = User(
        username=data['username'],
        email=data['email'],
        avatar=data.get('avatar', '👤'),
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

# ═══════════════════════════════════════════════════
# SERVEURS - ROUTES
# ═══════════════════════════════════════════════════

@app.route('/api/servers', methods=['GET'])
@jwt_required()
def get_servers():
    """Récupère les serveurs de l'utilisateur"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    servers = user.servers + user.owned_servers
    return jsonify([srv.to_dict() for srv in servers]), 200

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
# WEBSOCKET - CHAT TEMPS RÉEL
# ═══════════════════════════════════════════════════

@socketio.on('connect')
def handle_connect():
    """Connexion WebSocket"""
    print(f"🔗 Client connecté: {request.sid}")
    emit('connect_response', {'message': 'Connecté au serveur'})

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
