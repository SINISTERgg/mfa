from extensions import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import secrets


class User(db.Model):
    __tablename__ = 'users'

    # Primary Key
    id = db.Column(db.Integer, primary_key=True)
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
    face_enrolled_at = db.Column(db.DateTime, nullable=True)

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
    keystroke_features = db.Column(db.Text, nullable=True)
    keystroke_last_updated = db.Column(db.DateTime, nullable=True)

    # Relationships
    backup_codes = db.relationship('BackupCode', backref='user', lazy=True, cascade='all, delete-orphan')
    login_history = db.relationship('LoginHistory', backref='user', lazy=True, cascade='all, delete-orphan')

    # Methods
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
        print(f"🔑 [PASSWORD] Set for user: {self.username}")

    def check_password(self, password):
        """Check if password is correct"""
        result = check_password_hash(self.password_hash, password)
        print(f"🔍 [PASSWORD CHECK] User: {self.username}, Result: {result}")
        return result

    def generate_backup_codes(self, count=10):
        """Generate backup codes for the user"""
        codes = []
        for _ in range(count):
            code = BackupCode.generate_code()
            codes.append(code)
            backup_code = BackupCode(user_id=self.id)
            backup_code.set_code(code)
            db.session.add(backup_code)
        return codes

    def to_dict(self):
        """Convert user to dictionary"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'face_enrolled': self.face_enrolled,
            'voice_enrolled': self.voice_enrolled,
            'gesture_enrolled': self.gesture_enrolled,
            'keystroke_enrolled': self.keystroke_enrolled,
            'otp_enrolled': self.otp_enrolled,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
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
    """Model to track login attempts - FIXED VERSION"""
    __tablename__ = 'login_history'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    login_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    ip_address = db.Column(db.String(45))  # IPv6 support
    user_agent = db.Column(db.String(500))
    success = db.Column(db.Boolean, default=True, nullable=False)
    method_type = db.Column(db.String(50))  # password, face, voice, gesture, keystroke, totp, backup
    confidence = db.Column(db.Float)  # For biometric methods
    failure_reason = db.Column(db.String(200))

    def to_dict(self):
        """Convert to dictionary for API response"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'login_time': self.login_time.isoformat() if self.login_time else None,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'success': self.success,
            'method_type': self.method_type,
            'confidence': self.confidence,
            'failure_reason': self.failure_reason,
        }


class VoiceTemplate(db.Model):
    __tablename__ = 'voice_templates'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id'),
        nullable=False,
        unique=True,  # one template per user
    )

    # Serialized feature vector from voice_recognition.py
    features = db.Column(db.Text, nullable=False)

    # JSON string with meta info: duration, quality, etc.
    meta_json = db.Column(db.Text, nullable=True)

    # Optional path to stored raw audio file
    audio_path = db.Column(db.String(512), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    user = db.relationship(
        'User',
        backref=db.backref('voice_template', uselist=False, cascade='all, delete-orphan'),
    )
