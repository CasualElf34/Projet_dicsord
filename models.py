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
    avatar = db.Column(db.String(10), default='👤')
    color = db.Column(db.String(7), default='#94a3b8')
    status = db.Column(db.String(20), default='offline')  # online, away, dnd, offline
    tag = db.Column(db.String(4), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    messages = db.relationship('Message', backref='author', lazy=True, cascade='all, delete-orphan')
    servers = db.relationship('Server', secondary='server_members', backref='members')
    
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
    owner_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    description = db.Column(db.String(500), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    owner = db.relationship('User', backref='owned_servers')
    channels = db.relationship('Channel', backref='server', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'icon': self.icon,
            'owner_id': self.owner_id,
            'description': self.description,
            'channels': [ch.to_dict() for ch in self.channels],
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


# Association table pour les serveurs et membres
server_members = db.Table('server_members',
    db.Column('user_id', db.String(36), db.ForeignKey('users.id'), primary_key=True),
    db.Column('server_id', db.String(36), db.ForeignKey('servers.id'), primary_key=True)
)
