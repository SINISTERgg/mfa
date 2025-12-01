"""
Shared extensions for the Flask application.
This prevents circular imports and SQLAlchemy instance conflicts.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager

# Initialize extensions (but don't bind to app yet)
db = SQLAlchemy()
jwt = JWTManager()
