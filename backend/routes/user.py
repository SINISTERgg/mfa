import sys
import os

# Add backend directory to Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from flask import Blueprint, request, jsonify
from models import User, BackupCode, LoginHistory, db
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import pyotp
import qrcode
from io import BytesIO
import base64

user_bp = Blueprint('user', __name__)

# ===========================
# USER PROFILE
# ===========================

@user_bp.route('/profile', methods=['GET', 'OPTIONS'])
@jwt_required()
def get_profile():
    """Get user profile"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({'user': user.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@user_bp.route('/profile', methods=['PUT', 'OPTIONS'])
@jwt_required()
def update_profile():
    """Update user profile"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        if data.get('full_name'):
            user.full_name = data['full_name']
        if data.get('email'):
            existing = User.query.filter_by(email=data['email']).first()
            if existing and existing.id != user.id:
                return jsonify({'error': 'Email already in use'}), 400
            user.email = data['email']
        
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ===========================
# FACE RECOGNITION
# ===========================

@user_bp.route('/enroll/face', methods=['POST', 'OPTIONS'])
@jwt_required()
def enroll_face():
    """Enroll user's face for biometric authentication"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        print("\n" + "="*60)
        print("📸 [FACE ENROLL] Starting face enrollment")
        
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        print(f"👤 [USER] {user.username} (ID: {user.id})")
        
        # Get face image from request
        face_image = None
        
        if request.is_json:
            data = request.get_json()
            face_image = data.get('face_image')
            print("📦 [FORMAT] JSON request")
        else:
            face_image = request.form.get('face_image')
            print("📦 [FORMAT] FormData request")
        
        if not face_image:
            print("❌ [ERROR] No face image provided")
            return jsonify({'error': 'Face image is required'}), 400
        
        print(f"📏 [SIZE] Image size: {len(face_image)} characters")
        
        # ✅ FIXED IMPORT - Import at function level with proper path
        try:
            from services.face_recognition import face_service
        except ImportError:
            # Fallback - try alternative import
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "face_recognition_service",
                os.path.join(backend_dir, "services", "face_recognition.py")
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            face_service = module.face_service
        
        # Extract face embedding
        print("🔍 [EXTRACT] Extracting face embedding...")
        embedding, error, saved_path = face_service.extract_embedding(
            face_image,
            user_id=user.id,
            username=user.username,
            save_image=True
        )
        
        if error:
            print(f"❌ [ERROR] {error}")
            return jsonify({'error': error}), 400
        
        # Serialize and store embedding
        print("💾 [SAVE] Saving embedding to database...")
        user.face_encoding = face_service.serialize_embedding(embedding)
        user.face_enrolled = True
        
        db.session.commit()
        
        print("✅ [SUCCESS] Face enrolled successfully")
        print("="*60 + "\n")
        
        return jsonify({
            'message': 'Face enrolled successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ [ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        print("="*60 + "\n")
        return jsonify({'error': str(e)}), 500

# ===========================
# VOICE RECOGNITION
# ===========================

@user_bp.route('/enroll/voice', methods=['POST', 'OPTIONS'])
@jwt_required()
def enroll_voice():
    """Enroll voice recognition"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        print("\n" + "="*60)
        print("🎤 [VOICE ENROLL] Starting voice enrollment")
        
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        print(f"👤 [USER] {user.username} (ID: {user.id})")
        
        # Get voice audio from request
        voice_audio = None
        
        if request.is_json:
            data = request.get_json()
            voice_audio = data.get('voice_audio')
            print("📦 [FORMAT] JSON request")
        else:
            voice_audio = request.form.get('voice_audio')
            print("📦 [FORMAT] FormData request")
        
        if not voice_audio:
            print("❌ [ERROR] No voice audio provided")
            return jsonify({'error': 'Voice audio is required'}), 400
        
        print(f"📏 [SIZE] Audio size: {len(voice_audio)} characters")
        
        # Import voice service with fallback
        try:
            from services.voice_recognition import voice_service
        except ImportError as ie:
            print(f"⚠️ [IMPORT WARNING] {str(ie)}")
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "voice_recognition_service",
                os.path.join(backend_dir, "services", "voice_recognition.py")
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            voice_service = module.voice_service
        
        # Extract voice features
        print("🔍 [EXTRACT] Extracting voice features...")
        features, error, saved_path = voice_service.extract_features(
            voice_audio,
            user_id=user.id,
            username=user.username,
            save_audio=True
        )
        
        if error:
            print(f"❌ [ERROR] {error}")
            return jsonify({'error': error}), 400
        
        # Serialize and store features
        print("💾 [SAVE] Saving features to database...")
        user.voice_embedding = voice_service.serialize_features(features)
        user.voice_enrolled = True
        
        db.session.commit()
        
        print("✅ [SUCCESS] Voice enrolled successfully")
        print("="*60 + "\n")
        
        return jsonify({
            'message': 'Voice enrolled successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ [ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        print("="*60 + "\n")
        return jsonify({'error': str(e)}), 500


# ===========================
# OTP/TOTP
# ===========================

@user_bp.route('/enroll/otp', methods=['POST', 'OPTIONS'])
@jwt_required()
def enroll_otp():
    """Enroll OTP/TOTP"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=user.email,
            issuer_name='MFA Auth System'
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        user.otp_secret = secret
        user.otp_enrolled = True
        db.session.commit()
        
        return jsonify({
            'message': 'OTP enrolled successfully',
            'secret': secret,
            'qr_code': f'data:image/png;base64,{qr_code_base64}',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ===========================
# GESTURE RECOGNITION
# ===========================

@user_bp.route('/enroll/gesture', methods=['POST', 'OPTIONS'])
@jwt_required()
def enroll_gesture():
    """Enroll gesture pattern"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        gesture_data = data.get('gesture')
        
        if not gesture_data:
            return jsonify({'error': 'Gesture data is required'}), 400
        
        import json
        user.gesture_features = json.dumps(gesture_data)
        user.gesture_enrolled = True
        user.gesture_enrolled_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Gesture enrolled successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ===========================
# KEYSTROKE DYNAMICS
# ===========================

@user_bp.route('/enroll/keystroke', methods=['POST', 'OPTIONS'])
@jwt_required()
def enroll_keystroke():
    """Enroll keystroke pattern"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        keystroke_samples = data.get('samples') or data.get('keystroke_samples')
        passphrase = data.get('passphrase')
        
        if not keystroke_samples or not passphrase:
            return jsonify({'error': 'Keystroke samples and passphrase required'}), 400
        
        if len(keystroke_samples) < 3:
            return jsonify({'error': f'At least 3 samples required'}), 400
        
        try:
            from services.keystroke_service import enroll_keystroke_pattern, analyze_pattern_strength
        except ImportError:
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "keystroke_service",
                os.path.join(backend_dir, "services", "keystroke_service.py")
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            enroll_keystroke_pattern = module.enroll_keystroke_pattern
            analyze_pattern_strength = module.analyze_pattern_strength
        
        strength_analysis = analyze_pattern_strength(keystroke_samples)
        
        if strength_analysis['score'] < 0.3:
            return jsonify({
                'error': 'Keystroke pattern too weak',
                'analysis': strength_analysis
            }), 400
        
        profile = enroll_keystroke_pattern(keystroke_samples)
        profile['passphrase'] = passphrase
        profile['strength_analysis'] = strength_analysis
        
        import json
        user.keystroke_features = json.dumps(profile)
        user.keystroke_passphrase = passphrase
        user.keystroke_enrolled = True
        user.keystroke_enrolled_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Keystroke pattern enrolled successfully',
            'user': user.to_dict(),
            'analysis': strength_analysis
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ===========================
# BACKUP CODES
# ===========================

@user_bp.route('/backup-codes', methods=['GET', 'OPTIONS'])
@jwt_required()
def get_backup_codes():
    """Get backup codes status"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        user_id = get_jwt_identity()
        total = BackupCode.query.filter_by(user_id=user_id).count()
        used = BackupCode.query.filter_by(user_id=user_id, is_used=True).count()
        
        return jsonify({
            'total': total,
            'used': used,
            'remaining': total - used
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@user_bp.route('/backup-codes/regenerate', methods=['POST', 'OPTIONS'])
@jwt_required()
def regenerate_backup_codes():
    """Regenerate backup codes"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        BackupCode.query.filter_by(user_id=user.id).delete()
        
        plain_codes = []
        for _ in range(10):
            code = BackupCode.generate_code()
            plain_codes.append(code)
            
            backup_code = BackupCode(user_id=user.id)
            backup_code.set_code(code)
            db.session.add(backup_code)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Backup codes regenerated',
            'backup_codes': plain_codes
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ===========================
# LOGIN HISTORY
# ===========================

@user_bp.route('/login-history', methods=['GET', 'OPTIONS'])
@jwt_required()
def get_login_history():
    """Get login history"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        user_id = get_jwt_identity()
        limit = request.args.get('limit', 10, type=int)
        
        history = LoginHistory.query.filter_by(user_id=user_id)\
            .order_by(LoginHistory.login_time.desc())\
            .limit(limit)\
            .all()
        
        return jsonify({
            'history': [h.to_dict() for h in history]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===========================
# UNENROLL
# ===========================

@user_bp.route('/unenroll/<method>', methods=['POST', 'OPTIONS'])
@jwt_required()
def unenroll_method(method):
    """Unenroll MFA method"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if method == 'face':
            user.face_enrolled = False
            user.face_encoding = None
        elif method == 'voice':
            user.voice_enrolled = False
            user.voice_embedding = None
        elif method == 'otp':
            user.otp_enrolled = False
            user.otp_secret = None
        elif method == 'gesture':
            user.gesture_enrolled = False
            user.gesture_features = None
        elif method == 'keystroke':
            user.keystroke_enrolled = False
            user.keystroke_features = None
        else:
            return jsonify({'error': 'Invalid method'}), 400
        
        db.session.commit()
        
        return jsonify({
            'message': f'{method.capitalize()} disabled',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
