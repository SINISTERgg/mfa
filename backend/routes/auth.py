from flask import Blueprint, request, jsonify
from extensions import db
from models import User, BackupCode, LoginHistory, VoiceTemplate
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
)
from datetime import datetime, timedelta
import secrets
import jwt as pyjwt
import json

from services.voice_recognition import (
    voice_service_v2,
    SecurityProfile,
)

auth_bp = Blueprint('auth', __name__)

# -------------------------------------------------------------------
# MFA token helpers
# -------------------------------------------------------------------

MFA_TOKEN_SECRET = 'mfa-secret-key-change-in-production'
MFA_TOKEN_EXPIRY = 300  # 5 minutes


def create_mfa_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(seconds=MFA_TOKEN_EXPIRY),
        'iat': datetime.utcnow(),
    }
    return pyjwt.encode(payload, MFA_TOKEN_SECRET, algorithm='HS256')


def decode_mfa_token(token):
    try:
        payload = pyjwt.decode(token, MFA_TOKEN_SECRET, algorithms=['HS256'])
        return payload['user_id']
    except pyjwt.ExpiredSignatureError:
        raise Exception('MFA token expired. Please login again.')
    except pyjwt.InvalidTokenError:
        raise Exception('Invalid MFA token')



def log_login_attempt(user_id, method_type, success, confidence=None):
    """Helper to record a login attempt in LoginHistory; non-fatal on errors."""
    try:
        record = LoginHistory(
            user_id=user_id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            method_type=method_type,  # ✅ FIXED
            success=bool(success)
        )
        # Attach optional confidence if the model supports it (safe attempt)
        if confidence is not None:
            try:
                setattr(record, 'confidence', float(confidence))
            except Exception:
                # Model may not have a 'confidence' field; ignore silently
                pass

        db.session.add(record)
        db.session.commit()
    except Exception as e:
        # Rollback to keep DB consistent and avoid breaking authentication flow
        try:
            db.session.rollback()
        except Exception:
            pass
        print(f"❌ [LOG] Failed to record login attempt: {e}")


# ===========================
# REGISTRATION
# ===========================


