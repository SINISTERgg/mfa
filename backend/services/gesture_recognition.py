
import numpy as np
import json
from datetime import datetime
from pathlib import Path
import os
import hashlib


# Storage directory
GESTURE_STORAGE_DIR = Path("C:/Hoysala/Projects/mfa-authentication-system/backend/stored_gesture_data")
GESTURE_STORAGE_DIR.mkdir(parents=True, exist_ok=True)


class AdvancedGestureService:
    """Advanced gesture recognition with BALANCED motion pattern analysis (~90%)"""
    
    SIMILARITY_THRESHOLD = 0.88  # 88% similarity required (BALANCED ~90%)
    MIN_POINTS = 15  # Minimum data points in gesture
    MAX_POINTS = 1000  # Maximum data points
    FEATURE_SIZE = 200  # Fixed feature vector size


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
        """Extract comprehensive features from gesture data with BALANCED analysis"""
        print("\n" + "=" * 60)
        print("✋ [EXTRACT] Starting BALANCED gesture feature extraction")
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
            print("🔍 [FEATURES] Extracting BALANCED gesture features...")
            features = AdvancedGestureService._extract_comprehensive_features(
                x_coords, y_coords, timestamps, gesture_data
            )
            
            print(f"✅ [SUCCESS] Extracted {len(features)} features")
            print(f"📈 [STATS] Mean: {np.mean(features):.4f}, Std: {np.std(features):.4f}")
            print(f"📊 [NORM] L2 Norm: {np.linalg.norm(features):.4f}")
            
            # Save pattern if requested
            if save_pattern and user_id and username:
                saved_pattern_path, _ = AdvancedGestureService.save_gesture_pattern(
                    gesture_data, user_id, username
                )
            
            print("=" * 60 + "\n")
            return features, None, saved_pattern_path
            
        except Exception as e:
            print(f"❌ [ERROR] {str(e)}")
            import traceback
            traceback.print_exc()
            print("=" * 60 + "\n")
            return None, f"Gesture processing error: {e}", None


    @staticmethod
    def _extract_comprehensive_features(x_coords, y_coords, timestamps, gesture_data):
        """Extract comprehensive features with MULTIPLE analysis methods"""
        features = []
        
        # === 1. PATH GEOMETRY FEATURES ===
        
        # Path segments
        distances = np.sqrt(np.diff(x_coords)**2 + np.diff(y_coords)**2)
        total_length = np.sum(distances)
        features.append(total_length)
        
        # Average segment length
        avg_segment = np.mean(distances) if len(distances) > 0 else 0
        features.append(avg_segment)
        
        # Segment variance
        segment_var = np.var(distances) if len(distances) > 0 else 0
        features.append(segment_var)
        
        # === 2. BOUNDING BOX FEATURES ===
        
        x_min, x_max = np.min(x_coords), np.max(x_coords)
        y_min, y_max = np.min(y_coords), np.max(y_coords)
        width = x_max - x_min
        height = y_max - y_min
        
        features.extend([width, height, x_min, x_max, y_min, y_max])
        
        # Aspect ratio
        aspect_ratio = height / (width + 1e-10)
        features.append(aspect_ratio)
        
        # Diagonal length
        diagonal = np.sqrt(width**2 + height**2)
        features.append(diagonal)
        
        # === 3. CENTROID & MOMENTS ===
        
        centroid_x = np.mean(x_coords)
        centroid_y = np.mean(y_coords)
        features.extend([centroid_x, centroid_y])
        
        # Distance from centroid (for each quartile)
        distances_from_centroid = np.sqrt((x_coords - centroid_x)**2 + (y_coords - centroid_y)**2)
        features.extend([
            np.min(distances_from_centroid),
            np.percentile(distances_from_centroid, 25),
            np.median(distances_from_centroid),
            np.percentile(distances_from_centroid, 75),
            np.max(distances_from_centroid)
        ])
        
        # === 4. DIRECTIONAL FEATURES ===
        
        angles = np.arctan2(np.diff(y_coords), np.diff(x_coords))
        
        # Angle statistics
        if len(angles) > 0:
            features.extend([
                np.mean(angles),
                np.std(angles),
                np.min(angles),
                np.max(angles)
            ])
            
            # Direction changes (curvature)
            angle_changes = np.abs(np.diff(angles))
            significant_changes = np.sum(angle_changes > np.pi/4)
            features.append(significant_changes)
            
            # Total curvature
            total_curvature = np.sum(angle_changes)
            features.append(total_curvature)
        else:
            features.extend([0, 0, 0, 0, 0, 0])
        
        # === 5. VELOCITY & ACCELERATION ===
        
        if len(timestamps) == len(x_coords):
            time_diffs = np.diff(timestamps)
            velocities = distances / (time_diffs + 1e-10)
            
            features.extend([
                np.mean(velocities),
                np.std(velocities),
                np.min(velocities),
                np.max(velocities),
                np.median(velocities)
            ])
            
            # Acceleration
            if len(velocities) > 1:
                accelerations = np.diff(velocities)
                features.extend([
                    np.mean(np.abs(accelerations)),
                    np.std(accelerations),
                    np.max(np.abs(accelerations))
                ])
            else:
                features.extend([0, 0, 0])
        else:
            features.extend([0, 0, 0, 0, 0, 0, 0, 0])
        
        # === 6. HASH-BASED FINGERPRINT ===
        
        # Create deterministic hash from coordinates
        coord_string = ''.join([f"{x:.2f},{y:.2f};" for x, y in zip(x_coords[::2], y_coords[::2])])
        coord_hash = hashlib.sha256(coord_string.encode()).digest()
        hash_features = np.frombuffer(coord_hash[:32], dtype=np.uint8).astype(float) / 255.0
        features.extend(hash_features.tolist())
        
        # === 7. NORMALIZED SAMPLED POINTS (20 samples) ===
        
        n_samples = 20
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
        
        # === 8. SHAPE COMPLEXITY ===
        
        # Number of local extrema (peaks and valleys)
        x_peaks = len([i for i in range(1, len(x_coords)-1) 
                       if x_coords[i] > x_coords[i-1] and x_coords[i] > x_coords[i+1]])
        y_peaks = len([i for i in range(1, len(y_coords)-1) 
                       if y_coords[i] > y_coords[i-1] and y_coords[i] > y_coords[i+1]])
        
        features.extend([x_peaks, y_peaks])
        
        # === 9. START & END POINT ANALYSIS ===
        
        start_x, start_y = x_coords[0], y_coords[0]
        end_x, end_y = x_coords[-1], y_coords[-1]
        
        features.extend([start_x, start_y, end_x, end_y])
        
        # Distance from start to end (straight line)
        start_end_distance = np.sqrt((end_x - start_x)**2 + (end_y - start_y)**2)
        features.append(start_end_distance)
        
        # Ratio of path length to start-end distance (straightness)
        straightness = start_end_distance / (total_length + 1e-10)
        features.append(straightness)
        
        # === 10. STATISTICAL DISTRIBUTIONS ===
        
        # X and Y coordinate distributions
        features.extend([
            np.std(x_coords),
            np.std(y_coords),
            np.var(x_coords),
            np.var(y_coords)
        ])
        
        # Convert to numpy array
        features = np.array(features)
        
        # Ensure consistent size
        if len(features) < AdvancedGestureService.FEATURE_SIZE:
            features = np.pad(features, (0, AdvancedGestureService.FEATURE_SIZE - len(features)))
        else:
            features = features[:AdvancedGestureService.FEATURE_SIZE]
        
        # Normalize
        feature_norm = np.linalg.norm(features)
        if feature_norm > 0:
            features = features / feature_norm
        
        return features


    @staticmethod
    def verify_gestures(known_features, test_features, threshold=None):
        """Verify if two gestures match with BALANCED multi-method comparison (~90%)"""
        print("\n" + "=" * 60)
        print("🔐 [VERIFY] Starting BALANCED gesture verification (~90%)")
        
        if threshold is None:
            threshold = AdvancedGestureService.SIMILARITY_THRESHOLD
        
        print(f"🎯 [THRESHOLD] {threshold:.2%}")
        
        try:
            # Ensure same dimensions
            if len(known_features) != len(test_features):
                print(f"⚠️ [WARNING] Feature dimension mismatch: {len(known_features)} vs {len(test_features)}")
                return False, 0.0, 1.0
            
            # Method 1: Cosine Similarity (normalized dot product)
            dot_product = np.dot(known_features, test_features)
            norm_known = np.linalg.norm(known_features)
            norm_test = np.linalg.norm(test_features)
            cosine_similarity = dot_product / (norm_known * norm_test + 1e-10)
            
            # Method 2: Euclidean Distance
            euclidean_dist = np.linalg.norm(known_features - test_features)
            euclidean_similarity = 1 / (1 + euclidean_dist)
            
            # Method 3: Correlation Coefficient
            correlation = np.corrcoef(known_features, test_features)[0, 1]
            correlation_similarity = (correlation + 1) / 2  # Scale to [0, 1]
            
            # Method 4: Manhattan Distance
            manhattan_dist = np.sum(np.abs(known_features - test_features))
            manhattan_similarity = 1 / (1 + manhattan_dist)
            
            # Combined similarity (weighted average)
            similarity = (
                0.40 * cosine_similarity +
                0.25 * euclidean_similarity +
                0.25 * correlation_similarity +
                0.10 * manhattan_similarity
            )
            
            # Calculate distance
            distance = 1 - similarity
            
            # Check if match
            is_match = similarity >= threshold
            
            print(f"📏 [COSINE SIMILARITY] {cosine_similarity:.6f}")
            print(f"📏 [EUCLIDEAN SIMILARITY] {euclidean_similarity:.6f}")
            print(f"📏 [CORRELATION SIMILARITY] {correlation_similarity:.6f}")
            print(f"📏 [MANHATTAN SIMILARITY] {manhattan_similarity:.6f}")
            print(f"📊 [COMBINED SIMILARITY] {similarity:.2%}")
            print(f"📏 [DISTANCE] {distance:.6f}")
            print(f"🎯 [RESULT] Match: {is_match}")
            
            if is_match:
                print(f"✅ [SUCCESS] Gestures match! (confidence: {similarity:.2%})")
            else:
                print(f"❌ [FAILED] Gestures do not match (similarity: {similarity:.2%} < threshold: {threshold:.2%})")
            
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
print(f"🔐 [MODE] BALANCED VERIFICATION (~90% Security)")
print(f"📁 [STORAGE] {GESTURE_STORAGE_DIR.absolute()}")
print(f"🔧 [CONFIG] Threshold: {AdvancedGestureService.SIMILARITY_THRESHOLD:.2%} (BALANCED)")
print(f"📊 [CONFIG] Points: {AdvancedGestureService.MIN_POINTS}-{AdvancedGestureService.MAX_POINTS}")
print(f"📏 [CONFIG] Feature Size: {AdvancedGestureService.FEATURE_SIZE}")
print("=" * 60 + "\n")
