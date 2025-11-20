"""
Advanced Gesture Recognition Service
Using accelerometer data and motion patterns for authentication
Stores gesture patterns with ML-based verification
"""
import numpy as np
import json
from datetime import datetime
from pathlib import Path
from scipy.spatial.distance import euclidean, cosine
from scipy.signal import find_peaks
import os

# Storage directory
GESTURE_STORAGE_DIR = Path("C:/Hoysala/Projects/mfa-authentication-system/backend/stored_gesture_data")
GESTURE_STORAGE_DIR.mkdir(parents=True, exist_ok=True)

class AdvancedGestureService:
    """Advanced gesture recognition with motion pattern analysis"""
    
    SIMILARITY_THRESHOLD = 0.97  # 97% similarity required
    MIN_POINTS = 50  # Minimum data points in gesture
    MAX_POINTS = 500  # Maximum data points
    SAMPLE_RATE = 50  # Expected sample rate (Hz)

    @staticmethod
    def save_gesture_pattern(gesture_data, user_id, username):
        """Save gesture pattern to storage"""
        try:
            print(f"\n💾 [SAVE] Saving gesture for user_id={user_id}, username={username}")
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"user_{user_id}_{username}_{timestamp}_gesture.json"
            file_path = GESTURE_STORAGE_DIR / filename
            
            with open(file_path, 'w') as f:
                json.dump(gesture_data, f, indent=2)
            
            print(f"✅ [SAVED] Gesture saved: {file_path}")
            print(f"📏 [SIZE] {len(json.dumps(gesture_data))} bytes\n")
            
            return str(file_path), None
        except Exception as e:
            print(f"❌ [ERROR] Save failed: {str(e)}\n")
            return None, str(e)

    @staticmethod
    def extract_features(gesture_data, user_id=None, username=None, save_pattern=True):
        """Extract features from gesture data"""
        print("\n" + "=" * 60)
        print("✋ [EXTRACT] Starting gesture feature extraction")
        print(f"👤 [USER] user_id={user_id}, username={username}")
        
        saved_pattern_path = None
        
        try:
            # Validate gesture data structure
            if not isinstance(gesture_data, dict):
                return None, "Invalid gesture data format", None
            
            if 'points' not in gesture_data:
                return None, "Missing points in gesture data", None
            
            points = gesture_data['points']
            
            if not isinstance(points, list) or len(points) < AdvancedGestureService.MIN_POINTS:
                return None, f"Insufficient gesture points. Minimum {AdvancedGestureService.MIN_POINTS} required", None
            
            if len(points) > AdvancedGestureService.MAX_POINTS:
                return None, f"Too many gesture points. Maximum {AdvancedGestureService.MAX_POINTS} allowed", None
            
            print(f"📊 [POINTS] {len(points)} data points")
            
            # Extract coordinates
            x_coords = []
            y_coords = []
            timestamps = []
            
            for point in points:
                if 'x' in point and 'y' in point:
                    x_coords.append(float(point['x']))
                    y_coords.append(float(point['y']))
                    if 'timestamp' in point:
                        timestamps.append(float(point['timestamp']))
            
            if len(x_coords) == 0:
                return None, "No valid coordinate data found", None
            
            # Convert to numpy arrays
            x_coords = np.array(x_coords)
            y_coords = np.array(y_coords)
            
            # Extract comprehensive features
            print("🔍 [FEATURES] Extracting gesture features...")
            features = AdvancedGestureService._extract_gesture_features(
                x_coords, y_coords, timestamps
            )
            
            print(f"✅ [SUCCESS] Extracted {len(features)} features")
            print(f"📈 [STATS] Mean: {np.mean(features):.4f}, Std: {np.std(features):.4f}")
            
            # Save pattern if requested
            if save_pattern and user_id and username:
                saved_pattern_path, _ = AdvancedGestureService.save_gesture_pattern(
                    gesture_data, user_id, username
                )
            
            print("=" * 60 + "\n")
            return features, None, saved_pattern_path
            
        except Exception as e:
            print(f"❌ [ERROR] {str(e)}")
            print("=" * 60 + "\n")
            return None, f"Gesture processing error: {e}", None

    @staticmethod
    def _extract_gesture_features(x_coords, y_coords, timestamps):
        """Extract comprehensive features from gesture coordinates"""
        features = []
        
        # 1. Path Length
        distances = np.sqrt(np.diff(x_coords)**2 + np.diff(y_coords)**2)
        total_length = np.sum(distances)
        features.append(total_length)
        
        # 2. Bounding Box
        x_min, x_max = np.min(x_coords), np.max(x_coords)
        y_min, y_max = np.min(y_coords), np.max(y_coords)
        width = x_max - x_min
        height = y_max - y_min
        features.extend([width, height])
        
        # 3. Aspect Ratio
        aspect_ratio = height / (width + 1e-10)
        features.append(aspect_ratio)
        
        # 4. Centroid
        centroid_x = np.mean(x_coords)
        centroid_y = np.mean(y_coords)
        features.extend([centroid_x, centroid_y])
        
        # 5. Direction changes
        angles = np.arctan2(np.diff(y_coords), np.diff(x_coords))
        angle_changes = np.abs(np.diff(angles))
        direction_changes = np.sum(angle_changes > np.pi/4)  # Significant direction changes
        features.append(direction_changes)
        
        # 6. Velocity features (if timestamps available)
        if len(timestamps) == len(x_coords):
            time_diffs = np.diff(timestamps)
            velocities = distances / (time_diffs + 1e-10)
            avg_velocity = np.mean(velocities)
            max_velocity = np.max(velocities)
            features.extend([avg_velocity, max_velocity])
        else:
            features.extend([0, 0])
        
        # 7. Acceleration (second derivative)
        if len(distances) > 1:
            acceleration = np.diff(distances)
            avg_acceleration = np.mean(np.abs(acceleration))
            features.append(avg_acceleration)
        else:
            features.append(0)
        
        # 8. Curvature
        if len(angles) > 0:
            curvature = np.sum(np.abs(angle_changes)) / len(angles)
            features.append(curvature)
        else:
            features.append(0)
        
        # 9. Normalized coordinates (10 sample points along path)
        n_samples = 10
        if len(x_coords) >= n_samples:
            indices = np.linspace(0, len(x_coords)-1, n_samples).astype(int)
            sampled_x = x_coords[indices]
            sampled_y = y_coords[indices]
            
            # Normalize to [0, 1]
            if width > 0:
                sampled_x = (sampled_x - x_min) / width
            if height > 0:
                sampled_y = (sampled_y - y_min) / height
            
            features.extend(sampled_x.tolist())
            features.extend(sampled_y.tolist())
        else:
            features.extend([0] * (n_samples * 2))
        
        # 10. Complexity (number of peaks in distance function)
        if len(distances) > 2:
            peaks, _ = find_peaks(distances)
            complexity = len(peaks)
            features.append(complexity)
        else:
            features.append(0)
        
        # 11. Smoothness (variance of second derivative)
        if len(distances) > 2:
            second_deriv = np.diff(distances, n=2)
            smoothness = np.var(second_deriv)
            features.append(smoothness)
        else:
            features.append(0)
        
        # 12. Start and end point distances from centroid
        start_dist = np.sqrt((x_coords[0] - centroid_x)**2 + (y_coords[0] - centroid_y)**2)
        end_dist = np.sqrt((x_coords[-1] - centroid_x)**2 + (y_coords[-1] - centroid_y)**2)
        features.extend([start_dist, end_dist])
        
        return np.array(features)

    @staticmethod
    def verify_gestures(known_features, test_features, threshold=None):
        """Verify if two gestures match"""
        print("\n" + "=" * 60)
        print("🔐 [VERIFY] Starting gesture verification")
        
        if threshold is None:
            threshold = AdvancedGestureService.SIMILARITY_THRESHOLD
        
        print(f"🎯 [THRESHOLD] {threshold}")
        
        try:
            # Normalize features
            known_norm = known_features / (np.linalg.norm(known_features) + 1e-10)
            test_norm = test_features / (np.linalg.norm(test_features) + 1e-10)
            
            # Calculate cosine similarity
            distance = cosine(known_norm, test_norm)
            similarity = 1 - distance
            
            # Calculate euclidean distance for reference
            euclidean_dist = euclidean(known_norm, test_norm)
            
            is_match = similarity >= threshold
            
            print(f"📏 [COSINE DISTANCE] {distance:.6f}")
            print(f"📏 [EUCLIDEAN DISTANCE] {euclidean_dist:.6f}")
            print(f"📊 [SIMILARITY] {similarity:.2%}")
            print(f"🎯 [RESULT] Match: {is_match}")
            
            if is_match:
                print("✅ [SUCCESS] Gestures match!")
            else:
                print("❌ [FAILED] Gestures do not match")
            
            print("=" * 60 + "\n")
            
            return is_match, similarity, distance
            
        except Exception as e:
            print(f"❌ [ERROR] Verification failed: {str(e)}")
            print("=" * 60 + "\n")
            return False, 0.0, 1.0

    @staticmethod
    def serialize_features(features):
        """Convert features to string for database"""
        return json.dumps(features.tolist())

    @staticmethod
    def deserialize_features(features_str):
        """Convert string back to numpy array"""
        return np.array(json.loads(features_str))

    @staticmethod
    def delete_user_gestures(user_id):
        """Delete all gesture files for a user"""
        deleted = 0
        for file_path in GESTURE_STORAGE_DIR.glob(f"user_{user_id}_*"):
            try:
                os.remove(file_path)
                deleted += 1
            except Exception:
                continue
        return deleted

# Create singleton instance
gesture_service = AdvancedGestureService()

# Service initialization
print("\n" + "=" * 60)
print("🚀 [INIT] Gesture Recognition Service Initialized")
print(f"📁 [STORAGE] {GESTURE_STORAGE_DIR.absolute()}")
print(f"🔧 [CONFIG] Threshold: {AdvancedGestureService.SIMILARITY_THRESHOLD}")
print(f"📊 [CONFIG] Points: {AdvancedGestureService.MIN_POINTS}-{AdvancedGestureService.MAX_POINTS}")
print("=" * 60 + "\n")
def get_gesture_service():
    """Get the singleton gesture service instance"""
    return gesture_service