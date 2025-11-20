from functools import wraps
from flask import request, jsonify
from utils.jwt_handler import decode_token


def token_required(f):
    """Middleware to protect routes with JWT authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get token from header
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({'error': 'Authorization header is missing'}), 401
        
        parts = auth_header.split()
        
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return jsonify({'error': 'Invalid authorization header format'}), 401
        
        token = parts[1]
        
        # Decode and verify token
        payload, error = decode_token(token)
        
        if error:
            return jsonify({'error': error}), 401
        
        # Check token type
        if payload.get('type') != 'access':
            return jsonify({'error': 'Invalid token type'}), 401
        
        # Attach user_id to request
        request.user_id = payload['user_id']
        
        return f(*args, **kwargs)
    
    return decorated_function
