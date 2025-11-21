"""
Advanced Keystroke Dynamics Authentication Service - STRICT VERIFICATION MODE
Using statistical analysis and machine learning for typing pattern recognition
Only enrolled keystroke patterns pass authentication
"""
import numpy as np
import json
from datetime import datetime
from typing import List, Dict, Tuple
from scipy import stats
from sklearn.preprocessing import StandardScaler
from pathlib import Path
import os

# Storage directory for keystroke patterns
KEYSTROKE_STORAGE_DIR = Path("C:/Hoysala/Projects/mfa-authentication-system/backend/stored_keystroke_data")
KEYSTROKE_STORAGE_DIR.mkdir(parents=True, exist_ok=True)

class KeystrokeDynamicsAnalyzer:
    """Advanced keystroke dynamics authentication using statistical analysis with STRICT verification"""
    
    # ✅ STRICT THRESHOLDS
    SIMILARITY_THRESHOLD = 0.60  # Distance must be < 0.60 (STRICT)
    MIN_CONFIDENCE = 65.0  # Minimum 65% confidence
    MIN_SAMPLES = 3  # Minimum samples for enrollment
    RECOMMENDED_SAMPLES = 5  # Recommended samples for best accuracy
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.threshold = self.SIMILARITY_THRESHOLD
        print("\n" + "=" * 60)
        print("⌨️  [INIT] Keystroke Dynamics Analyzer Initialized")
        print(f"🔧 [CONFIG] Similarity Threshold: {self.SIMILARITY_THRESHOLD} (STRICT)")
        print(f"🔧 [CONFIG] Min Confidence: {self.MIN_CONFIDENCE}%")
        print(f"🔧 [CONFIG] Min Samples: {self.MIN_SAMPLES}")
        print(f"🔧 [CONFIG] Recommended Samples: {self.RECOMMENDED_SAMPLES}")
        print("=" * 60 + "\n")
    
    @staticmethod
    def save_keystroke_pattern(pattern_data: Dict, user_id: int, username: str) -> Tuple[str, str]:
        """Save keystroke pattern to storage directory"""
        try:
            print(f"\n💾 [SAVE] Saving keystroke pattern for user_id={user_id}, username={username}")
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"user_{user_id}_{username}_{timestamp}_keystroke.json"
            file_path = KEYSTROKE_STORAGE_DIR / filename
            
            with open(file_path, 'w') as f:
                json.dump(pattern_data, f, indent=2)
            
            print(f"✅ [SAVED] Keystroke pattern saved: {file_path}")
            print(f"📏 [SIZE] {os.path.getsize(file_path)} bytes\n")
            
            return str(file_path), None
            
        except Exception as e:
            print(f"❌ [ERROR] Save failed: {str(e)}\n")
            return None, str(e)
    
    def extract_features(self, keystroke_data: Dict, log_details: bool = True) -> np.ndarray:
        """
        Extract statistical features from keystroke data with detailed logging
        
        Features extracted:
        - Dwell times (key hold duration)
        - Flight times (time between keys)
        - Typing speed and rhythm
        - Pressure variations (from hold time)
        """
        if log_details:
            print("\n🔍 [EXTRACT] Extracting keystroke features...")
        
        timings = keystroke_data.get('timings', [])
        
        if not timings or len(timings) < 3:
            print(f"❌ [ERROR] Insufficient keystroke data: {len(timings)} timings")
            raise ValueError("Insufficient keystroke data. Need at least 3 keystrokes.")
        
        if log_details:
            print(f"📊 [TIMINGS] {len(timings)} keystroke events")
        
        # Extract dwell times (how long each key is held)
        dwell_times = [t['holdTime'] for t in timings if 'holdTime' in t]
        
        # Extract flight times (time between key releases)
        flight_times = [t['flightTime'] for t in timings if 'flightTime' in t]
        
        if log_details:
            print(f"⏱️  [DWELL] {len(dwell_times)} dwell times")
            print(f"✈️  [FLIGHT] {len(flight_times)} flight times")
        
        # Calculate statistical features
        features = []
        
        # === 1. DWELL TIME FEATURES ===
        if dwell_times:
            dwell_features = [
                np.mean(dwell_times),
                np.std(dwell_times),
                np.median(dwell_times),
                np.min(dwell_times),
                np.max(dwell_times),
            ]
            features.extend(dwell_features)
            
            if log_details:
                print(f"📈 [DWELL STATS] Mean: {dwell_features[0]:.2f}ms, Std: {dwell_features[1]:.2f}ms")
        else:
            features.extend([0, 0, 0, 0, 0])
        
        # === 2. FLIGHT TIME FEATURES ===
        if flight_times:
            flight_features = [
                np.mean(flight_times),
                np.std(flight_times),
                np.median(flight_times),
                np.min(flight_times),
                np.max(flight_times),
            ]
            features.extend(flight_features)
            
            if log_details:
                print(f"📈 [FLIGHT STATS] Mean: {flight_features[0]:.2f}ms, Std: {flight_features[1]:.2f}ms")
        else:
            features.extend([0, 0, 0, 0, 0])
        
        # === 3. TYPING RHYTHM FEATURES ===
        if len(timings) > 1:
            # Calculate intervals between consecutive keystrokes
            intervals = []
            for i in range(len(timings) - 1):
                interval = timings[i + 1]['timestamp'] - timings[i]['timestamp']
                intervals.append(interval)
            
            # Calculate typing speed (keys per second)
            total_duration = timings[-1]['timestamp'] - timings[0]['timestamp']
            typing_speed = len(intervals) / (total_duration / 1000) if total_duration > 0 else 0
            
            rhythm_features = [
                np.mean(intervals),
                np.std(intervals),
                typing_speed
            ]
            features.extend(rhythm_features)
            
            if log_details:
                print(f"⚡ [RHYTHM] Typing speed: {typing_speed:.2f} keys/sec")
                print(f"📈 [INTERVALS] Mean: {rhythm_features[0]:.2f}ms, Std: {rhythm_features[1]:.2f}ms")
        else:
            features.extend([0, 0, 0])
        
        feature_array = np.array(features)
        
        if log_details:
            print(f"✅ [SUCCESS] Extracted {len(feature_array)} features")
            print(f"📊 [STATS] Mean: {np.mean(feature_array):.4f}, Std: {np.std(feature_array):.4f}")
        
        return feature_array
    
    def enroll_pattern(self, samples: List[Dict], user_id: int = None, username: str = None) -> Dict:
        """
        Create enrollment profile from multiple keystroke samples with detailed logging
        
        Args:
            samples: List of keystroke data dictionaries (3-5 samples)
            user_id: User ID for storage
            username: Username for storage
        
        Returns:
            Enrollment profile with statistics
        """
        print("\n" + "=" * 60)
        print("⌨️  [ENROLL] Starting keystroke pattern enrollment")
        print(f"👤 [USER] user_id={user_id}, username={username}")
        print(f"📊 [SAMPLES] {len(samples)} typing samples provided")
        
        start_time = datetime.now()
        
        # Validate sample count
        if len(samples) < self.MIN_SAMPLES:
            print(f"❌ [ERROR] Insufficient samples: {len(samples)} < {self.MIN_SAMPLES}")
            raise ValueError(f"Need at least {self.MIN_SAMPLES} samples for enrollment")
        
        if len(samples) < self.RECOMMENDED_SAMPLES:
            print(f"⚠️  [WARNING] Less than recommended samples ({len(samples)} < {self.RECOMMENDED_SAMPLES})")
        
        # Extract features from all samples
        print("\n🔍 [EXTRACT] Extracting features from all samples...")
        feature_vectors = []
        
        for i, sample in enumerate(samples):
            print(f"\n📝 [SAMPLE {i+1}/{len(samples)}]")
            try:
                features = self.extract_features(sample, log_details=True)
                feature_vectors.append(features)
            except Exception as e:
                print(f"❌ [ERROR] Sample {i+1} failed: {str(e)}")
                raise
        
        feature_matrix = np.array(feature_vectors)
        
        print("\n📊 [ANALYSIS] Computing enrollment statistics...")
        
        # Calculate mean and standard deviation for each feature
        mean_features = np.mean(feature_matrix, axis=0)
        std_features = np.std(feature_matrix, axis=0)
        
        print(f"📈 [MEAN FEATURES] {mean_features[:5]}... (showing first 5)")
        print(f"📈 [STD FEATURES] {std_features[:5]}... (showing first 5)")
        
        # Calculate consistency score (lower std = more consistent)
        consistency_score = 1.0 - np.mean(std_features / (mean_features + 1e-6))
        consistency_score = max(0, min(1, consistency_score))
        
        print(f"📊 [CONSISTENCY] {consistency_score:.2%}")
        
        # Build enrollment profile
        profile = {
            'mean_features': mean_features.tolist(),
            'std_features': std_features.tolist(),
            'num_samples': len(samples),
            'consistency_score': float(consistency_score),
            'enrolled_at': datetime.utcnow().isoformat(),
            'user_id': user_id,
            'username': username
        }
        
        # Save pattern to storage
        if user_id and username:
            saved_path, error = self.save_keystroke_pattern(profile, user_id, username)
        
        duration = (datetime.now() - start_time).total_seconds()
        
        print(f"\n✅ [SUCCESS] Enrollment completed in {duration:.2f}s")
        print(f"📊 [PROFILE] {len(samples)} samples, consistency: {consistency_score:.2%}")
        print("=" * 60 + "\n")
        
        return profile
    
    def verify_pattern(self, enrolled_profile: Dict, sample: Dict) -> Tuple[bool, float]:
        """
        Verify a keystroke sample against enrolled profile with STRICT validation
        
        Args:
            enrolled_profile: User's enrolled keystroke profile
            sample: New keystroke sample to verify
        
        Returns:
            (verified: bool, confidence: float)
        """
        print("\n" + "=" * 60)
        print("🔐 [VERIFY] Starting STRICT keystroke verification")
        
        start_time = datetime.now()
        
        try:
            # Extract features from sample
            print("🔍 [EXTRACT] Extracting features from login sample...")
            sample_features = self.extract_features(sample, log_details=True)
            
            # Get enrolled features
            print("\n📦 [LOAD] Loading enrolled profile...")
            mean_features = np.array(enrolled_profile['mean_features'])
            std_features = np.array(enrolled_profile['std_features'])
            
            print(f"✅ [LOADED] Enrolled profile ({len(mean_features)} features)")
            print(f"📊 [ENROLLED] Consistency: {enrolled_profile.get('consistency_score', 0):.2%}")
            
            # Calculate Mahalanobis distance (normalized distance)
            print("\n📏 [DISTANCE] Calculating Mahalanobis distance...")
            diff = sample_features - mean_features
            normalized_diff = diff / (std_features + 1e-6)
            distance = np.sqrt(np.mean(normalized_diff ** 2))
            
            print(f"📏 [DISTANCE] {distance:.6f}")
            
            # Calculate confidence (inverse of distance, normalized to 0-100%)
            confidence = (1.0 / (1.0 + distance)) * 100
            
            print(f"📊 [CONFIDENCE] {confidence:.2f}%")
            
            # ✅ STRICT DECISION: Both criteria must be met
            criterion_1 = distance < self.threshold
            criterion_2 = confidence >= self.MIN_CONFIDENCE
            
            verified = criterion_1 and criterion_2
            
            duration = (datetime.now() - start_time).total_seconds()
            
            print(f"\n🎯 [CRITERIA]")
            print(f"   Distance < {self.threshold}: {distance:.4f} {'✅' if criterion_1 else '❌'}")
            print(f"   Confidence >= {self.MIN_CONFIDENCE}%: {confidence:.2f}% {'✅' if criterion_2 else '❌'}")
            print(f"   Timing: {duration:.4f}s")
            
            print(f"\n🎯 [DECISION] Match: {verified}")
            
            if verified:
                print(f"✅ [SUCCESS] Keystroke pattern matches! (confidence: {confidence:.2f}%)")
            else:
                print(f"❌ [FAILED] Keystroke pattern does NOT match")
                if not criterion_1:
                    print(f"   ❌ Distance too high: {distance:.4f} >= {self.threshold}")
                if not criterion_2:
                    print(f"   ❌ Confidence too low: {confidence:.2f}% < {self.MIN_CONFIDENCE}%")
            
            print("=" * 60 + "\n")
            
            return verified, float(confidence)
            
        except Exception as e:
            print(f"❌ [ERROR] Verification failed: {str(e)}")
            import traceback
            traceback.print_exc()
            print("=" * 60 + "\n")
            return False, 0.0
    
    def calculate_pattern_strength(self, samples: List[Dict]) -> Dict:
        """
        Calculate the strength/quality of keystroke patterns with detailed analysis
        
        Returns:
            Dictionary with strength metrics and recommendations
        """
        print("\n" + "=" * 60)
        print("📊 [ANALYZE] Analyzing keystroke pattern strength")
        print(f"📝 [SAMPLES] {len(samples)} samples provided")
        
        if len(samples) < self.MIN_SAMPLES:
            print(f"❌ [ERROR] Insufficient samples: {len(samples)} < {self.MIN_SAMPLES}")
            result = {
                'strength': 'weak',
                'score': 0.0,
                'consistency': 0.0,
                'num_samples': len(samples),
                'recommendations': [f'Collect at least {self.MIN_SAMPLES} samples']
            }
            print("=" * 60 + "\n")
            return result
        
        # Extract features from all samples
        feature_vectors = []
        for i, sample in enumerate(samples):
            try:
                features = self.extract_features(sample, log_details=False)
                feature_vectors.append(features)
            except Exception as e:
                print(f"⚠️  [WARNING] Sample {i+1} skipped: {str(e)}")
        
        if len(feature_vectors) < self.MIN_SAMPLES:
            result = {
                'strength': 'weak',
                'score': 0.0,
                'consistency': 0.0,
                'num_samples': len(feature_vectors),
                'recommendations': ['Some samples failed processing']
            }
            print("=" * 60 + "\n")
            return result
        
        feature_matrix = np.array(feature_vectors)
        
        print(f"✅ [PROCESSED] {len(feature_vectors)} valid samples")
        
        # Calculate metrics
        std_features = np.std(feature_matrix, axis=0)
        mean_features = np.mean(feature_matrix, axis=0)
        
        # Consistency: lower std relative to mean is better
        consistency = 1.0 - np.mean(std_features / (mean_features + 1e-6))
        consistency = max(0, min(1, consistency))
        
        print(f"📊 [CONSISTENCY] {consistency:.2%}")
        
        # Calculate overall strength
        sample_factor = min(len(samples) / self.RECOMMENDED_SAMPLES, 1.0)
        overall_score = (consistency * 0.7) + (sample_factor * 0.3)
        
        print(f"📈 [SAMPLE FACTOR] {sample_factor:.2%}")
        print(f"📊 [OVERALL SCORE] {overall_score:.2%}")
        
        # Determine strength category
        if overall_score >= 0.8:
            strength = 'strong'
            strength_emoji = '🟢'
        elif overall_score >= 0.6:
            strength = 'good'
            strength_emoji = '🟡'
        elif overall_score >= 0.4:
            strength = 'moderate'
            strength_emoji = '🟠'
        else:
            strength = 'weak'
            strength_emoji = '🔴'
        
        print(f"\n{strength_emoji} [STRENGTH] {strength.upper()} ({overall_score:.2%})")
        
        # Generate recommendations
        recommendations = []
        if len(samples) < self.RECOMMENDED_SAMPLES:
            recommendations.append(f'Add more samples (current: {len(samples)}, recommended: {self.RECOMMENDED_SAMPLES})')
        if consistency < 0.6:
            recommendations.append('Try to type more consistently - same speed and rhythm')
        if consistency >= 0.8:
            recommendations.append('Excellent typing consistency!')
        
        if recommendations:
            print("\n💡 [RECOMMENDATIONS]")
            for rec in recommendations:
                print(f"   • {rec}")
        
        result = {
            'strength': strength,
            'score': float(overall_score),
            'consistency': float(consistency),
            'num_samples': len(samples),
            'recommendations': recommendations
        }
        
        print("=" * 60 + "\n")
        
        return result

