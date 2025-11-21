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

# Storage directory for face images
FACE_STORAGE_DIR = Path("stored_face_data")
FACE_STORAGE_DIR.mkdir(exist_ok=True)

class AdvancedFaceService:
    """
    Face recognition service using the face_recognition library.
    Handles image processing, embedding extraction, and verification.
    """
    
    DETECTION_MODEL = "hog"  # 'hog' is faster, 'cnn' is more accurate but slower
    ENCODING_MODEL = "large"
    MATCH_THRESHOLD = 0.99  # Default for face_recognition

    @staticmethod
    def save_face_image(base64_image, user_id, username):
        """Saves the enrolled face image to the storage directory."""
        print(f"\n💾 [SAVE] Starting face image save for user_id={user_id}, username={username}")
        
        try:
            if 'base64,' in base64_image:
                base64_image = base64_image.split('base64,')[1]
            
            image_data = base64.b64decode(base64_image)
            image = Image.open(io.BytesIO(image_data))
            
            print(f"📊 [IMAGE] Image mode: {image.mode}, Size: {image.size}")

            # Ensure image is RGB before saving
            if image.mode != 'RGB':
                print(f"🔄 [CONVERT] Converting image from {image.mode} to RGB")
                image = image.convert('RGB')

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"user_{user_id}_{username}_{timestamp}_face.jpg"
            file_path = FACE_STORAGE_DIR / filename
            
            image.save(file_path, "JPEG")
            print(f"✅ [SAVED] Face image saved: {file_path}")
            print(f"📏 [SIZE] File size: {os.path.getsize(file_path)} bytes\n")
            
            return str(file_path), None
            
        except Exception as e:
            print(f"❌ [ERROR] Failed to save face image: {str(e)}\n")
            return None, str(e)

    @staticmethod
    def extract_embedding(base64_image, user_id=None, username=None, save_image=True):
        """
        Extracts a 128-dimensional face embedding from a base64 image.
        """
        print("\n" + "=" * 60)
        print(f"🔍 [EXTRACT] Starting face embedding extraction")
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
                print("⚠️  [CONVERT] Converting RGBA to RGB...")
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

            if not face_locations:
                print("⚠️  [NO FACE] No face detected")
                print("=" * 60 + "\n")
                return None, "No face detected. Please try again.", None
                
            if len(face_locations) > 1:
                print(f"⚠️  [MULTIPLE] {len(face_locations)} faces detected")
                print("=" * 60 + "\n")
                return None, "Multiple faces detected. Please ensure only one person is in the frame.", None

            print(f"✅ [DETECTED] Face location: {face_locations[0]}")

            # Extract embeddings
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
                print("❌ [FAILED] Could not extract features")
                print("=" * 60 + "\n")
                return None, "Could not extract features from the detected face.", None

            embedding = face_encodings[0]
            print(f"✅ [SUCCESS] Embedding shape: {embedding.shape}")
            print(f"📈 [STATS] Mean: {np.mean(embedding):.4f}, Std: {np.std(embedding):.4f}")

            # Save image if requested
            if save_image and user_id and username:
                saved_image_path, save_error = AdvancedFaceService.save_face_image(
                    base64_image, 
                    user_id, 
                    username
                )
            
            total_duration = (datetime.now() - start_time).total_seconds()
            print(f"⏱️  [TOTAL] Processing time: {total_duration:.2f}s")
            print("✅ [COMPLETE] Extraction successful")
            print("=" * 60 + "\n")
            
            return embedding, None, saved_image_path
            
        except RuntimeError as re:
            print(f"❌ [RUNTIME ERROR] {str(re)}")
            print("=" * 60 + "\n")
            if "Unsupported image type" in str(re):
                return None, "Image format is not supported. Please use a standard image.", None
            return None, "A runtime error occurred during face processing.", None
            
        except Exception as e:
            print(f"❌ [UNEXPECTED ERROR] {str(e)}")
            print("=" * 60 + "\n")
            return None, "An unexpected error occurred during face extraction.", None

    @staticmethod
    def verify_faces(known_embedding, test_embedding, threshold=None):
        """Verifies if two face embeddings match."""
        print("\n" + "=" * 60)
        print("🔐 [VERIFY] Starting face verification")
        
        if threshold is None:
            threshold = AdvancedFaceService.MATCH_THRESHOLD
        
        print(f"🎯 [THRESHOLD] {threshold}")
        
        try:
            start_time = datetime.now()
            
            # Calculate distance
            distance = face_recognition.face_distance([known_embedding], test_embedding)[0]
            
            # Determine if match
            is_match = distance <= threshold
            
            # Calculate confidence
            confidence = max(0, (1 - (distance / threshold)) * 100) if is_match else 0
            
            duration = (datetime.now() - start_time).total_seconds()
            
            print(f"📏 [DISTANCE] {distance:.6f}")
            print(f"🎯 [RESULT] Match: {is_match}")
            print(f"📊 [CONFIDENCE] {confidence:.2f}%")
            print(f"⏱️  [TIMING] {duration:.4f}s")
            
            if is_match:
                print(f"✅ [SUCCESS] Faces match!")
            else:
                print(f"❌ [FAILED] Faces do not match")
            
            print("=" * 60 + "\n")
            
            return is_match, confidence, distance
            
        except Exception as e:
            print(f"❌ [ERROR] Verification failed: {str(e)}")
            print("=" * 60 + "\n")
            return False, 0.0, 1.0

    @staticmethod
    def serialize_embedding(embedding):
        """Converts numpy array to a JSON string for database storage."""
        return json.dumps(embedding.tolist())

    @staticmethod
    def deserialize_embedding(json_string):
        """Converts a JSON string back to a numpy array."""
        return np.array(json.loads(json_string))

# Create singleton instance
face_service = AdvancedFaceService()

# Service initialization message
print("\n" + "=" * 60)
print("🚀 [INIT] Face Recognition Service Initialized")
print(f"📁 [STORAGE] {FACE_STORAGE_DIR.absolute()}")
print(f"🔧 [CONFIG] Detection: {AdvancedFaceService.DETECTION_MODEL}, Encoding: {AdvancedFaceService.ENCODING_MODEL}")
print(f"🔧 [CONFIG] Threshold: {AdvancedFaceService.MATCH_THRESHOLD}")
print("=" * 60 + "\n")
