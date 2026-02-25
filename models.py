"""
DATABASE MODELS — Likoo
Utilise SQLite avec SQLAlchemy
"""

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import uuid

db = SQLAlchemy()

# ═══════════════════════════════════════════════════
# MODÈLES DE DONNÉES
# ═══════════════════════════════════════════════════

class User(db.Model):
    """Modèle utilisateur"""
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    # avatar can be an emoji or a URL/relative path to an uploaded image/gif
    avatar = db.Column(db.String(255), default='👤')
    color = db.Column(db.String(7), default='#94a3b8')
    status = db.Column(db.String(20), default='offline')  # online, away, dnd, offline
    tag = db.Column(db.String(4), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    messages = db.relationship('Message', backref='author', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash et stocke le mot de passe"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Vérifie le mot de passe"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """Convertit en dictionnaire"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'avatar': self.avatar,
            'color': self.color,
            'status': self.status,
            'tag': self.tag,
            'created_at': self.created_at.isoformat()
        }


class Server(db.Model):
    """Modèle serveur"""
    __tablename__ = 'servers'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    icon = db.Column(db.String(10), default='🎪')
    icon_image = db.Column(db.String(255), default=None)  # URL vers image du serveur
    owner_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    description = db.Column(db.String(500), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    owner = db.relationship('User', backref='owned_servers')
    channels = db.relationship('Channel', backref='server', lazy=True, cascade='all, delete-orphan')
    roles = db.relationship('Role', backref='server', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'icon': self.icon,
            'icon_image': self.icon_image,
            'owner_id': self.owner_id,
            'description': self.description,
            'channels': [ch.to_dict() for ch in self.channels],
            'roles': [r.to_dict() for r in self.roles],
            'members': [m.to_dict() for m in self.memberships],
            'created_at': self.created_at.isoformat()
        }


class Channel(db.Model):
    """Modèle canal"""
    __tablename__ = 'channels'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    server_id = db.Column(db.String(36), db.ForeignKey('servers.id'), nullable=False)
    type = db.Column(db.String(10), default='text')  # text, voice
    description = db.Column(db.String(500), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    messages = db.relationship('Message', backref='channel', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'server_id': self.server_id,
            'type': self.type,
            'description': self.description,
            'created_at': self.created_at.isoformat()
        }


class Role(db.Model):
    """Modèle rôle serveur"""
    __tablename__ = 'roles'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(50), nullable=False)
    server_id = db.Column(db.String(36), db.ForeignKey('servers.id'), nullable=False)
    color = db.Column(db.String(7), default='#94a3b8')  # Couleur du rôle
    permissions = db.Column(db.JSON, default={
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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'server_id': self.server_id,
            'color': self.color,
            'permissions': self.permissions,
            'created_at': self.created_at.isoformat()
        }


class ServerMember(db.Model):
    """Assocation user-server avec rôle"""
    __tablename__ = 'server_members'
    
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), primary_key=True)
    server_id = db.Column(db.String(36), db.ForeignKey('servers.id'), primary_key=True)
    role_id = db.Column(db.String(36), db.ForeignKey('roles.id'), nullable=True)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='server_memberships')
    server = db.relationship('Server', backref='memberships')
    
    def to_dict(self):
        return {
            'user_id': self.user_id,
            'username': self.user.username,
            'avatar': self.user.avatar,
            'status': self.user.status,
            'role_id': self.role_id,
            'joined_at': self.joined_at.isoformat()
        }
    role = db.relationship('Role', backref='members')


class Message(db.Model):
    """Modèle message"""
    __tablename__ = 'messages'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    channel_id = db.Column(db.String(36), db.ForeignKey('channels.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    edited_at = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'id': self.id,
            'content': self.content,
            'author': self.author.to_dict(),
            'channel_id': self.channel_id,
            'created_at': self.created_at.isoformat(),
            'edited_at': self.edited_at.isoformat() if self.edited_at else None
        }


class DirectMessage(db.Model):
    """Message privé entre deux utilisateurs"""
    __tablename__ = 'direct_messages'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sender_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    receiver_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    sender = db.relationship('User', foreign_keys=[sender_id])

    def to_dict(self):
        return {
            'id': self.id,
            'content': self.content,
            'sender_id': self.sender_id,
            'receiver_id': self.receiver_id,
            'author': self.sender.to_dict(),
            'created_at': self.created_at.isoformat()
        }


class FriendRequest(db.Model):
    """Demande d'ami entre deux utilisateurs"""
    __tablename__ = 'friend_requests'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sender_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    receiver_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(10), default='pending')  # pending, accepted, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_requests')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_requests')

    def to_dict(self):
        return {
            'id': self.id,
            'sender': self.sender.to_dict(),
            'receiver': self.receiver.to_dict(),
            'status': self.status,
            'created_at': self.created_at.isoformat()
        }


class ServerInvite(db.Model):
    """Code d'invitation pour rejoindre un serveur"""
    __tablename__ = 'server_invites'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    code = db.Column(db.String(10), unique=True, nullable=False)  # Code unique court (ex: ABC123)
    server_id = db.Column(db.String(36), db.ForeignKey('servers.id'), nullable=False)
    creator_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    uses = db.Column(db.Integer, default=0)  # Nombre d'utilisations
    max_uses = db.Column(db.Integer, default=None)  # None = illimite
    expires_at = db.Column(db.DateTime, default=None)  # None = jamais
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    server = db.relationship('Server', backref='invites')
    creator = db.relationship('User', backref='created_invites')
    
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'server_id': self.server_id,
            'creator_id': self.creator_id,
            'uses': self.uses,
            'max_uses': self.max_uses,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_at': self.created_at.isoformat()
        }
