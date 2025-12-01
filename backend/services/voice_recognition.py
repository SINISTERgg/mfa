import base64
import hashlib
import io
import json
import os
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
from pydub import AudioSegment   # requires ffmpeg installed

# -------------------------------------------------------------------
# Configuration & enums
# -------------------------------------------------------------------

VOICE_STORAGE_DIR = Path(
    "C:/Hoysala/Projects/mfa-authentication-system/backend/stored_voice_data"
)
VOICE_STORAGE_DIR.mkdir(parents=True, exist_ok=True)


class SecurityProfile(str, Enum):
    RELAXED = "RELAXED"      # ~80%+
    BALANCED = "BALANCED"    # ~90%+
    STRICT = "STRICT"        # ~95%+


PROFILE_CONFIG = {
    SecurityProfile.RELAXED: {"threshold": 0.80, "min_bytes": 8_000},
    SecurityProfile.BALANCED: {"threshold": 0.88, "min_bytes": 10_000},
    SecurityProfile.STRICT: {"threshold": 0.93, "min_bytes": 12_000},
}

FEATURE_SIZE = 320       # extended vector (hash + stats + coarse MFCC‑like)
MAX_AUDIO_SIZE = 5_000_000
WAVE_TARGET_SR = 16_000  # 16 kHz mono is standard for speaker tasks


@dataclass
class VerificationResult:
    is_match: bool
    similarity: float
    distance: float
    profile: SecurityProfile
    threshold: float
    quality_score: float
    flags: list[str]


# -------------------------------------------------------------------
# Audio decoding: base64 WebM/Opus → mono PCM array
# -------------------------------------------------------------------

class AudioDecoder:
    @staticmethod
    def decode_base64_webm_to_waveform(base64_audio: str) -> Tuple[np.ndarray, int]:
        """Decode base64 audio/webm;codecs=opus → mono PCM float32, target 16 kHz."""
        if "base64," in base64_audio:
            base64_audio = base64_audio.split("base64,", 1)[1]

        raw_bytes = base64.b64decode(base64_audio)
        size = len(raw_bytes)

        if size == 0:
            raise ValueError("Empty audio payload")

        # Decode WebM/Opus using pydub + ffmpeg
        audio = AudioSegment.from_file(io.BytesIO(raw_bytes), format="webm")
        audio = audio.set_channels(1).set_frame_rate(WAVE_TARGET_SR)

        samples = np.array(audio.get_array_of_samples()).astype(np.float32)
        # Normalize to [-1, 1]
        samples /= np.iinfo(audio.array_type).max

        return samples, size


# -------------------------------------------------------------------
# Feature extraction
# -------------------------------------------------------------------

