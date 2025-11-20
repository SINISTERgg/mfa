import jwt
import datetime


def create_access_token(user_id):
    """Create access token"""
    try:
        payload = {
            'user_id': user_id,
            'type': 'access',
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24),
            'iat': datetime.datetime.utcnow()
        }
        token = jwt.encode(payload, 'your-secret-key-change-this', algorithm='HS256')
        # Handle both string and bytes
        return token if isinstance(token, str) else token.decode('utf-8')
    except Exception as e:
        print(f"Token creation error: {e}")
        return None


def create_refresh_token(user_id):
    """Create refresh token"""
    try:
        payload = {
            'user_id': user_id,
            'type': 'refresh',
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=30),
            'iat': datetime.datetime.utcnow()
        }
        token = jwt.encode(payload, 'your-secret-key-change-this', algorithm='HS256')
        return token if isinstance(token, str) else token.decode('utf-8')
    except Exception as e:
        print(f"Token creation error: {e}")
        return None


def decode_token(token):
    """Decode JWT token"""
    try:
        payload = jwt.decode(token, 'your-secret-key-change-this', algorithms=['HS256'])
        return payload, None
    except jwt.ExpiredSignatureError:
        return None, 'Token expired'
    except jwt.InvalidTokenError as e:
        return None, f'Invalid token: {str(e)}'
    except Exception as e:
        return None, f'Token error: {str(e)}'


def create_mfa_pending_token(user_id, device_fingerprint):
    """Create MFA pending token"""
    try:
        payload = {
            'user_id': user_id,
            'device_fingerprint': device_fingerprint,
            'type': 'mfa_pending',
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=10),
            'iat': datetime.datetime.utcnow()
        }
        token = jwt.encode(payload, 'your-secret-key-change-this', algorithm='HS256')
        return token if isinstance(token, str) else token.decode('utf-8')
    except Exception as e:
        print(f"Token creation error: {e}")
        return None
