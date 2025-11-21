from flask import Blueprint, request, jsonify
from models import User, BackupCode, LoginHistory, db
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import secrets
import jwt as pyjwt

auth_bp = Blueprint('auth', __name__)

# MFA Token Configuration
MFA_TOKEN_SECRET = 'mfa-secret-key-change-in-production'
MFA_TOKEN_EXPIRY = 300  # 5 minutes

def create_mfa_token(user_id):
    """Create a temporary MFA token with user_id encoded"""
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(seconds=MFA_TOKEN_EXPIRY),
        'iat': datetime.utcnow()
    }
    return pyjwt.encode(payload, MFA_TOKEN_SECRET, algorithm='HS256')

def decode_mfa_token(token):
    """Decode and verify MFA token, return user_id"""
    try:
        payload = pyjwt.decode(token, MFA_TOKEN_SECRET, algorithms=['HS256'])
        return payload['user_id']
    except pyjwt.ExpiredSignatureError:
        raise Exception('MFA token expired. Please login again.')
    except pyjwt.InvalidTokenError:
        raise Exception('Invalid MFA token')

# ===========================
# REGISTRATION
# ===========================

@auth_bp.route('/register', methods=['POST', 'OPTIONS'])
def register():
    """Register a new user and generate backup codes"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.get_json()
        
        if not data.get('username') or not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Username, email, and password are required'}), 400
        
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Username already exists'}), 400
        
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already exists'}), 400
        
        user = User(
            username=data['username'],
            email=data['email'],
            full_name=data.get('full_name', '')
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.flush()
        
        # Generate backup codes
        plain_codes = []
        for _ in range(10):
            code = BackupCode.generate_code()
            plain_codes.append(code)
            
            backup_code = BackupCode(user_id=user.id)
            backup_code.set_code(code)
            db.session.add(backup_code)
        
        db.session.commit()
        
        return jsonify({
            'message': 'User registered successfully',
            'user': user.to_dict(),
            'backup_codes': plain_codes
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ===========================
# LOGIN (Step 1: Password)
# ===========================

@auth_bp.route('/login', methods=['POST', 'OPTIONS'])
def login():
    """Step 1: Verify username and password, return enrolled methods"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.get_json()
        
        if not data.get('username') or not data.get('password'):
            return jsonify({'error': 'Username and password are required'}), 400
        
        user = User.query.filter_by(username=data['username']).first()
        
        if not user or not user.check_password(data['password']):
            return jsonify({'error': 'Invalid username or password'}), 401
        
        if not user.is_active:
            return jsonify({'error': 'Account is deactivated'}), 403
        
        # Generate MFA token
        mfa_token = create_mfa_token(user.id)
        
        # ✅ Get enrolled MFA methods
        enrolled_methods = []
        if user.face_enrolled:
            enrolled_methods.append('face')
        if user.voice_enrolled:
            enrolled_methods.append('voice')
        if user.otp_enrolled:
            enrolled_methods.append('otp')
        if user.gesture_enrolled:
            enrolled_methods.append('gesture')
        if user.keystroke_enrolled:
            enrolled_methods.append('keystroke')
        
        # Always allow backup codes
        enrolled_methods.append('backup_code')
        
        return jsonify({
            'message': 'Password verified. Please complete MFA.',
            'mfa_token': mfa_token,
            'user_id': user.id,
            'username': user.username,
            'enrolled_methods': enrolled_methods,
            'requires_mfa': True
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===========================
# MFA VERIFICATION ROUTES
# ===========================

@auth_bp.route('/mfa/verify-face', methods=['POST', 'OPTIONS'])
def verify_face():
    """Verify face recognition with STRICT multi-metric validation"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.get_json()
        mfa_token = data.get('mfa_token')
        face_image = data.get('face_image')
        
        print("\n" + "="*60)
        print("🔐 [FACE VERIFY] Starting STRICT face verification")
        
        if not mfa_token:
            return jsonify({'error': 'MFA token is required'}), 400
        
        if not face_image:
            return jsonify({'error': 'Face image is required'}), 400
        
        # Decode MFA token to get user_id
        user_id = decode_mfa_token(mfa_token)
        user = User.query.get(user_id)
        
        # ✅ STRICT CHECK: Ensure user exists and face is enrolled
        if not user:
            print("❌ [ERROR] User not found")
            return jsonify({'error': 'User not found'}), 404
        
        if not user.face_enrolled or not user.face_encoding:
            print("❌ [ERROR] Face not enrolled for this user")
            return jsonify({'error': 'Face authentication not enrolled'}), 400
        
        print(f"👤 [USER] {user.username} (ID: {user.id})")
        
        # Import face service
        from services.face_recognition import face_service
        
        # ✅ Extract embedding from LOGIN attempt
        print("🔍 [EXTRACT] Extracting embedding from login face...")
        test_embedding, error, _ = face_service.extract_embedding(
            face_image,
            user_id=user.id,
            username=user.username,
            save_image=False  # Don't save login attempts
        )
        
        if error:
            print(f"❌ [ERROR] {error}")
            return jsonify({'error': error}), 400
        
        # ✅ Load ENROLLED face embedding for THIS USER
        print("📦 [LOAD] Loading enrolled face embedding...")
        try:
            stored_embedding = face_service.deserialize_embedding(user.face_encoding)
        except Exception as e:
            print(f"❌ [ERROR] Failed to load stored embedding: {str(e)}")
            return jsonify({'error': 'Invalid stored face data. Please re-enroll.'}), 500
        
        # ✅ STRICT VERIFICATION: Compare embeddings
        print("🔐 [VERIFY] Comparing faces with STRICT threshold...")
        is_match, confidence, distance = face_service.verify_faces(
            stored_embedding,
            test_embedding
        )
        
        # ✅ STRICT DECISION: Only allow if match is TRUE
        if not is_match:
            print(f"❌ [FAILED] Face verification failed")
            print(f"   Distance: {distance:.6f}")
            print(f"   Confidence: {confidence:.2f}%")
            
            # Log failed attempt
            login_record = LoginHistory(
                user_id=user.id,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                mfa_method='face',
                success=False
            )
            db.session.add(login_record)
            db.session.commit()
            
            return jsonify({
                'error': 'Face verification failed. The face does not match your enrolled face.',
                'confidence': float(confidence),
                'distance': float(distance)
            }), 401
        
        # ✅ SUCCESS: Generate tokens
        print(f"✅ [SUCCESS] Face verified (confidence: {confidence:.2f}%)")
        
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)
        
        user.last_login = datetime.utcnow()
        
        # Log successful login
        login_record = LoginHistory(
            user_id=user.id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            mfa_method='face',
            success=True
        )
        db.session.add(login_record)
        db.session.commit()
        
        print("="*60 + "\n")
        
        return jsonify({
            'message': f'Face verified successfully (confidence: {confidence:.2f}%)',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'confidence': float(confidence),
            'distance': float(distance),
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        print(f"❌ [ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        print("="*60 + "\n")
        return jsonify({'error': 'Verification failed. Please try again.'}), 500


@auth_bp.route('/mfa/verify-voice', methods=['POST', 'OPTIONS'])
def verify_voice():
    """Verify voice recognition with STRICT matching"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.get_json()
        mfa_token = data.get('mfa_token')
        voice_audio = data.get('voice_audio')
        
        print("\n" + "="*60)
        print("🎤 [VOICE VERIFY] Starting voice verification")
        
        if not mfa_token:
            return jsonify({'error': 'MFA token is required'}), 400
        
        if not voice_audio:
            return jsonify({'error': 'Voice audio is required'}), 400
        
        user_id = decode_mfa_token(mfa_token)
        user = User.query.get(user_id)
        
        if not user or not user.voice_enrolled:
            print("❌ [VOICE VERIFY] Voice not enrolled for this user")
            return jsonify({'error': 'Voice authentication not enrolled'}), 400
        
        print(f"👤 [USER] {user.username} (ID: {user.id})")
        
        # Import voice service
        try:
            from services.voice_recognition import voice_service
        except ImportError:
            import importlib.util
            import os
            import sys
            backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            spec = importlib.util.spec_from_file_location(
                "voice_recognition_service",
                os.path.join(backend_dir, "services", "voice_recognition.py")
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            voice_service = module.voice_service
        
        # Extract features from provided audio
        print("🔍 [EXTRACT] Extracting features from login voice...")
        test_features, error, _ = voice_service.extract_features(
            voice_audio,
            user_id=user.id,
            username=user.username,
            save_audio=False
        )
        
        if error:
            print(f"❌ [ERROR] {error}")
            return jsonify({'error': error}), 400
        
        # Load enrolled voice features
        print("📦 [LOAD] Loading enrolled voice features...")
        stored_features = voice_service.deserialize_features(user.voice_embedding)
        
        # Verify voices match
        print("🔐 [VERIFY] Comparing voices with STRICT threshold...")
        is_match, similarity, distance = voice_service.verify_voices(
            stored_features,
            test_features
        )
        
        if not is_match:
            print(f"❌ [FAILED] Voice verification failed (similarity: {similarity:.2%})")
            
            # Log failed attempt
            login_record = LoginHistory(
                user_id=user.id,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                mfa_method='voice',
                success=False
            )
            db.session.add(login_record)
            db.session.commit()
            
            return jsonify({
                'error': 'Voice verification failed. Please try again or use a different method.',
                'similarity': similarity
            }), 401
        
        print(f"✅ [SUCCESS] Voice verified (similarity: {similarity:.2%})")
        
        # Generate tokens
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)
        
        user.last_login = datetime.utcnow()
        
        # Log successful login
        login_record = LoginHistory(
            user_id=user.id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            mfa_method='voice',
            success=True
        )
        db.session.add(login_record)
        db.session.commit()
        
        print("="*60 + "\n")
        
        return jsonify({
            'message': f'Voice verified successfully (confidence: {similarity:.2%})',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'similarity': similarity,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        print(f"❌ [ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        print("="*60 + "\n")
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/mfa/verify-otp', methods=['POST', 'OPTIONS'])
def verify_otp():
    """Verify OTP/TOTP code"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.get_json()
        mfa_token = data.get('mfa_token')
        otp_code = data.get('otp_code')
        
        if not mfa_token or not otp_code:
            return jsonify({'error': 'MFA token and OTP code are required'}), 400
        
        user_id = decode_mfa_token(mfa_token)
        user = User.query.get(user_id)
        
        if not user or not user.otp_enrolled:
            return jsonify({'error': 'OTP not enrolled'}), 400
        
        # Verify OTP
        import pyotp
        totp = pyotp.TOTP(user.otp_secret)
        
        if not totp.verify(otp_code):
            return jsonify({'error': 'Invalid OTP code'}), 401
        
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)
        
        user.last_login = datetime.utcnow()
        
        login_record = LoginHistory(
            user_id=user.id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            mfa_method='otp',
            success=True
        )
        db.session.add(login_record)
        db.session.commit()
        
        return jsonify({
            'message': 'OTP verified successfully',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/mfa/verify-backup-code', methods=['POST', 'OPTIONS'])
def verify_backup_code():
    """Verify backup code"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.get_json()
        mfa_token = data.get('mfa_token')
        backup_code = data.get('backup_code')
        
        if not mfa_token or not backup_code:
            return jsonify({'error': 'MFA token and backup code are required'}), 400
        
        user_id = decode_mfa_token(mfa_token)
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        codes = BackupCode.query.filter_by(user_id=user.id, is_used=False).all()
        
        if not codes:
            return jsonify({'error': 'No backup codes available'}), 400
        
        for code in codes:
            if code.check_code(backup_code.strip().upper()):
                code.is_used = True
                code.used_at = datetime.utcnow()
                
                access_token = create_access_token(identity=user.id)
                refresh_token = create_refresh_token(identity=user.id)
                
                user.last_login = datetime.utcnow()
                
                login_record = LoginHistory(
                    user_id=user.id,
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent'),
                    mfa_method='backup_code',
                    success=True
                )
                db.session.add(login_record)
                db.session.commit()
                
                return jsonify({
                    'message': 'Backup code verified successfully',
                    'access_token': access_token,
                    'refresh_token': refresh_token,
                    'user': user.to_dict()
                }), 200
        
        return jsonify({'error': 'Invalid backup code'}), 401
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/mfa/verify-gesture', methods=['POST', 'OPTIONS'])
def verify_gesture():
    """Verify gesture recognition with STRICT matching"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.get_json()
        mfa_token = data.get('mfa_token')
        gesture_data = data.get('gesture')
        
        print("\n" + "="*60)
        print("✋ [GESTURE VERIFY] Starting gesture verification")
        
        if not mfa_token:
            return jsonify({'error': 'MFA token is required'}), 400
        
        if not gesture_data:
            return jsonify({'error': 'Gesture data is required'}), 400
        
        user_id = decode_mfa_token(mfa_token)
        user = User.query.get(user_id)
        
        if not user or not user.gesture_enrolled:
            print("❌ [GESTURE VERIFY] Gesture not enrolled")
            return jsonify({'error': 'Gesture authentication not enrolled'}), 400
        
        print(f"👤 [USER] {user.username} (ID: {user.id})")
        
        # Import gesture service
        try:
            from services.gesture_recognition import gesture_service
        except ImportError:
            import importlib.util
            import os
            import sys
            backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            spec = importlib.util.spec_from_file_location(
                "gesture_recognition_service",
                os.path.join(backend_dir, "services", "gesture_recognition.py")
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            gesture_service = module.gesture_service
        
        # Extract features from provided gesture
        print("🔍 [EXTRACT] Extracting features from login gesture...")
        test_features, error, _ = gesture_service.extract_features(
            gesture_data,
            user_id=user.id,
            username=user.username,
            save_pattern=False
        )
        
        if error:
            print(f"❌ [ERROR] {error}")
            return jsonify({'error': error}), 400
        
        # Load enrolled gesture features
        print("📦 [LOAD] Loading enrolled gesture features...")
        stored_features = gesture_service.deserialize_features(user.gesture_features)
        
        # Verify gestures match
        print("🔐 [VERIFY] Comparing gestures with STRICT threshold...")
        is_match, similarity, distance = gesture_service.verify_gestures(
            stored_features,
            test_features
        )
        
        if not is_match:
            print(f"❌ [FAILED] Gesture verification failed (similarity: {similarity:.2%})")
            
            # Log failed attempt
            login_record = LoginHistory(
                user_id=user.id,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                mfa_method='gesture',
                success=False
            )
            db.session.add(login_record)
            db.session.commit()
            
            return jsonify({
                'error': 'Gesture verification failed. Please try again or use a different method.',
                'similarity': similarity
            }), 401
        
        print(f"✅ [SUCCESS] Gesture verified (similarity: {similarity:.2%})")
        
        # Generate tokens
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)
        
        user.last_login = datetime.utcnow()
        
        # Log successful login
        login_record = LoginHistory(
            user_id=user.id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            mfa_method='gesture',
            success=True
        )
        db.session.add(login_record)
        db.session.commit()
        
        print("="*60 + "\n")
        
        return jsonify({
            'message': f'Gesture verified successfully (confidence: {similarity:.2%})',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'similarity': similarity,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        print(f"❌ [ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        print("="*60 + "\n")
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/mfa/verify-keystroke', methods=['POST', 'OPTIONS'])
def verify_keystroke():
    """Verify keystroke dynamics with ML-based matching"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.get_json()
        mfa_token = data.get('mfa_token')
        keystroke_sample = data.get('keystroke')
        passphrase = data.get('passphrase')
        
        if not mfa_token or not keystroke_sample:
            return jsonify({'error': 'MFA token and keystroke data required'}), 400
        
        user_id = decode_mfa_token(mfa_token)
        user = User.query.get(user_id)
        
        if not user or not user.keystroke_enrolled:
            return jsonify({'error': 'Keystroke pattern not enrolled'}), 400
        
        # Verify passphrase
        if passphrase != user.keystroke_passphrase:
            return jsonify({'error': 'Incorrect passphrase'}), 401
        
        # Import keystroke service
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        
        from services.keystroke_service import verify_keystroke_pattern
        import json
        
        # Load enrolled profile
        enrolled_profile = json.loads(user.keystroke_features)
        
        # Verify keystroke pattern
        verified, confidence = verify_keystroke_pattern(enrolled_profile, keystroke_sample)
        
        if not verified:
            return jsonify({
                'error': 'Keystroke pattern does not match',
                'confidence': confidence
            }), 401
        
        # Generate tokens
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)
        
        user.last_login = datetime.utcnow()
        
        login_record = LoginHistory(
            user_id=user.id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            mfa_method='keystroke',
            success=True
        )
        db.session.add(login_record)
        db.session.commit()
        
        return jsonify({
            'message': f'Keystroke verified (confidence: {confidence:.2%})',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'confidence': confidence,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===========================
# TOKEN REFRESH
# ===========================

@auth_bp.route('/refresh', methods=['POST', 'OPTIONS'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        current_user_id = get_jwt_identity()
        access_token = create_access_token(identity=current_user_id)
        
        return jsonify({'access_token': access_token}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===========================
# LOGOUT
# ===========================

@auth_bp.route('/logout', methods=['POST', 'OPTIONS'])
@jwt_required()
def logout():
    """Logout user"""
    if request.method == 'OPTIONS':
        return '', 200
    
    return jsonify({'message': 'Logged out successfully'}), 200
