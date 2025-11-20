import numpy as np
import json
from datetime import datetime
from typing import List, Dict, Tuple
from scipy import stats
from sklearn.preprocessing import StandardScaler


class KeystrokeDynamicsAnalyzer:
    """Advanced keystroke dynamics authentication using statistical analysis"""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.threshold = 0.40  # Similarity threshold (lower = stricter)
    
    def extract_features(self, keystroke_data: Dict) -> np.ndarray:
        """
        Extract statistical features from keystroke data
        
        Features:
        - Dwell times (key hold duration)
        - Flight times (time between keys)
        - Typing speed
        - Rhythm patterns
        - Pressure variations (simulated from hold time)
        """
        timings = keystroke_data.get('timings', [])
        
        if not timings or len(timings) < 3:
            raise ValueError("Insufficient keystroke data")
        
        # Extract dwell times (how long each key is held)
        dwell_times = [t['holdTime'] for t in timings if 'holdTime' in t]
        
        # Extract flight times (time between key releases)
        flight_times = [t['flightTime'] for t in timings if 'flightTime' in t]
        
        # Calculate statistical features
        features = []
        
        # Dwell time features
        if dwell_times:
            features.extend([
                np.mean(dwell_times),
                np.std(dwell_times),
                np.median(dwell_times),
                np.min(dwell_times),
                np.max(dwell_times),
            ])
        else:
            features.extend([0, 0, 0, 0, 0])
        
        # Flight time features
        if flight_times:
            features.extend([
                np.mean(flight_times),
                np.std(flight_times),
                np.median(flight_times),
                np.min(flight_times),
                np.max(flight_times),
            ])
        else:
            features.extend([0, 0, 0, 0, 0])
        
        # Typing rhythm features
        if len(timings) > 1:
            # Calculate intervals between consecutive keystrokes
            intervals = []
            for i in range(len(timings) - 1):
                interval = timings[i + 1]['timestamp'] - timings[i]['timestamp']
                intervals.append(interval)
            
            features.extend([
                np.mean(intervals),
                np.std(intervals),
                len(intervals) / (timings[-1]['timestamp'] - timings[0]['timestamp']) * 1000  # keys per second
            ])
        else:
            features.extend([0, 0, 0])
        
        return np.array(features)
    
    def enroll_pattern(self, samples: List[Dict]) -> Dict:
        """
        Create enrollment profile from multiple samples
        
        Args:
            samples: List of keystroke data dictionaries (5 samples recommended)
        
        Returns:
            Enrollment profile with mean and std of features
        """
        if len(samples) < 3:
            raise ValueError("Need at least 3 samples for enrollment")
        
        # Extract features from all samples
        feature_vectors = []
        for sample in samples:
            features = self.extract_features(sample)
            feature_vectors.append(features)
        
        feature_matrix = np.array(feature_vectors)
        
        # Calculate mean and standard deviation for each feature
        mean_features = np.mean(feature_matrix, axis=0)
        std_features = np.std(feature_matrix, axis=0)
        
        # Calculate consistency score (lower std = more consistent)
        consistency_score = 1.0 - np.mean(std_features / (mean_features + 1e-6))
        consistency_score = max(0, min(1, consistency_score))
        
        profile = {
            'mean_features': mean_features.tolist(),
            'std_features': std_features.tolist(),
            'num_samples': len(samples),
            'consistency_score': float(consistency_score),
            'enrolled_at': datetime.utcnow().isoformat()
        }
        
        return profile
    
    def verify_pattern(self, enrolled_profile: Dict, sample: Dict) -> Tuple[bool, float]:
        """
        Verify a keystroke sample against enrolled profile
        
        Args:
            enrolled_profile: User's enrolled keystroke profile
            sample: New keystroke sample to verify
        
        Returns:
            (verified: bool, confidence: float)
        """
        # Extract features from sample
        sample_features = self.extract_features(sample)
        
        # Get enrolled features
        mean_features = np.array(enrolled_profile['mean_features'])
        std_features = np.array(enrolled_profile['std_features'])
        
        # Calculate Mahalanobis distance (normalized distance)
        # Add small epsilon to avoid division by zero
        diff = sample_features - mean_features
        normalized_diff = diff / (std_features + 1e-6)
        distance = np.sqrt(np.mean(normalized_diff ** 2))
        
        # Calculate confidence (inverse of distance, normalized to 0-1)
        confidence = 1.0 / (1.0 + distance)
        
        # Verify based on threshold
        verified = distance < self.threshold
        
        return verified, float(confidence)
    
    def calculate_pattern_strength(self, samples: List[Dict]) -> Dict:
        """
        Calculate the strength/quality of keystroke patterns
        
        Returns:
            Dictionary with strength metrics
        """
        if len(samples) < 3:
            return {
                'strength': 'weak',
                'score': 0.0,
                'consistency': 0.0,
                'recommendations': ['Collect at least 3 samples']
            }
        
        feature_vectors = []
        for sample in samples:
            features = self.extract_features(sample)
            feature_vectors.append(features)
        
        feature_matrix = np.array(feature_vectors)
        
        # Calculate metrics
        std_features = np.std(feature_matrix, axis=0)
        mean_features = np.mean(feature_matrix, axis=0)
        
        # Consistency: lower std relative to mean is better
        consistency = 1.0 - np.mean(std_features / (mean_features + 1e-6))
        consistency = max(0, min(1, consistency))
        
        # Calculate overall strength
        sample_factor = min(len(samples) / 5.0, 1.0)  # Ideal is 5 samples
        overall_score = (consistency * 0.7) + (sample_factor * 0.3)
        
        # Determine strength category
        if overall_score >= 0.8:
            strength = 'strong'
        elif overall_score >= 0.6:
            strength = 'good'
        elif overall_score >= 0.4:
            strength = 'moderate'
        else:
            strength = 'weak'
        
        recommendations = []
        if len(samples) < 5:
            recommendations.append('Add more samples for better accuracy')
        if consistency < 0.6:
            recommendations.append('Try to type more consistently')
        
        return {
            'strength': strength,
            'score': float(overall_score),
            'consistency': float(consistency),
            'num_samples': len(samples),
            'recommendations': recommendations
        }


# Global analyzer instance
keystroke_analyzer = KeystrokeDynamicsAnalyzer()


def enroll_keystroke_pattern(samples_data: List[Dict]) -> Dict:
    """
    Enroll keystroke pattern from multiple samples
    
    Args:
        samples_data: List of keystroke sample dictionaries
    
    Returns:
        Enrollment profile
    """
    return keystroke_analyzer.enroll_pattern(samples_data)


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
# End of file: backend/services/keystroke_service.py