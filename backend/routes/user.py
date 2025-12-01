import sys
import os

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from flask import Blueprint, request, jsonify
# ✅ Import db from extensions, not models
from extensions import db
from models import User, BackupCode, LoginHistory , VoiceTemplate
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import pyotp
import qrcode
from io import BytesIO
import base64
import json
from services.voice_recognition import (
    voice_service_v2,           # main singleton
    SecurityProfile,
)

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
    """Enroll user's face for biometric authentication with validation"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        print("\n" + "="*60)
        print("📸 [FACE ENROLL] Starting face enrollment")
        
        # Get current user from JWT
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            print("❌ [ERROR] User not found")
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
        
        print(f"📏 [SIZE] Image data: {len(face_image)} characters")
        
        # Import face service
        try:
            from services.face_recognition import face_service
        except ImportError:
            # Fallback import
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "face_recognition_service",
                os.path.join(backend_dir, "services", "face_recognition.py")
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            face_service = module.face_service
        
        # ✅ EXTRACT: Get face embedding from enrollment image
        print("🔍 [EXTRACT] Extracting face embedding for enrollment...")
        embedding, error, saved_path = face_service.extract_embedding(
            face_image,
            user_id=user.id,
            username=user.username,
            save_image=True  # Save enrollment image
        )
        
        if error:
            print(f"❌ [ERROR] {error}")
            return jsonify({'error': error}), 400
        
        if embedding is None:
            print("❌ [ERROR] No embedding extracted")
            return jsonify({'error': 'Could not extract face from image'}), 400
        
        # ✅ VALIDATE: Ensure embedding is valid
        if embedding.shape[0] != 128:
            print(f"❌ [ERROR] Invalid embedding shape: {embedding.shape}")
            return jsonify({'error': 'Invalid face embedding extracted'}), 500
        
        # ✅ SERIALIZE: Convert numpy array to JSON string for database
        print("💾 [SERIALIZE] Converting embedding to database format...")
        try:
            serialized_embedding = face_service.serialize_embedding(embedding)
        except Exception as e:
            print(f"❌ [ERROR] Serialization failed: {str(e)}")
            return jsonify({'error': 'Failed to process face data'}), 500
        
        # ✅ SAVE: Store in database
        print("💾 [SAVE] Saving to database...")
        user.face_encoding = serialized_embedding
        user.face_enrolled = True
        user.face_enrolled_at = datetime.utcnow()
        
        db.session.commit()
        
        print("✅ [SUCCESS] Face enrolled successfully")
        print(f"📊 [STATS] Embedding shape: {embedding.shape}")
        print(f"📁 [SAVED] Image: {saved_path}")
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

@user_bp.route("/enroll/voice", methods=["POST", "OPTIONS"])
@jwt_required()
def enroll_voice():
    """Enroll a user's voice. Expects JSON: { "voice_audio": "<base64 webm>" }"""
    if request.method == "OPTIONS":
        return "", 200

    try:
        current_user_id = get_jwt_identity()
        user: User = User.query.get(current_user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        data = request.get_json() or {}
        base64_audio = data.get("voice_audio")
        if not base64_audio:
            return jsonify({"error": "Missing 'voice_audio' field"}), 400

        print("\n" + "=" * 60)
        print("🎤 [VOICE ENROLL] Starting voice enrollment")
        print(f"👤 [USER] {user.username} (ID: {user.id})")
        print("📦 [FORMAT] JSON request")
        print(f"📏 [SIZE] Audio size: {len(base64_audio)} characters")

        # Extract features & optionally save raw audio
        feats, meta, saved_path = voice_service_v2.extract_features(
            base64_audio=base64_audio,
            user_id=str(user.id),
            username=user.username,
            save_audio=True,
            profile=SecurityProfile.BALANCED,
        )

        # Serialize features for DB
        features_str = voice_service_v2.serialize_features(feats)

        # Upsert voice template row
        template = VoiceTemplate.query.filter_by(user_id=user.id).first()
        if template is None:
            template = VoiceTemplate(user_id=user.id)

        template.features = features_str
        template.meta_json = json.dumps(meta)
        template.audio_path = saved_path
        db.session.add(template)

        # ✅ ALSO update flags on User so UI and login can see it
        user.voice_enrolled = True
        user.voice_embedding = features_str  # keep in User for backward compatibility
        user.updated_at = datetime.utcnow()

        db.session.commit()

        print("✅ [VOICE ENROLL] Voice enrolled successfully")
        print(f"📊 [QUALITY] {meta.get('quality_score')}, duration={meta.get('duration_sec')}s")
        print("=" * 60 + "\n")

        return jsonify(
            {
                "message": "Voice enrolled successfully",
                "quality_score": meta.get("quality_score"),
                "duration_sec": meta.get("duration_sec"),
                "user": user.to_dict(),
            }
        ), 200

    except ValueError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        db.session.rollback()
        print("Voice enroll error:", e)
        return jsonify({"error": "Internal server error"}), 500

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

@user_bp.route('/otp/generate', methods=['GET'])
@jwt_required()
def generate_otp_qr():
    """Generate TOTP secret and QR code for the logged-in user."""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        # Create a new secret if user does not have one yet
        if not getattr(user, "otp_secret", None):
            user.otp_secret = pyotp.random_base32()
            db.session.commit()

        secret = user.otp_secret

        # Build TOTP provisioning URI
        totp = pyotp.TOTP(secret)
        uri = totp.provisioning_uri(
            name=user.email or user.username,
            issuer_name="MFA Authentication System"
        )

        # Generate QR as PNG in memory
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(uri)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        buffer = BytesIO()
        img.save(buffer, format="PNG")
        img_bytes = buffer.getvalue()
        img_b64 = base64.b64encode(img_bytes).decode("utf-8")
        data_url = f"data:image/png;base64,{img_b64}"

        return jsonify({
            "qr_code": data_url,
            "secret": secret
        }), 200

    except Exception as e:
        print("Error generating OTP QR:", e)
        return jsonify({"error": "Failed to generate QR code"}), 500

# ===========================
# GESTURE RECOGNITION
# ===========================
@user_bp.route('/enroll/gesture', methods=['POST', 'OPTIONS'])
@jwt_required()
def enroll_gesture():
    """Enroll gesture pattern with STRICT/BALANCED verification."""
    if request.method == 'OPTIONS':
        return '', 200

    try:
        print("\n" + "=" * 60)
        print("✋ [GESTURE ENROLL] Starting gesture enrollment")

        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        print(f"👤 [USER] {user.username} (ID: {user.id})")

        if not request.is_json:
            print("❌ [ERROR] Request content type is not JSON")
            return jsonify({'error': 'Request must be JSON'}), 400

        data = request.get_json(silent=True) or {}
        print(f"🧾 [RAW DATA] {data}")

        # Frontend now sends { "points": [...] }
        points = data.get('points')
        if not points or not isinstance(points, list):
            print("❌ [ERROR] Gesture points are missing or invalid")
            return jsonify({'error': 'Gesture points are required'}), 400

        gesture_data = {'points': points}

        total_points = len(points)
        print(f"📊 [POINTS] {total_points} points in gesture")

        # Import gesture service
        try:
            from services.gesture_recognition import gesture_service
        except ImportError:
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "gesture_recognition_service",
                os.path.join(backend_dir, "services", "gesture_recognition.py"),
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            gesture_service = module.gesture_service

        # Extract features
        print("🔍 [EXTRACT] Extracting gesture features...")
        features, error, saved_path = gesture_service.extract_features(
            gesture_data,
            user_id=user.id,
            username=user.username,
            save_pattern=True,
        )

        if error:
            print(f"❌ [ERROR] {error}")
            return jsonify({'error': error}), 400

        # Serialize and store
        print("💾 [SAVE] Saving features to database...")
        user.gesture_features = gesture_service.serialize_features(features)
        user.gesture_enrolled = True
        user.gesture_enrolled_at = datetime.utcnow()

        db.session.commit()

        print("✅ [SUCCESS] Gesture enrolled successfully")
        print("=" * 60 + "\n")

        return jsonify({
            'message': 'Gesture enrolled successfully',
            'user': user.to_dict(),
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"❌ [ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        print("=" * 60 + "\n")
        return jsonify({'error': 'Internal server error'}), 500



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
    """Get user's login history"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        user_id = get_jwt_identity()
        limit = request.args.get('limit', 50, type=int)
        
        print(f"📊 [LOGIN HISTORY] Fetching history for user_id: {user_id}, limit: {limit}")
        
        # Get login history from database
        history = LoginHistory.query.filter_by(user_id=user_id)\
            .order_by(LoginHistory.login_time.desc())\
            .limit(limit)\
            .all()
        
        history_list = [record.to_dict() for record in history]
        
        print(f"✅ [LOGIN HISTORY] Found {len(history_list)} records")
        
        return jsonify({
            'history': history_list,
            'total': len(history_list)
        }), 200
        
    except Exception as e:
        print(f"❌ [LOGIN HISTORY] Error: {str(e)}") 
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e), 'history': []}), 500


# ===========================
# UNENROLL
# ===========================

@user_bp.route('/unenroll/<method>', methods=['DELETE', 'OPTIONS'])
@jwt_required()
def unenroll_method(method):
    """Remove an enrolled authentication method"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Map method names to database fields
        method_mapping = {
            'face': 'face_enrolled',
            'voice': 'voice_enrolled',
            'gesture': 'gesture_enrolled',
            'keystroke': 'keystroke_enrolled',
            'totp': 'otp_enrolled'
        }
        
        if method not in method_mapping:
            return jsonify({'error': 'Invalid method'}), 400
        
        field_name = method_mapping[method]
        
        # Check if method is enrolled
        if not getattr(user, field_name, False):
            return jsonify({'error': 'Method not enrolled'}), 400
        
        # Unenroll the method
        setattr(user, field_name, False)
        
        # Also clear the related data
        if method == 'face':
            user.face_encoding = None
            user.face_image_path = None
            user.face_enrolled_at = None
        elif method == 'voice':
            user.voice_embedding = None
            VoiceTemplate.query.filter_by(user_id=user.id).delete()
        elif method == 'gesture':
            user.gesture_features = None
            user.gesture_enrolled_at = None
        elif method == 'keystroke':
            user.keystroke_features = None
            user.keystroke_passphrase = None
            user.keystroke_enrolled_at = None
        elif method == 'totp':
            user.otp_secret = None
        
        db.session.commit()
        
        print(f"✅ [UNENROLL] User {user.username} unenrolled from {method}")
        
        return jsonify({
            'message': f'{method.capitalize()} authentication removed successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ [UNENROLL] Error: {str(e)}")
        return jsonify({'error': str(e)}), 500