@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or not all(k in data for k in ['username', 'email', 'password']):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Check if user already exists
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already registered'}), 400
        
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Username already taken'}), 400
        
        # Create new user
        new_user = User(
            username=data['username'],
            email=data['email']
        )
        new_user.set_password(data['password'])
        
        # ✅ FIRST: Add user to database and commit to get user.id
        db.session.add(new_user)
        db.session.commit()
        
        # ✅ NOW: Generate backup codes (user.id exists now)
        backup_codes = new_user.generate_backup_codes()
        db.session.commit()
        
        # Generate tokens for auto-login
        access_token = create_access_token(identity=new_user.id)
        refresh_token = create_refresh_token(identity=new_user.id)
        
        print(f"✅ [REGISTER] User created: {new_user.username}")
        
        # ✅ Return backup codes along with tokens
        return jsonify({
            'message': 'Registration successful',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'backup_codes': backup_codes,
            'user': new_user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ [REGISTER] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Registration failed'}), 500


# ===========================
# LOGIN (Step 1: Password)
# ===========================


@auth_bp.route('/login', methods=['POST'])
def login():
    """User login endpoint"""
    try:
        data = request.get_json()
        
        # ✅ Add debug logging
        print("\n" + "="*60)
        print("🔐 [LOGIN] Login attempt")
        print(f"📥 [DATA] Received: {data}")
        print("="*60)
        
        # Validate required fields
        if not data:
            print("❌ [ERROR] No data received")
            return jsonify({'error': 'No data provided'}), 400
        
        if 'email' not in data:
            print("❌ [ERROR] Missing email field")
            return jsonify({'error': 'Email is required'}), 400
            
        if 'password' not in data:
            print("❌ [ERROR] Missing password field")
            return jsonify({'error': 'Password is required'}), 400
        
        email = data.get('email')
        password = data.get('password')
        
        print(f"📧 [EMAIL] {email}")
        print(f"🔑 [PASSWORD] {'*' * len(password)} ({len(password)} chars)")
        
        # Find user
        user = User.query.filter_by(email=email).first()
        
        if not user:
            print(f"❌ [ERROR] User not found: {email}")
            return jsonify({'error': 'Invalid email or password'}), 400
        
        print(f"✅ [USER] Found: {user.username} (ID: {user.id})")
        
        # Check password
        if not user.check_password(password):
            print(f"❌ [ERROR] Invalid password for user: {user.username}")
            return jsonify({'error': 'Invalid email or password'}), 400
        
        print(f"✅ [PASSWORD] Correct")
        
        # Check if MFA is required
        mfa_methods = []
        if user.face_enrolled:
            mfa_methods.append('face')
        if user.voice_enrolled:
            mfa_methods.append('voice')
        if user.gesture_enrolled:
            mfa_methods.append('gesture')
        if user.keystroke_enrolled:
            mfa_methods.append('keystroke')
        if user.otp_enrolled:  # ✅ FIXED: was totp_enabled
            mfa_methods.append('totp')
        
        print(f"🔐 [MFA] Enrolled methods: {mfa_methods}")
        
        if mfa_methods:
            # MFA required
            mfa_token = create_mfa_token(user.id)
            print(f"✅ [MFA] Token generated: {mfa_token[:20]}...")
            print("="*60 + "\n")
            
            return jsonify({
                'requires_mfa': True,
                'mfa_token': mfa_token,
                'enrolled_methods': mfa_methods
            }), 200
        else:
            # No MFA, direct login
            access_token = create_access_token(identity=user.id)
            refresh_token = create_refresh_token(identity=user.id)
            
            # Update last login
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            # Log login attempt
            log_login_attempt(user.id, 'password', True, 100.0)
            
            print(f"✅ [LOGIN] Direct login successful")
            print(f"🎫 [TOKEN] Access token generated")
            print("="*60 + "\n")
            
            return jsonify({
                'message': 'Login successful',
                'access_token': access_token,
                'refresh_token': refresh_token,
                'user': user.to_dict()
            }), 200
        
    except Exception as e:
        print(f"❌ [EXCEPTION] {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        print("="*60 + "\n")
        return jsonify({'error': 'Login failed'}), 500



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
                method_type='face',  # ✅ FIXED
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
            method_type='face',  # ✅ FIXED
            success=True,
            confidence=float(confidence)  # ✅ Added confidence
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
def mfa_verify_voice():
    """Verify voice as an MFA step"""
    if request.method == 'OPTIONS':
        return '', 200

    try:
        data = request.get_json() or {}
        mfa_token = data.get('mfa_token')
        base64_audio = data.get('voice_audio')

        if not mfa_token or not base64_audio:
            return jsonify({'error': 'MFA token and voice_audio are required'}), 400

        # Use same helper as other MFA routes
        user_id = decode_mfa_token(mfa_token)
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        template = VoiceTemplate.query.filter_by(user_id=user.id).first()
        if not template or not template.features:
            return jsonify({'error': 'Voice not enrolled'}), 400

        known_features = voice_service_v2.deserialize_features(template.features)
        known_meta = json.loads(template.meta_json or "{}")

        probe_features, probe_meta, _ = voice_service_v2.extract_features(
            base64_audio=base64_audio,
            user_id=str(user.id),
            username=user.username,
            save_audio=False,
            profile=SecurityProfile.BALANCED,
        )

        result = voice_service_v2.verify(
            known_features=known_features,
            probe_features=probe_features,
            known_meta=known_meta,
            probe_meta=probe_meta,
            profile=SecurityProfile.BALANCED,
        )

        record = LoginHistory(
            user_id=user.id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            method_type='voice',
            success=result.is_match,
            confidence=result.similarity * 100.0,
            failure_reason=None if result.is_match else 'Voice mismatch',
        )
        db.session.add(record)
        db.session.commit()

        if not result.is_match:
            return jsonify({
                'error': 'Voice verification failed',
                'similarity': result.similarity,
                'flags': result.flags,
            }), 401

        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)

        return jsonify({
            'message': 'Voice verified successfully',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'similarity': result.similarity,
            'user': user.to_dict(),
        }), 200

    except Exception as e:
        print('mfa_verify_voice error:', e)
        return jsonify({'error': 'Internal server error'}), 500
    
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
        
        # 🔍 Decode MFA token with error handling
        try:
            user_id = decode_mfa_token(mfa_token)
            if not user_id:
                return jsonify({'error': 'Invalid MFA token'}), 401
        except Exception as token_err:
            print(f"MFA token decode failed: {token_err}")
            return jsonify({'error': 'Invalid or expired MFA token'}), 401
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        if not user.otp_enrolled:
            return jsonify({'error': 'OTP not enrolled for this user'}), 400
        
        # 🔧 Verify OTP with time window & detailed logging
        import pyotp
        totp = pyotp.TOTP(user.otp_secret)
        
        # Allow 90s window (3x30s) for clock drift
        is_valid = totp.verify(otp_code, valid_window=3)
        
        print(f"TOTP Debug - User: {user.id}, Secret: {user.otp_secret[:8]}..., Code: {otp_code}, Valid: {is_valid}")
        
        if not is_valid:
            # Log failed attempt
            login_record = LoginHistory(
                user_id=user.id,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                method_type='totp',
                success=False,
                failure_reason=f'Invalid OTP code: {otp_code}'
            )
            db.session.add(login_record)
            db.session.commit()
            
            return jsonify({
                'error': 'Invalid OTP code',
                'code': 'OTP_INVALID',
                'retry_after': 30
            }), 401
        
        # ✅ Success - Create tokens & update user
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)
        
        user.last_login = datetime.utcnow()
        
        login_record = LoginHistory(
            user_id=user.id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            method_type='totp',
            success=True,
            confidence=100.0
        )
        db.session.add(login_record)
        db.session.commit()
        
        return jsonify({
            'message': 'OTP verified successfully',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.to_dict()
        }), 200
        
    except pyotp.HOTPError as e:
        print(f"TOTP HOTP Error: {e}")
        return jsonify({'error': 'Invalid OTP secret format'}), 400
    except ValueError as e:
        print(f"TOTP ValueError: {e}")
        return jsonify({'error': 'Invalid OTP code format'}), 400
    except Exception as e:
        print(f"Verify OTP unexpected error: {e}")
        return jsonify({'error': 'Internal server error'}), 500



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
                    method_type='backup',  # ✅ FIXED
                    success=True,
                    confidence=100.0
                )
                db.session.add(login_record)
                db.session.commit()
                
                return jsonify({
                    'message': 'Backup code verified successfully',
                    'access_token': access_token,
                    'refresh_token': refresh_token,
                    'user': user.to_dict()
                }), 200
        
        # Log failed attempt
        login_record = LoginHistory(
            user_id=user.id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            method_type='backup',  # ✅ FIXED
            success=False,
            failure_reason='Invalid backup code'
        )
        db.session.add(login_record)
        db.session.commit()
        
        return jsonify({'error': 'Invalid backup code'}), 401
        
    except Exception as e:
        print(f"❌ [BACKUP CODE ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
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
                method_type='gesture',  # ✅ FIXED
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
            method_type='gesture',  # ✅ FIXED
            success=True,
            confidence=float(similarity * 100)
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
            # Log failed attempt
            login_record = LoginHistory(
                user_id=user.id,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                method_type='keystroke',  # ✅ FIXED
                success=False,
                confidence=float(confidence)
            )
            db.session.add(login_record)
            db.session.commit()
            
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
            method_type='keystroke',  # ✅ FIXED
            success=True,
            confidence=float(confidence)
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
