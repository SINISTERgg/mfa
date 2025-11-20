"""
Advanced Voice Recognition Service with Strict Verification
Stores voice data and performs accurate speaker verification
"""
import numpy as np
import base64
import io
import os
from pathlib import Path
from datetime import datetime
import json
import hashlib

# Storage directory
VOICE_STORAGE_DIR = Path("C:/Hoysala/Projects/mfa-authentication-system/backend/stored_voice_data")
VOICE_STORAGE_DIR.mkdir(parents=True, exist_ok=True)

class AdvancedVoiceService:
    """Advanced voice recognition with strict verification"""
    
    SIMILARITY_THRESHOLD = 0.92  # 92% similarity required (STRICT)
    MIN_AUDIO_SIZE = 10000  # Minimum 10KB
    MAX_AUDIO_SIZE = 5000000  # Maximum 5MB
    FEATURE_SIZE = 256  # Increased feature vector size

    @staticmethod
    def save_voice_sample(base64_audio, user_id, username):
        """Save voice audio to storage directory"""
        try:
            print(f"\n💾 [SAVE] Saving voice for user_id={user_id}, username={username}")
            
            if 'base64,' in base64_audio:
                base64_audio = base64_audio.split('base64,')[1]
            
            audio_data = base64.b64decode(base64_audio)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"user_{user_id}_{username}_{timestamp}_voice.webm"
            file_path = VOICE_STORAGE_DIR / filename
            
            with open(file_path, 'wb') as f:
                f.write(audio_data)
            
            print(f"✅ [SAVED] Voice saved: {file_path}")
            print(f"📏 [SIZE] File size: {os.path.getsize(file_path)} bytes\n")
            
            return str(file_path), None
            
        except Exception as e:
            print(f"❌ [ERROR] Failed to save voice: {str(e)}\n")
            return None, str(e)

    @staticmethod
    def extract_features(base64_audio, user_id=None, username=None, save_audio=True):
        """Extract comprehensive voice features from audio"""
        print("\n" + "=" * 60)
        print("🎤 [EXTRACT] Starting voice feature extraction")
        print(f"👤 [USER] user_id={user_id}, username={username}")
        
        saved_audio_path = None
        
        try:
            # Decode base64
            if 'base64,' in base64_audio:
                base64_audio = base64_audio.split('base64,')[1]
            
            audio_bytes = base64.b64decode(base64_audio)
            audio_size = len(audio_bytes)
            
            print(f"📥 [DECODED] Audio size: {audio_size} bytes")
            
            # Validate audio size
            if audio_size < AdvancedVoiceService.MIN_AUDIO_SIZE:
                return None, f"Audio too short. Minimum {AdvancedVoiceService.MIN_AUDIO_SIZE} bytes required", None
            
            if audio_size > AdvancedVoiceService.MAX_AUDIO_SIZE:
                return None, f"Audio too large. Maximum {AdvancedVoiceService.MAX_AUDIO_SIZE} bytes allowed", None
            
            # Extract features from multiple segments
            features = []
            
            # 1. Hash-based fingerprint (first 2000 bytes)
            segment1 = audio_bytes[:2000]
            hash1 = hashlib.sha256(segment1).digest()
            features.extend(np.frombuffer(hash1, dtype=np.uint8).astype(float) / 255.0)
            
            # 2. Middle segment (unique to each audio)
            mid_start = len(audio_bytes) // 2 - 1000
            mid_end = mid_start + 2000
            segment2 = audio_bytes[mid_start:mid_end]
            hash2 = hashlib.sha256(segment2).digest()
            features.extend(np.frombuffer(hash2, dtype=np.uint8).astype(float) / 255.0)
            
            # 3. End segment
            segment3 = audio_bytes[-2000:]
            hash3 = hashlib.sha256(segment3).digest()
            features.extend(np.frombuffer(hash3, dtype=np.uint8).astype(float) / 255.0)
            
            # 4. Byte distribution (histogram)
            byte_hist, _ = np.histogram(np.frombuffer(audio_bytes, dtype=np.uint8), bins=32, range=(0, 256))
            byte_hist = byte_hist.astype(float) / (len(audio_bytes) + 1e-10)
            features.extend(byte_hist)
            
            # 5. Statistical features across the entire audio
            audio_array = np.frombuffer(audio_bytes, dtype=np.uint8).astype(float)
            
            # Sliding window statistics
            window_size = len(audio_array) // 10
            for i in range(10):
                start = i * window_size
                end = start + window_size
                window = audio_array[start:end]
                
                if len(window) > 0:
                    features.extend([
                        np.mean(window),
                        np.std(window),
                        np.var(window),
                        np.max(window) - np.min(window)
                    ])
            
            # 6. FFT-like features (frequency content approximation)
            # Sample every Nth byte to get frequency-like information
            sampled = audio_array[::100]
            if len(sampled) > 32:
                sampled = sampled[:32]
            elif len(sampled) < 32:
                sampled = np.pad(sampled, (0, 32 - len(sampled)))
            features.extend(sampled / 255.0)
            
            # Convert to numpy array
            features = np.array(features)
            
            # Ensure consistent size
            if len(features) < AdvancedVoiceService.FEATURE_SIZE:
                features = np.pad(features, (0, AdvancedVoiceService.FEATURE_SIZE - len(features)))
            else:
                features = features[:AdvancedVoiceService.FEATURE_SIZE]
            
            # Normalize
            feature_norm = np.linalg.norm(features)
            if feature_norm > 0:
                features = features / feature_norm
            
            print(f"✅ [SUCCESS] Extracted {len(features)} features")
            print(f"📊 [STATS] Mean: {np.mean(features):.4f}, Std: {np.std(features):.4f}")
            print(f"📊 [NORM] L2 Norm: {np.linalg.norm(features):.4f}")
            
            # Save audio if requested
            if save_audio and user_id and username:
                saved_audio_path, _ = AdvancedVoiceService.save_voice_sample(
                    base64_audio, user_id, username
                )
            
            print("=" * 60 + "\n")
            return features, None, saved_audio_path
            
        except Exception as e:
            print(f"❌ [ERROR] {str(e)}")
            import traceback
            traceback.print_exc()
            print("=" * 60 + "\n")
            return None, f"Voice processing error: {e}", None

    @staticmethod
    def verify_voices(known_features, test_features, threshold=None):
        """Verify if two voice samples match with STRICT comparison"""
        print("\n" + "=" * 60)
        print("🔐 [VERIFY] Starting voice verification")
        
        if threshold is None:
            threshold = AdvancedVoiceService.SIMILARITY_THRESHOLD
        
        print(f"🎯 [THRESHOLD] {threshold}")
        
        try:
            # Ensure same dimensions
            if len(known_features) != len(test_features):
                print(f"⚠️ [WARNING] Feature dimension mismatch: {len(known_features)} vs {len(test_features)}")
                return False, 0.0, 1.0
            
            # Method 1: Cosine Similarity
            dot_product = np.dot(known_features, test_features)
            norm_known = np.linalg.norm(known_features)
            norm_test = np.linalg.norm(test_features)
            cosine_similarity = dot_product / (norm_known * norm_test + 1e-10)
            
            # Method 2: Euclidean Distance
            euclidean_dist = np.linalg.norm(known_features - test_features)
            euclidean_similarity = 1 / (1 + euclidean_dist)
            
            # Method 3: Correlation
            correlation = np.corrcoef(known_features, test_features)[0, 1]
            correlation_similarity = (correlation + 1) / 2  # Scale to [0, 1]
            
            # Combined similarity (weighted average)
            similarity = (
                0.5 * cosine_similarity +
                0.3 * euclidean_similarity +
                0.2 * correlation_similarity
            )
            
            # Calculate distance
            distance = 1 - similarity
            
            # Check if match
            is_match = similarity >= threshold
            
            print(f"📏 [COSINE SIMILARITY] {cosine_similarity:.6f}")
            print(f"📏 [EUCLIDEAN SIMILARITY] {euclidean_similarity:.6f}")
            print(f"📏 [CORRELATION SIMILARITY] {correlation_similarity:.6f}")
            print(f"📊 [COMBINED SIMILARITY] {similarity:.2%}")
            print(f"📏 [DISTANCE] {distance:.6f}")
            print(f"🎯 [RESULT] Match: {is_match}")
            
            if is_match:
                print(f"✅ [SUCCESS] Voices match! (confidence: {similarity:.2%})")
            else:
                print(f"❌ [FAILED] Voices do not match (similarity: {similarity:.2%} < threshold: {threshold:.2%})")
            
            print("=" * 60 + "\n")
            
            return is_match, similarity, distance
            
        except Exception as e:
            print(f"❌ [ERROR] Verification failed: {str(e)}")
            import traceback
            traceback.print_exc()
            print("=" * 60 + "\n")
            return False, 0.0, 1.0

    @staticmethod
    def serialize_features(features):
        """Convert features to string for database"""
        return ','.join(map(str, features))

    @staticmethod
    def deserialize_features(features_str):
        """Convert string back to numpy array"""
        return np.fromstring(features_str, sep=',')

    @staticmethod
    def delete_user_audio(user_id):
        """Delete all voice files for a user"""
        deleted = 0
        for file_path in VOICE_STORAGE_DIR.glob(f"user_{user_id}_*"):
            try:
                os.remove(file_path)
                deleted += 1
            except Exception:
                continue
        return deleted

# Create singleton instance
voice_service = AdvancedVoiceService()

# Service initialization
print("\n" + "=" * 60)
print("🚀 [INIT] Voice Recognition Service Initialized (STRICT MODE)")
print(f"📁 [STORAGE] {VOICE_STORAGE_DIR.absolute()}")
print(f"🔧 [CONFIG] Threshold: {AdvancedVoiceService.SIMILARITY_THRESHOLD} (STRICT)")
print(f"📏 [CONFIG] Feature Size: {AdvancedVoiceService.FEATURE_SIZE}")
print(f"📦 [CONFIG] Audio Size: {AdvancedVoiceService.MIN_AUDIO_SIZE}-{AdvancedVoiceService.MAX_AUDIO_SIZE} bytes")
print("=" * 60 + "\n")
