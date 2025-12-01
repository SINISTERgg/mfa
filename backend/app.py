from flask import Flask
from flask_cors import CORS
from datetime import datetime
import os
from routes.auth import auth_bp
# Create Flask app
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///mfa_auth.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')

# ✅ Import extensions from extensions.py
from extensions import db, jwt

# ✅ Initialize extensions with app
db.init_app(app)
jwt.init_app(app)

# ✅ CORS Configuration
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000", "http://127.0.0.1:3000"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "expose_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True,
        "max_age": 3600
    }
})

# ✅ Import models AFTER db is initialized
with app.app_context():
    from models import User, BackupCode, LoginHistory
    
    try:
        db.create_all()
        print("✅ Database tables created successfully")
    except Exception as e:
        print(f"❌ Database error: {str(e)}")

# ✅ Import and register blueprints
from routes.auth import auth_bp
from routes.user import user_bp

app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(user_bp, url_prefix='/api/user')

# Health check endpoint
@app.route('/api/health', methods=['GET'])
def health_check():
    return {'status': 'ok', 'timestamp': datetime.utcnow().isoformat()}, 200

# Root endpoint
@app.route('/')
def index():
    return {
        'message': 'MFA Authentication API',
        'version': '1.0.0',
        'endpoints': {
            'auth': '/api/auth',
            'user': '/api/user',
            'health': '/api/health'
        }
    }, 200

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 Starting MFA Authentication Server")
    print("="*60)
    print(f"📍 Server: http://localhost:5000")
    print(f"📍 API Base: http://localhost:5000/api")
    print(f"📍 Frontend: http://localhost:3000")
    print("="*60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
