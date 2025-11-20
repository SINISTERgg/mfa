import os
from flask import Flask, jsonify
from flask_cors import CORS
from models import db
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager

# Initialize extensions
migrate = Migrate()
jwt = JWTManager()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mfa_auth.db'  # ✅ Fixed path
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = 'stored_faces'
    app.config['BACKUP_CODES_COUNT'] = 10
    
    # JWT Configuration
    app.config['JWT_SECRET_KEY'] = 'jwt-secret-key-change-in-production'
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 3600
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = 2592000
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    
    # Enable CORS
    CORS(app, resources={
        r"/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    @app.after_request
    def after_request(response):
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        return response
    
    # Create database tables
    with app.app_context():
        db.create_all()
        print("✅ Database tables created successfully")
    
    # Register blueprints
    from routes.auth import auth_bp
    from routes.user import user_bp
    from routes.device import device_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(user_bp, url_prefix='/api/user')
    app.register_blueprint(device_bp, url_prefix='/api/device')
    
    # Health check routes
    @app.route('/')
    def index():
        return jsonify({
            'message': 'MFA Authentication System API',
            'version': '2.0.0',
            'status': 'running',
            'features': [
                'Face Recognition',
                'Voice Recognition',
                'OTP/TOTP',
                'Backup Codes',
                'Gesture Recognition',
                'Keystroke Dynamics'
            ]
        }), 200
    
    @app.route('/health')
    def health():
        return jsonify({'status': 'healthy'}), 200
    
    @app.route('/routes')
    def list_routes():
        routes = []
        for rule in app.url_map.iter_rules():
            if rule.endpoint != 'static':
                routes.append({
                    'endpoint': rule.endpoint,
                    'methods': sorted(list(rule.methods - {'HEAD', 'OPTIONS'})),
                    'path': str(rule)
                })
        return jsonify({'routes': sorted(routes, key=lambda x: x['path'])}), 200
    
    return app

if __name__ == '__main__':
    app = create_app()
    print("\n" + "="*70)
    print("🚀 MFA Authentication System v2.0")
    print("="*70)
    print("✅ Server:     http://127.0.0.1:5000")
    print("✅ Health:     http://127.0.0.1:5000/health")
    print("✅ Routes:     http://127.0.0.1:5000/routes")
    print("\n📋 Features:")
    print("   • Face Recognition")
    print("   • Voice Recognition")
    print("   • OTP/TOTP")
    print("   • Backup Codes")
    print("   • Gesture Recognition")
    print("   • Keystroke Dynamics")
    print("="*70 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
