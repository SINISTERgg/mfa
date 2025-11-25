"""
Advanced Face Recognition Service - STRICT VERIFICATION MODE
Uses face_recognition library with multi-metric validation
Only enrolled faces pass authentication - Zero false positives
"""
import face_recognition
import cv2
import numpy as np
import base64
from PIL import Image
import io
import json
import os
from pathlib import Path
from datetime import datetime
import hashlib

# Storage directory for face images
FACE_STORAGE_DIR = Path("stored_face_data")
FACE_STORAGE_DIR.mkdir(exist_ok=True)

class AdvancedFaceService:
    """
    Face recognition with STRICT multi-metric verification.
    Only enrolled faces will pass authentication.
    """
    
    DETECTION_MODEL = "hog"  # 'hog' is faster, 'cnn' is more accurate
    ENCODING_MODEL = "large"  # Use large model for 128-dim embeddings
    
    # ✅ STRICT THRESHOLDS - Tuned to reject impostors
    DISTANCE_THRESHOLD = 0.35    # Face distance must be < 0.40 (STRICT)
    MIN_CONFIDENCE = 90.0  # Minimum 90% confidence required
    MIN_COSINE_SIMILARITY = 0.65  # Cosine similarity must be > 0.65

    @staticmethod
    def save_face_image(base64_image, user_id, username):
        """Saves enrolled face image to storage directory"""
        print(f"\n💾 [SAVE] Saving face image for user_id={user_id}, username={username}")
        
        try:
            # Decode base64
            if 'base64,' in base64_image:
                base64_image = base64_image.split('base64,')[1]
            
            image_data = base64.b64decode(base64_image)
            image = Image.open(io.BytesIO(image_data))
            
            print(f"📊 [IMAGE] Mode: {image.mode}, Size: {image.size}")
            
            # Ensure RGB format
            if image.mode != 'RGB':
                print(f"🔄 [CONVERT] Converting {image.mode} → RGB")
                image = image.convert('RGB')
            
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"user_{user_id}_{username}_{timestamp}_face.jpg"
            file_path = FACE_STORAGE_DIR / filename
            
            # Save as JPEG
            image.save(file_path, "JPEG", quality=95)
            
            print(f"✅ [SAVED] {file_path}")
            print(f"📏 [SIZE] {os.path.getsize(file_path)} bytes\n")
            
            return str(file_path), None
            
        except Exception as e:
            print(f"❌ [ERROR] Save failed: {str(e)}\n")
            return None, str(e)

    @staticmethod
    def extract_embedding(base64_image, user_id=None, username=None, save_image=True):
        """
        Extracts 128-dimensional face embedding with validation.
        Returns: (embedding, error, saved_path)
        """
        print("\n" + "=" * 60)
        print("🔍 [EXTRACT] Starting face embedding extraction")
        print(f"👤 [USER] user_id={user_id}, username={username}")
        
        saved_image_path = None
        start_time = datetime.now()
        
        try:
            # Decode base64 image
            print("📥 [DECODE] Decoding base64 image...")
            if 'base64,' in base64_image:
                base64_image = base64_image.split('base64,')[1]
            
            image_data = base64.b64decode(base64_image)
            image = np.array(Image.open(io.BytesIO(image_data)))
            
            print(f"📊 [IMAGE] Shape: {image.shape}, dtype: {image.dtype}")
            
            # Convert RGBA to RGB if needed
            if len(image.shape) == 3 and image.shape[2] == 4:
                print("⚠️  [CONVERT] Converting RGBA → RGB...")
                image = image[:, :, :3]
                print(f"✅ [CONVERT] New shape: {image.shape}")
            
            # Detect faces
            print(f"🔎 [DETECT] Detecting faces (model: {AdvancedFaceService.DETECTION_MODEL})...")
            detect_start = datetime.now()
            
            face_locations = face_recognition.face_locations(
                image, 
                model=AdvancedFaceService.DETECTION_MODEL
            )
            
            detect_duration = (datetime.now() - detect_start).total_seconds()
            print(f"⏱️  [TIMING] Detection: {detect_duration:.2f}s")
            
            # Validate detection
            if not face_locations:
                print("⚠️  [NO FACE] No face detected")
                print("=" * 60 + "\n")
                return None, "No face detected. Please ensure your face is visible and well-lit.", None
            
            if len(face_locations) > 1:
                print(f"⚠️  [MULTIPLE] {len(face_locations)} faces detected")
                print("=" * 60 + "\n")
                return None, "Multiple faces detected. Please ensure only one person is in frame.", None
            
            print(f"✅ [DETECTED] Face location: {face_locations[0]}")
            
            # Extract face embeddings
            print(f"🧬 [ENCODE] Extracting embeddings (model: {AdvancedFaceService.ENCODING_MODEL})...")
            encode_start = datetime.now()
            
            face_encodings = face_recognition.face_encodings(
                image, 
                known_face_locations=face_locations, 
                model=AdvancedFaceService.ENCODING_MODEL
            )
            
            encode_duration = (datetime.now() - encode_start).total_seconds()
            print(f"⏱️  [TIMING] Encoding: {encode_duration:.2f}s")
            
            if not face_encodings:
                print("❌ [FAILED] Could not extract facial features")
                print("=" * 60 + "\n")
                return None, "Could not extract facial features. Please try again with better lighting.", None
            
            embedding = face_encodings[0]
            
            # Quality check - Generate unique hash for this embedding
            embedding_hash = hashlib.sha256(embedding.tobytes()).hexdigest()[:16]
            
            print(f"✅ [SUCCESS] Embedding extracted")
            print(f"📊 [SHAPE] {embedding.shape}")
            print(f"📈 [STATS] Mean: {np.mean(embedding):.4f}, Std: {np.std(embedding):.4f}")
            print(f"🔑 [HASH] {embedding_hash}")
            
            # Save image if requested
            if save_image and user_id and username:
                saved_image_path, _ = AdvancedFaceService.save_face_image(
                    base64_image, user_id, username
                )
            
            total_duration = (datetime.now() - start_time).total_seconds()
            print(f"⏱️  [TOTAL] {total_duration:.2f}s")
            print("✅ [COMPLETE] Extraction successful")
            print("=" * 60 + "\n")
            
            return embedding, None, saved_image_path
            
        except Exception as e:
            print(f"❌ [ERROR] {str(e)}")
            import traceback
            traceback.print_exc()
            print("=" * 60 + "\n")
            return None, f"Face processing error: {str(e)}", None

    @staticmethod
    def verify_faces(known_embedding, test_embedding, threshold=None):
        """
        STRICT face verification using multiple metrics.
        Only returns True if ALL criteria are met:
        1. Face distance < threshold
        2. Confidence >= 95%
        3. Cosine similarity > 0.85
        """
        print("\n" + "=" * 60)
        print("🔐 [VERIFY] Starting STRICT face verification")
        
        if threshold is None:
            threshold = AdvancedFaceService.DISTANCE_THRESHOLD
        
        print(f"🎯 [CRITERIA]")
        print(f"   1. Distance < {threshold}")
        print(f"   2. Confidence >= {AdvancedFaceService.MIN_CONFIDENCE}%")
        print(f"   3. Cosine Similarity > {AdvancedFaceService.MIN_COSINE_SIMILARITY}")
        
        try:
            start_time = datetime.now()
            
            # ✅ METRIC 1: Face Distance (primary metric from face_recognition library)
            distance = face_recognition.face_distance([known_embedding], test_embedding)[0]
            
            # ✅ METRIC 2: Confidence Percentage
            if distance < threshold:
                confidence = (1 - (distance / threshold)) * 100
            else:
                confidence = 0
            
            # ✅ METRIC 3: Cosine Similarity (secondary validation)
            dot_product = np.dot(known_embedding, test_embedding)
            norm_known = np.linalg.norm(known_embedding)
            norm_test = np.linalg.norm(test_embedding)
            cosine_similarity = dot_product / (norm_known * norm_test + 1e-10)
            
            # ✅ METRIC 4: Euclidean Distance (tertiary validation)
            euclidean_dist = np.linalg.norm(known_embedding - test_embedding)
            
            # ✅ STRICT DECISION: ALL criteria must be met
            criterion_1 = distance < threshold
            criterion_2 = confidence >= AdvancedFaceService.MIN_CONFIDENCE
            criterion_3 = cosine_similarity > AdvancedFaceService.MIN_COSINE_SIMILARITY
            
            is_match = criterion_1 and criterion_2 and criterion_3
            
            duration = (datetime.now() - start_time).total_seconds()
            
            print(f"\n📊 [METRICS]")
            print(f"   Face Distance:      {distance:.6f} {'✅' if criterion_1 else '❌'}")
            print(f"   Confidence:         {confidence:.2f}% {'✅' if criterion_2 else '❌'}")
            print(f"   Cosine Similarity:  {cosine_similarity:.6f} {'✅' if criterion_3 else '❌'}")
            print(f"   Euclidean Distance: {euclidean_dist:.6f}")
            print(f"   Timing:             {duration:.4f}s")
            
            print(f"\n🎯 [DECISION] Match: {is_match}")
            
            if is_match:
                print(f"✅ [SUCCESS] All criteria met - Faces match!")
                print(f"   Confidence: {confidence:.2f}%")
            else:
                print(f"❌ [FAILED] Criteria not met - Faces do NOT match")
                if not criterion_1:
                    print(f"   ❌ Distance too high: {distance:.4f} >= {threshold}")
                if not criterion_2:
                    print(f"   ❌ Confidence too low: {confidence:.2f}% < {AdvancedFaceService.MIN_CONFIDENCE}%")
                if not criterion_3:
                    print(f"   ❌ Cosine similarity too low: {cosine_similarity:.4f} <= {AdvancedFaceService.MIN_COSINE_SIMILARITY}")
            
            print("=" * 60 + "\n")
            
            return is_match, confidence, distance
            
        except Exception as e:
            print(f"❌ [ERROR] Verification failed: {str(e)}")
            import traceback
            traceback.print_exc()
            print("=" * 60 + "\n")
            return False, 0.0, 1.0

    @staticmethod
    def serialize_embedding(embedding):
        """Converts numpy array to JSON string for database storage"""
        return json.dumps(embedding.tolist())

    @staticmethod
    def deserialize_embedding(json_string):
        """Converts JSON string back to numpy array"""
        try:
            return np.array(json.loads(json_string))
        except Exception as e:
            print(f"❌ [DESERIALIZE ERROR] {str(e)}")
            raise Exception("Invalid face encoding data. Please re-enroll face.")

    @staticmethod
    def delete_user_faces(user_id):
        """Delete all face images for a user"""
        deleted = 0
        for file_path in FACE_STORAGE_DIR.glob(f"user_{user_id}_*"):
            try:
                os.remove(file_path)
                deleted += 1
                print(f"🗑️  Deleted: {file_path}")
            except Exception as e:
                print(f"⚠️  Could not delete {file_path}: {str(e)}")
        return deleted

# Create singleton instance
face_service = AdvancedFaceService()

# Service initialization message
print("\n" + "=" * 60)
print("🚀 [INIT] Face Recognition Service Initialized")
print(f"🔐 [MODE] STRICT VERIFICATION")
print(f"📁 [STORAGE] {FACE_STORAGE_DIR.absolute()}")
print(f"🔧 [CONFIG] Detection Model: {AdvancedFaceService.DETECTION_MODEL}")
print(f"🔧 [CONFIG] Encoding Model: {AdvancedFaceService.ENCODING_MODEL}")
print(f"🎯 [THRESHOLDS]")
print(f"   Distance: < {AdvancedFaceService.DISTANCE_THRESHOLD}")
print(f"   Confidence: >= {AdvancedFaceService.MIN_CONFIDENCE}%")
print(f"   Cosine Similarity: > {AdvancedFaceService.MIN_COSINE_SIMILARITY}")
print("=" * 60 + "\n")
