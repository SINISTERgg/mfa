from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import secrets

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True)
    
    # Basic Info
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(150))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Account Status
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    
    # Face Recognition
    face_enrolled = db.Column(db.Boolean, default=False)
    face_encoding = db.Column(db.Text)
    face_image_path = db.Column(db.String(255))
    
    # Voice Recognition
    voice_enrolled = db.Column(db.Boolean, default=False)
    voice_embedding = db.Column(db.Text)
    
    # OTP/TOTP
    otp_enrolled = db.Column(db.Boolean, default=False)
    otp_secret = db.Column(db.String(32))
    
    # Gesture Recognition
    gesture_enrolled = db.Column(db.Boolean, default=False)
    gesture_features = db.Column(db.Text, nullable=True)
    gesture_enrolled_at = db.Column(db.DateTime, nullable=True)
    
    # Keystroke Dynamics
    keystroke_enrolled = db.Column(db.Boolean, default=False)
    keystroke_enrolled_at = db.Column(db.DateTime, nullable=True)
    keystroke_passphrase = db.Column(db.String(255), nullable=True)
    keystroke_features = db.Column(db.Text, nullable=True)  # JSON string of ML features
    keystroke_last_updated = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    backup_codes = db.relationship('BackupCode', backref='user', lazy=True, cascade='all, delete-orphan')
    login_history = db.relationship('LoginHistory', backref='user', lazy=True, cascade='all, delete-orphan')
    
    # Methods
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'face_enrolled': self.face_enrolled,
            'voice_enrolled': self.voice_enrolled,
            'otp_enrolled': self.otp_enrolled,
            'gesture_enrolled': self.gesture_enrolled,
            'keystroke_enrolled': self.keystroke_enrolled,
        }


class BackupCode(db.Model):
    __tablename__ = 'backup_codes'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    code_hash = db.Column(db.String(255), nullable=False)
    is_used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    used_at = db.Column(db.DateTime, nullable=True)
    
    def set_code(self, code):
        self.code_hash = generate_password_hash(code)
    
    def check_code(self, code):
        return check_password_hash(self.code_hash, code)
    
    @staticmethod
    def generate_code():
        """Generate a random 8-character backup code"""
        return secrets.token_urlsafe(6)[:8].upper()


class LoginHistory(db.Model):
    __tablename__ = 'login_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    login_time = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(255))
    device_fingerprint = db.Column(db.String(255))
    mfa_method = db.Column(db.String(50))
    success = db.Column(db.Boolean, default=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'login_time': self.login_time.isoformat() if self.login_time else None,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'mfa_method': self.mfa_method,
            'success': self.success
        }