class FeatureExtractor:
    FEATURE_SIZE = FEATURE_SIZE

    @staticmethod
    def _hash_fingerprints(audio_bytes: bytes) -> np.ndarray:
        """Three SHA‑256 segments + histogram + simple global stats (byte space)."""
        n = len(audio_bytes)
        arr = np.frombuffer(audio_bytes, dtype=np.uint8).astype(np.float32)

        feats = []

        # Segments (front, mid, end)
        seg_len = min(2000, n // 3 or 1)

        seg1 = audio_bytes[:seg_len]
        seg2_start = max(0, n // 2 - seg_len // 2)
        seg2 = audio_bytes[seg2_start: seg2_start + seg_len]
        seg3 = audio_bytes[-seg_len:]

        for seg in (seg1, seg2, seg3):
            h = hashlib.sha256(seg).digest()
            h_arr = np.frombuffer(h, dtype=np.uint8).astype(np.float32) / 255.0
            feats.append(h_arr)

        # Byte histogram
        hist, _ = np.histogram(arr, bins=32, range=(0, 256))
        hist = hist.astype(np.float32) / (n + 1e-9)
        feats.append(hist)

        # Global stats
        feats.append(np.array([arr.mean(), arr.std(), arr.var(),
                               float(arr.max() - arr.min())], dtype=np.float32))

        return np.concatenate(feats, axis=0)

    @staticmethod
    def _waveform_stats(wave: np.ndarray) -> np.ndarray:
        """Cheap signal‑domain stats (duration, energy, clipping, spectral tilt proxy)."""
        if len(wave) == 0:
            return np.zeros(16, dtype=np.float32)

        # Basic energy & dynamics
        mean = float(np.mean(wave))
        std = float(np.std(wave))
        rms = float(np.sqrt(np.mean(wave ** 2)))
        peak = float(np.max(np.abs(wave)))
        dynamic_range = float(peak - np.min(np.abs(wave)))

        # Clipping ratio
        clip_thr = 0.98
        clipping_ratio = float(np.mean(np.abs(wave) > clip_thr))

        # Coarse “spectral tilt”: low vs high band energy
        n = len(wave)
        first_half = wave[: n // 2]
        second_half = wave[n // 2:]

        low_rms = float(np.sqrt(np.mean(first_half ** 2)))
        high_rms = float(np.sqrt(np.mean(second_half ** 2)))
        tilt = float(low_rms - high_rms)

        # Frame‑level stats
        frame_len = int(0.025 * WAVE_TARGET_SR)  # 25 ms
        hop = int(0.010 * WAVE_TARGET_SR)        # 10 ms
        if frame_len <= 0 or hop <= 0:
            return np.zeros(16, dtype=np.float32)

        energies = []
        for i in range(0, n - frame_len, hop):
            frame = wave[i: i + frame_len]
            energies.append(np.sqrt(np.mean(frame ** 2)))
        energies = np.array(energies, dtype=np.float32) if len(energies) else np.zeros(1, dtype=np.float32)

        feats = np.array([
            mean, std, rms, peak, dynamic_range,
            clipping_ratio, low_rms, high_rms, tilt,
            float(energies.mean()),
            float(energies.std()),
            float(energies.max(initial=0.0)),
            float(energies.min(initial=0.0)),
            float(len(energies)),
            float(len(wave) / WAVE_TARGET_SR),  # duration sec
            float(np.percentile(energies, 90)) if len(energies) else 0.0,
        ], dtype=np.float32)

        return feats

    @classmethod
    def extract_feature_vector(
        cls,
        base64_audio: str,
        profile: SecurityProfile = SecurityProfile.BALANCED,
    ) -> Tuple[np.ndarray, dict]:
        """
        Decode base64 WebM, build deterministic feature vector, plus quality metrics.
        """
        # Decode once to bytes for hash features
        if "base64," in base64_audio:
            raw_b64 = base64_audio.split("base64,", 1)[1]
        else:
            raw_b64 = base64_audio

        audio_bytes = base64.b64decode(raw_b64)
        byte_len = len(audio_bytes)

        # Size guards per profile
        cfg = PROFILE_CONFIG[profile]
        if byte_len < cfg["min_bytes"]:
            raise ValueError(
                f"Audio too short for {profile.value}. "
                f"Have {byte_len} bytes, need ≥ {cfg['min_bytes']}."
            )
        if byte_len > MAX_AUDIO_SIZE:
            raise ValueError(
                f"Audio too large ({byte_len} bytes). Max {MAX_AUDIO_SIZE} bytes allowed."
            )

        # Hash/domain‑agnostic features
        hash_feats = cls._hash_fingerprints(audio_bytes)

        # Decode waveform for signal‑domain stats
        waveform, _ = AudioDecoder.decode_base64_webm_to_waveform(base64_audio)
        wave_feats = cls._waveform_stats(waveform)

        # Optional coarse “FFT‑like” sample for some frequency texture
        sampled = waveform[:: max(1, len(waveform) // 64)]
        if len(sampled) > 64:
            sampled = sampled[:64]
        sampled = np.pad(sampled, (0, 64 - len(sampled)), mode="constant")
        sampled = sampled.astype(np.float32)

        feats = np.concatenate([hash_feats, wave_feats, sampled], axis=0)

        # Fix length to FEATURE_SIZE
        if len(feats) < cls.FEATURE_SIZE:
            feats = np.pad(feats, (0, cls.FEATURE_SIZE - len(feats)))
        else:
            feats = feats[: cls.FEATURE_SIZE]

        # L2 normalize
        norm = np.linalg.norm(feats)
        if norm > 0:
            feats = feats / norm

        # Quality metrics
        duration_sec = float(len(waveform) / WAVE_TARGET_SR)
        clipping_ratio = float(np.mean(np.abs(waveform) > 0.98)) if len(waveform) else 0.0
        quality = max(0.0, 1.0 - clipping_ratio) * min(1.0, duration_sec / 4.0)

        meta = {
            "byte_len": byte_len,
            "duration_sec": duration_sec,
            "clipping_ratio": clipping_ratio,
            "quality_score": quality,
        }
        return feats.astype(np.float32), meta


# -------------------------------------------------------------------
# Matching / verification
# -------------------------------------------------------------------

class VoiceMatcher:
    @staticmethod
    def _cosine(a: np.ndarray, b: np.ndarray) -> float:
        return float(
            np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9)
        )

    @staticmethod
    def _euclidean_sim(a: np.ndarray, b: np.ndarray) -> float:
        dist = float(np.linalg.norm(a - b))
        return float(1.0 / (1.0 + dist))

    @staticmethod
    def _correlation_sim(a: np.ndarray, b: np.ndarray) -> float:
        if a.ndim != 1 or b.ndim != 1 or len(a) < 2:
            return 0.5
        c = np.corrcoef(a, b)[0, 1]
        return float((c + 1.0) / 2.0)

    @classmethod
    def compare(
        cls,
        known: np.ndarray,
        probe: np.ndarray,
        profile: SecurityProfile = SecurityProfile.BALANCED,
        quality_known: float = 1.0,
        quality_probe: float = 1.0,
    ) -> VerificationResult:
        if known.shape != probe.shape:
            raise ValueError(
                f"Feature dim mismatch: {known.shape} vs {probe.shape}"
            )

        cos = cls._cosine(known, probe)
        eu = cls._euclidean_sim(known, probe)
        corr = cls._correlation_sim(known, probe)

        # Combined similarity; tune weights per profile if desired
        similarity = 0.5 * cos + 0.3 * eu + 0.2 * corr
        distance = 1.0 - similarity

        cfg = PROFILE_CONFIG[profile]
        threshold = cfg["threshold"]

        # Simple quality model: average and clamp
        avg_quality = max(0.0, min(1.0, (quality_known + quality_probe) / 2.0))
        effective_similarity = similarity * (0.5 + 0.5 * avg_quality)

        is_match = effective_similarity >= threshold

        flags = []
        if avg_quality < 0.4:
            flags.append("LOW_QUALITY_AUDIO")
        if cos < threshold - 0.15:
            flags.append("STRONG_VOICE_MISMATCH")
        if distance < 0.02 and avg_quality < 0.3:
            flags.append("POTENTIAL_REPLAY_OR_SYNTHETIC")

        return VerificationResult(
            is_match=is_match,
            similarity=float(effective_similarity),
            distance=float(distance),
            profile=profile,
            threshold=float(threshold),
            quality_score=float(avg_quality),
            flags=flags,
        )


# -------------------------------------------------------------------
# High‑level service
# -------------------------------------------------------------------

class AdvancedVoiceServiceV2:
    """Advanced, profile‑aware voice recognition service (from scratch)."""

    def __init__(self, storage_dir: Path = VOICE_STORAGE_DIR):
        self.storage_dir = storage_dir

        print("\n" + "=" * 60)
        print("🚀 [INIT] Advanced Voice Recognition Service v2")
        print(f"📁 [STORAGE] {self.storage_dir.absolute()}")
        for p, cfg in PROFILE_CONFIG.items():
            print(f"🔧 [{p.value}] threshold={cfg['threshold']:.2%}, "
                  f"min_bytes={cfg['min_bytes']}")
        print(f"📏 [CONFIG] Feature Size: {FEATURE_SIZE}")
        print("=" * 60 + "\n")

    # ---------- Storage helpers ----------

    def save_voice_sample(
        self, base64_audio: str, user_id: str, username: str
    ) -> str:
        if "base64," in base64_audio:
            base64_audio = base64_audio.split("base64,", 1)[1]

        audio_bytes = base64.b64decode(base64_audio)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"user_{user_id}_{username}_{timestamp}_voice.webm"
        path = self.storage_dir / filename
        with open(path, "wb") as f:
            f.write(audio_bytes)
        return str(path)

    @staticmethod
    def serialize_features(features: np.ndarray) -> str:
        return ",".join(map(str, features.astype(np.float32)))

    @staticmethod
    def deserialize_features(features_str: str) -> np.ndarray:
        return np.fromstring(features_str, sep=",", dtype=np.float32)

    def delete_user_audio(self, user_id: str) -> int:
        deleted = 0
        for fp in self.storage_dir.glob(f"user_{user_id}_*"):
            try:
                os.remove(fp)
                deleted += 1
            except OSError:
                continue
        return deleted

    # ---------- Public API ----------

    def extract_features(
        self,
        base64_audio: str,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        save_audio: bool = True,
        profile: SecurityProfile = SecurityProfile.BALANCED,
    ) -> Tuple[np.ndarray, dict, Optional[str]]:
        feats, meta = FeatureExtractor.extract_feature_vector(
            base64_audio, profile=profile
        )

        saved_path = None
        if save_audio and user_id and username:
            saved_path = self.save_voice_sample(base64_audio, user_id, username)

        return feats, meta, saved_path

    def verify(
        self,
        known_features: np.ndarray,
        probe_features: np.ndarray,
        known_meta: Optional[dict] = None,
        probe_meta: Optional[dict] = None,
        profile: SecurityProfile = SecurityProfile.BALANCED,
    ) -> VerificationResult:
        q_known = (known_meta or {}).get("quality_score", 1.0)
        q_probe = (probe_meta or {}).get("quality_score", 1.0)
        return VoiceMatcher.compare(
            known_features,
            probe_features,
            profile=profile,
            quality_known=q_known,
            quality_probe=q_probe,
        )


# Singleton-style instance
voice_service_v2 = AdvancedVoiceServiceV2()
def get_voice_service_v2() -> AdvancedVoiceServiceV2:
    return voice_service_v2