# ===========================
# GLOBAL ANALYZER INSTANCE
# ===========================

keystroke_analyzer = KeystrokeDynamicsAnalyzer()

# ===========================
# CONVENIENCE FUNCTIONS
# ===========================

def enroll_keystroke_pattern(samples_data: List[Dict], user_id: int = None, username: str = None) -> Dict:
    """
    Enroll keystroke pattern from multiple samples
    
    Args:
        samples_data: List of keystroke sample dictionaries
        user_id: User ID for storage
        username: Username for storage
    
    Returns:
        Enrollment profile
    """
    return keystroke_analyzer.enroll_pattern(samples_data, user_id, username)

def verify_keystroke_pattern(enrolled_profile: Dict, sample_data: Dict) -> Tuple[bool, float]:
    """
    Verify keystroke sample against enrolled profile
    
    Args:
        enrolled_profile: User's enrolled profile
        sample_data: New keystroke sample
    
    Returns:
        (verified, confidence)
    """
    return keystroke_analyzer.verify_pattern(enrolled_profile, sample_data)

def analyze_pattern_strength(samples_data: List[Dict]) -> Dict:
    """
    Analyze the strength of keystroke patterns
    
    Args:
        samples_data: List of keystroke samples
    
    Returns:
        Strength analysis dictionary
    """
    return keystroke_analyzer.calculate_pattern_strength(samples_data)

# ===========================
# SERVICE INITIALIZATION
# ===========================

print("\n" + "=" * 60)
print("🚀 [INIT] Keystroke Dynamics Service Initialized (BALANCED MODE)")
print(f"📁 [STORAGE] {KEYSTROKE_STORAGE_DIR.absolute()}")
print(f"🔧 [CONFIG] Similarity Threshold: {KeystrokeDynamicsAnalyzer.SIMILARITY_THRESHOLD} (BALANCED)")
print(f"🔧 [CONFIG] Min Confidence: {KeystrokeDynamicsAnalyzer.MIN_CONFIDENCE}%")
print(f"🔧 [CONFIG] Min Samples: {KeystrokeDynamicsAnalyzer.MIN_SAMPLES}")
print(f"🔧 [CONFIG] Recommended Samples: {KeystrokeDynamicsAnalyzer.RECOMMENDED_SAMPLES}")
print("=" * 60 + "\n")
