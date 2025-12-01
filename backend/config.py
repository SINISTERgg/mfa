import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration"""
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///mfa_auth.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    
    # JWT
    # JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)  # ✅ Changed from 1 hour to 24 hours
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)  # 30 days

    # CORS
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(',')
    
    # Security
    BCRYPT_LOG_ROUNDS = int(os.getenv('BCRYPT_LOG_ROUNDS', 12))
    
    # Face Recognition
    FACE_RECOGNITION_MODEL = os.getenv('FACE_RECOGNITION_MODEL', 'VGG-Face')
    FACE_DETECTOR_BACKEND = os.getenv('FACE_DETECTOR_BACKEND', 'opencv')
    FACE_DISTANCE_METRIC = os.getenv('FACE_DISTANCE_METRIC', 'cosine')
    FACE_RECOGNITION_THRESHOLD = float(os.getenv('FACE_RECOGNITION_THRESHOLD', 0.6))
    
    # Voice Recognition
    VOICE_RECOGNITION_THRESHOLD = float(os.getenv('VOICE_RECOGNITION_THRESHOLD', 0.7))
    VOICE_SAMPLE_RATE = int(os.getenv('VOICE_SAMPLE_RATE', 16000))
    
    # OTP
    OTP_ISSUER_NAME = os.getenv('OTP_ISSUER_NAME', 'MFA Auth System')
    OTP_VALIDITY_WINDOW = int(os.getenv('OTP_VALIDITY_WINDOW', 2))
    
    # Device Fingerprint
    DEVICE_TRUST_DURATION = int(os.getenv('DEVICE_TRUST_DURATION', 2592000))  # 30 days
    
    # File Upload
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'stored_faces')
    ALLOWED_EXTENSIONS = set(os.getenv('ALLOWED_EXTENSIONS', 'jpg,jpeg,png').split(','))
    
    # Rate Limiting
    RATELIMIT_STORAGE_URL = os.getenv('RATELIMIT_STORAGE_URL', 'memory://')
    RATELIMIT_DEFAULT = os.getenv('RATELIMIT_DEFAULT', '100 per hour')
    
    # Backup Codes
    BACKUP_CODES_COUNT = int(os.getenv('BACKUP_CODES_COUNT', 10))


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_ECHO = True


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    SQLALCHEMY_ECHO = False


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///test_mfa_auth.db'
    BCRYPT_LOG_ROUNDS = 4  # Faster for tests


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
