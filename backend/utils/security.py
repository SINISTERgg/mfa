import bcrypt
import secrets
import hashlib
from cryptography.fernet import Fernet
import base64
import os


def hash_password(password):
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(password, hashed):
    """Verify a password against its hash"""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except Exception:
        return False


def generate_token(length=32):
    """Generate a secure random token"""
    return secrets.token_urlsafe(length)


def verify_token(token, expected_token):
    """Safely compare two tokens"""
    return secrets.compare_digest(token, expected_token)


def hash_fingerprint(fingerprint_data):
    """Hash device fingerprint for storage"""
    return hashlib.sha256(fingerprint_data.encode('utf-8')).hexdigest()


def generate_backup_code():
    """Generate a human-readable backup code"""
    # Format: XXXX-XXXX
    part1 = secrets.token_hex(2).upper()
    part2 = secrets.token_hex(2).upper()
    return f"{part1}-{part2}"


class DataEncryption:
    """Encrypt and decrypt sensitive data"""
    
    def __init__(self, key=None):
        if key is None:
            key = os.getenv('ENCRYPTION_KEY')
            if key is None:
                # Generate a key if none exists (for development)
                key = Fernet.generate_key().decode()
        
        if isinstance(key, str):
            key = key.encode()
        
        self.cipher = Fernet(key)
    
    def encrypt(self, data):
        """Encrypt data"""
        if isinstance(data, str):
            data = data.encode()
        return self.cipher.encrypt(data)
    
    def decrypt(self, encrypted_data):
        """Decrypt data"""
        return self.cipher.decrypt(encrypted_data).decode()


def sanitize_filename(filename):
    """Sanitize filename to prevent directory traversal"""
    import re
    # Remove any non-alphanumeric characters except dots, dashes, and underscores
    filename = re.sub(r'[^\w\-.]', '_', filename)
    # Remove any leading dots
    filename = filename.lstrip('.')
    return filename


def generate_otp_secret():
    """Generate a base32 secret for OTP"""
    return base64.b32encode(os.urandom(10)).decode('utf-8')
