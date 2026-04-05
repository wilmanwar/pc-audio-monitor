#!/usr/bin/env python3
"""
Music Genre and Type Classification Module

Two-stage pipeline:
  Stage 1 — Music vs Speech/Noise (hand-crafted signal features, no dependencies)
  Stage 2 — Genre classification:
      PRIMARY:  Essentia pretrained ONNX models (EffNet embeddings + Discogs400
                genre classifier). Requires librosa + onnxruntime + model files.
      FALLBACK: Hand-crafted heuristics used automatically if models not found.

Model files required (one-time download):

  1. discogs-effnet-bsdynamic-1.onnx  (~18 MB)
       https://essentia.upf.edu/models/feature-extractors/discogs-effnet/discogs-effnet-bsdynamic-1.onnx

  2. discogs-effnet-bsdynamic-1.json  (label file, contains the 400 class names)
       https://essentia.upf.edu/models/feature-extractors/discogs-effnet/discogs-effnet-bsdynamic-1.json

  This is the ONLY EffNet model available in ONNX format. It was trained as a
  400-class music style classifier, so its outputs are genre probabilities
  directly — no separate classifier head needed. All other variants
  (.pb files, bs64, bs512) require TensorFlow which is not available on Windows.

  The "bsdynamic" means dynamic batch size — it accepts any number of patches
  in one call, which is ideal for our use case.

Place these 2 files in the same directory as this script, or set
MODEL_DIR in your .env to point to the folder containing them.

Install dependencies:
  pip install librosa onnxruntime
"""

import os
import json
import logging
import numpy as np
from typing import Dict, Tuple, Optional, List

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Broad genre mapping: Discogs400 has very specific sub-genres like
# "Rock: Punk" or "Electronic: Techno". We collapse them into the broad
# categories your app already uses so the HA dashboard stays readable.
# ---------------------------------------------------------------------------
DISCOGS_TO_BROAD = {
    "Blues":            "Blues",
    "Brass & Military": "Classical",
    "Children's":       "Other",
    "Classical":        "Classical",
    "Electronic":       "Electronic",
    "Folk, World, & Country": "Folk/Country",
    "Funk / Soul":      "Funk/Soul",
    "Hip Hop":          "Hip-Hop",
    "Jazz":             "Jazz",
    "Latin":            "Latin",
    "Non-Music":        "Non-Music",
    "Pop":              "Pop",
    "Reggae":           "Reggae",
    "Rock":             "Rock",
    "Stage & Screen":   "Other",
}

def _top_level(discogs_label: str) -> str:
    """Extract top-level genre from a Discogs label like 'Rock---Punk'."""
    top = discogs_label.split("---")[0].strip()
    return DISCOGS_TO_BROAD.get(top, top)


# ---------------------------------------------------------------------------
# ONNX model loader — lazy, loads once, gracefully absent
# ---------------------------------------------------------------------------

class _OnnxGenreClassifier:
    """
    Wraps the Essentia discogs-effnet ONNX model for genre classification.

    Uses the music-style-classification version of the model which outputs
    400 Discogs genre probabilities directly — no separate classifier head
    needed. The two-stage pipeline (effnet embeddings -> genre_discogs400
    classifier) has no ONNX version for the classifier head; only .pb files
    exist for that. This single model approach works entirely with onnxruntime.

    Loads lazily on first call, falls back to heuristics silently if missing.
    """

    TARGET_SR  = 16000   # Model expects 16 kHz mono
    N_MELS     = 96
    HOP_LENGTH = 256
    N_FFT      = 512
    PATCH_SIZE = 128     # frames per patch (EffNet uses 128-frame patches)

    def __init__(self, model_dir: str):
        self.model_dir = model_dir
        self._session      = None
        self._labels: List[str] = []
        self._loaded = False
        self._failed = False
        self._librosa = None

    def _try_load(self) -> bool:
        if self._loaded:
            return True
        if self._failed:
            return False

        model_path  = os.path.join(self.model_dir, "discogs-effnet-bsdynamic-1.onnx")
        labels_path = os.path.join(self.model_dir, "discogs-effnet-bsdynamic-1.json")

        missing = [p for p in [model_path, labels_path]
                   if not os.path.exists(p)]
        if missing:
            logger.info(
                "Essentia ONNX genre model not found — using heuristic classifier.\n"
                f"To enable ML classification, download these 2 files into '{self.model_dir}':\n"
                "  discogs-effnet-bsdynamic-1.onnx (~18 MB)\n"
                "    https://essentia.upf.edu/models/feature-extractors/"
                "discogs-effnet/discogs-effnet-bsdynamic-1.onnx\n"
                "  discogs-effnet-bsdynamic-1.json (tiny)\n"
                "    https://essentia.upf.edu/models/feature-extractors/"
                "discogs-effnet/discogs-effnet-bsdynamic-1.json\n"
                "Then: pip install librosa onnxruntime"
            )
            self._failed = True
            return False

        try:
            import onnxruntime as ort
            opts = ort.SessionOptions()
            opts.log_severity_level = 3
            self._session = ort.InferenceSession(model_path, sess_options=opts)

            with open(labels_path) as f:
                meta = json.load(f)
            self._labels = meta.get("classes", [])

            import librosa
            self._librosa = librosa

            # Log input shape so we can verify patch dimensions at startup
            inp = self._session.get_inputs()[0]
            logger.info(
                f"Essentia EffNet genre model loaded — "
                f"{len(self._labels)} Discogs styles | "
                f"input: {inp.name} shape={inp.shape}"
            )
            self._loaded = True
            return True

        except ImportError as e:
            logger.warning(
                f"ML genre classifier unavailable ({e}). "
                "Install with: pip install librosa onnxruntime"
            )
            self._failed = True
            return False
        except Exception as e:
            logger.warning(f"Failed to load ONNX model: {e}")
            self._failed = True
            return False

    def predict(
        self, audio: np.ndarray, src_sr: int
    ) -> Optional[Tuple[str, float, str]]:
        """
        Run inference. Returns (broad_genre, confidence, detailed_label) or None.
        """
        if not self._try_load():
            return None

        try:
            librosa = self._librosa

            # 1. Resample to 16 kHz mono
            audio_f32 = audio.astype(np.float32)
            if audio_f32.ndim > 1:
                audio_f32 = np.mean(audio_f32, axis=1)
            if src_sr != self.TARGET_SR:
                audio_f32 = librosa.resample(
                    audio_f32, orig_sr=src_sr, target_sr=self.TARGET_SR)

            # Pad to at least one patch
            min_samples = self.PATCH_SIZE * self.HOP_LENGTH
            if len(audio_f32) < min_samples:
                audio_f32 = np.pad(audio_f32, (0, min_samples - len(audio_f32)))

            # 2. Mel spectrogram — Essentia EffNet parameters
            mel = librosa.feature.melspectrogram(
                y=audio_f32,
                sr=self.TARGET_SR,
                n_fft=self.N_FFT,
                hop_length=self.HOP_LENGTH,
                n_mels=self.N_MELS,
                fmax=self.TARGET_SR / 2,
                power=2.0,
            )
            # Essentia log compression
            mel = np.log10(1 + 10000 * mel).astype(np.float32)
            # mel shape: (N_MELS, time_frames)

            # 3. Slice into patches of shape (n_patches, PATCH_SIZE, N_MELS)
            #    bsdynamic accepts any batch size — pass all patches at once
            n_frames  = mel.shape[1]
            n_patches = n_frames // self.PATCH_SIZE
            if n_patches == 0:
                return None

            patches = mel[:, :n_patches * self.PATCH_SIZE]          # (96, n*128)
            patches = patches.reshape(self.N_MELS, n_patches, self.PATCH_SIZE)
            patches = patches.transpose(1, 2, 0)                     # (n, 128, 96)

            inp_name   = self._session.get_inputs()[0].name
            genre_probs = self._session.run(None, {inp_name: patches})[0]
            # genre_probs: (n_patches, 400) — average across patches
            mean_probs = np.mean(genre_probs, axis=0)  # (400,)

            # 4. Top prediction
            top_idx    = int(np.argmax(mean_probs))
            confidence = float(mean_probs[top_idx])
            detailed   = self._labels[top_idx] if top_idx < len(self._labels) else "Unknown"
            broad      = _top_level(detailed)

            logger.debug(
                f"ONNX genre: {broad} ({confidence:.2f}) [{detailed}] "
                f"from {n_patches} patches"
            )
            return broad, confidence, detailed

        except Exception as e:
            logger.warning(f"ONNX inference error: {e}", exc_info=True)
            return None


# ---------------------------------------------------------------------------
# Main classifier class
# ---------------------------------------------------------------------------

class MusicClassifier:
    """
    Classifies audio as music/non-music and identifies genre.

    Genre classification uses the Essentia pretrained ONNX pipeline when
    model files are present, and falls back to hand-crafted heuristics
    otherwise — so the app works out of the box without any extra setup.
    """

    def __init__(self, samplerate: int = 44100):
        self.samplerate = samplerate
        model_dir = os.getenv("MODEL_DIR", os.path.dirname(os.path.abspath(__file__)))
        self._onnx = _OnnxGenreClassifier(model_dir)

    # ------------------------------------------------------------------
    # Feature extraction (used by music/speech detector AND heuristic fallback)
    # ------------------------------------------------------------------

    def extract_features(self, audio_data: np.ndarray) -> Dict[str, float]:
        """Extract spectral, temporal, and harmonic features."""
        if audio_data.ndim > 1:
            audio_data = np.mean(audio_data, axis=1)
        if len(audio_data) < 1000:
            return {}

        features = {}
        try:
            chunk_size = int(self.samplerate * 0.02)  # 20 ms

            window   = np.hanning(len(audio_data))
            windowed = audio_data * window
            fft      = np.fft.rfft(windowed)
            freqs    = np.fft.rfftfreq(len(windowed), 1.0 / self.samplerate)
            magnitude    = np.abs(fft)
            total_energy = np.sum(magnitude) + 1e-10

            # Spectral entropy
            norm_mag = magnitude / total_energy
            sp_ent   = -np.sum(norm_mag[norm_mag > 0] *
                               np.log2(norm_mag[norm_mag > 0] + 1e-10))
            max_ent  = np.log2(len(magnitude))
            features['spectral_entropy'] = float(
                sp_ent / max_ent if max_ent > 0 else 0)

            features['spectral_centroid'] = float(
                np.sum(freqs * magnitude) / total_energy)

            cum_energy  = np.cumsum(magnitude)
            rolloff_idx = np.where(cum_energy >= 0.95 * total_energy)[0]
            features['spectral_rolloff'] = float(
                freqs[rolloff_idx[0]] if len(rolloff_idx) > 0 else 0)

            # Spectral flux
            fluxes, prev_mag = [], None
            for i in range(0, len(audio_data) - chunk_size, chunk_size):
                cf = np.abs(np.fft.rfft(
                    audio_data[i:i+chunk_size] * np.hanning(chunk_size)))
                if prev_mag is not None:
                    fluxes.append(float(np.sqrt(np.sum((cf - prev_mag) ** 2))))
                prev_mag = cf
            features['spectral_flux'] = float(np.mean(fluxes)) if fluxes else 0

            # ZCR
            features['zero_crossing_rate'] = float(
                np.sum(np.abs(np.diff(np.sign(audio_data)))) /
                (2 * len(audio_data)))

            features['rms_energy'] = float(np.sqrt(np.mean(audio_data ** 2)))

            # Energy stability
            energy_frames = [
                np.sqrt(np.mean(audio_data[i:i+chunk_size] ** 2))
                for i in range(0, len(audio_data) - chunk_size, chunk_size // 2)
            ]
            mean_e = float(np.mean(energy_frames)) + 1e-10
            features['energy_stability'] = float(np.std(energy_frames) / mean_e)

            # Burst ratio (speech has gaps between syllables)
            silence_thr = mean_e * 0.10
            features['burst_ratio'] = float(
                sum(1 for e in energy_frames if e < silence_thr) /
                len(energy_frames)) if energy_frames else 0.0

            # Harmonic peaks
            features['harmonic_peaks'] = float(
                np.sum(magnitude > np.mean(magnitude) * 0.5) / len(magnitude))

            # Band energies
            def band(low, high):
                mask = (freqs >= low) & (freqs < high)
                return float(np.sum(magnitude[mask]) / total_energy) if mask.any() else 0.0

            features['brightness']         = band(2000, 20000)
            features['presence']           = band(2000, 4000)
            features['bass_content']       = band(20, 250)
            features['mid_content']        = band(250, 2000)
            features['percussion_content'] = band(5000, 20000)
            features['speech_band']        = band(300, 3400)
            features['sub_bass']           = band(20, 100)

            # Spectral flatness
            mag_pos = magnitude[magnitude > 0]
            if len(mag_pos) > 1:
                geo  = np.exp(np.mean(np.log(mag_pos + 1e-10)))
                arth = np.mean(mag_pos)
                features['spectral_flatness'] = float(geo / (arth + 1e-10))
            else:
                features['spectral_flatness'] = 1.0

            # Pitch periodicity via autocorrelation
            try:
                ac_len = min(len(audio_data), 4096)
                ac = np.correlate(audio_data[:ac_len], audio_data[:ac_len], 'full')
                ac = ac[len(ac)//2:]
                ac = ac / (ac[0] + 1e-10)
                min_lag = int(self.samplerate / 1000)
                max_lag = int(self.samplerate / 50)
                features['pitch_periodicity'] = float(
                    max(0.0, np.max(ac[min_lag:max_lag]))
                    if max_lag < len(ac) else 0.0)
            except Exception:
                features['pitch_periodicity'] = 0.0

        except Exception as e:
            logger.error(f"Feature extraction error: {e}")

        return features

    # ------------------------------------------------------------------
    # Stage 1 — Music vs speech/noise
    # ------------------------------------------------------------------

    def is_music_vs_speech(self, features: Dict[str, float]) -> Tuple[bool, float]:
        """Return (is_music, confidence). Uses hand-crafted signal features."""
        if not features:
            return True, 0.5

        try:
            entropy      = features.get('spectral_entropy', 0.5)
            zcr          = features.get('zero_crossing_rate', 0.05)
            speech_band  = features.get('speech_band', 0.3)
            pitch_p      = features.get('pitch_periodicity', 0.0)
            bass         = features.get('bass_content', 0.1)
            sub_bass     = features.get('sub_bass', 0.0)
            burst_ratio  = features.get('burst_ratio', 0.0)
            flatness     = features.get('spectral_flatness', 0.5)
            harmonic_p   = features.get('harmonic_peaks', 0.1)

            # Hard veto 1: burstiness (word gaps)
            if burst_ratio > 0.30:
                conf = min(burst_ratio / 0.30, 1.0)
                logger.debug(f"Speech VETO burst={burst_ratio:.2f}")
                return False, 0.60 + 0.40 * conf

            # Hard veto 2: flat spectrum + speech-band dominance
            if flatness > 0.15 and speech_band > 0.55:
                conf = min((flatness / 0.15) * (speech_band / 0.55), 1.0)
                logger.debug(f"Speech VETO flat={flatness:.3f} sb={speech_band:.2f}")
                return False, 0.60 + 0.40 * conf

            # Scored evidence
            speech_score  = 0.0
            speech_score += 0.25 if zcr > 0.06 else (zcr / 0.06) * 0.25
            speech_score += 0.25 if speech_band > 0.60 else (speech_band / 0.60) * 0.15
            speech_score += 0.20 if entropy > 0.78 else 0.0
            speech_score += 0.15 if pitch_p < 0.15 else 0.0
            speech_score += 0.15 if bass < 0.05 else 0.0

            music_score  = 0.0
            music_score += 0.30 if pitch_p > 0.20 else (pitch_p / 0.20) * 0.30
            music_score += 0.20 if sub_bass > 0.02 else 0.0
            music_score += 0.20 if bass > 0.08 else 0.0
            music_score += 0.15 if flatness < 0.08 else 0.0
            music_score += 0.15 if entropy < 0.75 else 0.0

            if speech_score >= 0.60:
                is_music, confidence = False, speech_score
            elif music_score >= 0.55:
                is_music, confidence = True, music_score
            elif music_score > speech_score:
                is_music, confidence = True, music_score
            else:
                is_music, confidence = False, speech_score

            logger.debug(
                f"Music={is_music} music={music_score:.2f} speech={speech_score:.2f} "
                f"zcr={zcr:.4f} ent={entropy:.3f} pitch={pitch_p:.3f} "
                f"bass={bass:.3f} sub={sub_bass:.3f} "
                f"burst={burst_ratio:.2f} flat={flatness:.3f} sb={speech_band:.2f}"
            )
            return is_music, float(confidence)

        except Exception as e:
            logger.error(f"Music/speech classification error: {e}")
            return True, 0.5

    # ------------------------------------------------------------------
    # Stage 2 — Genre (ONNX primary, heuristic fallback)
    # ------------------------------------------------------------------

    def classify_genre(
        self, audio_data: np.ndarray, features: Dict[str, float]
    ) -> Tuple[str, float]:
        """
        Classify genre. Tries ONNX model first, falls back to heuristics.
        Returns (genre_label, confidence).
        """
        # Try ONNX
        result = self._onnx.predict(audio_data, self.samplerate)
        if result is not None:
            broad, confidence, detailed = result
            return broad, confidence

        # Heuristic fallback
        return self._heuristic_genre(features)

    def _heuristic_genre(
        self, features: Dict[str, float]
    ) -> Tuple[str, float]:
        """Hand-crafted genre scoring, calibrated to real feature values."""
        if not features:
            return "Unknown", 0.0

        bass      = features.get('bass_content', 0.0)
        mid       = features.get('mid_content', 0.0)
        treble    = features.get('brightness', 0.0)
        perc      = features.get('percussion_content', 0.0)
        entropy   = features.get('spectral_entropy', 0.5)
        stability = features.get('energy_stability', 1.0)
        pitch_p   = features.get('pitch_periodicity', 0.0)
        flatness  = features.get('spectral_flatness', 0.5)

        scores = {}

        # Classical — low entropy, tonal, low bass
        if pitch_p > 0.15 and entropy < 0.82 and flatness < 0.20:
            scores['Classical'] = (
                0.30 * min(pitch_p / 0.5, 1.0) +
                0.30 * max(0, 1 - abs(entropy - 0.70) / 0.12) +
                0.25 * min(mid / 0.5, 1.0) +
                0.15 * max(0, 1 - bass / 0.18)
            )

        # Pop — balanced, moderate bass, high entropy
        if bass > 0.10 and mid > 0.35:
            scores['Pop'] = (
                0.30 * min(mid / 0.5, 1.0) +
                0.25 * max(0, 1 - abs(bass - 0.18) / 0.10) +
                0.25 * min(perc / 0.12, 1.0) +
                0.20 * max(0, 1 - abs(entropy - 0.88) / 0.06)
            )

        # Rock — high bass + percussion
        if bass > 0.15 and perc > 0.10:
            scores['Rock'] = (
                0.35 * min(bass / 0.25, 1.0) +
                0.35 * min(perc / 0.18, 1.0) +
                0.20 * min(treble / 0.25, 1.0) +
                0.10 * max(0, 1 - abs(entropy - 0.90) / 0.05)
            )

        # Electronic — bright, percussive, synthetic
        if treble > 0.20 and perc > 0.08:
            scores['Electronic'] = (
                0.30 * min(treble / 0.28, 1.0) +
                0.30 * min(perc / 0.18, 1.0) +
                0.25 * max(0, 1 - pitch_p / 0.4) +
                0.15 * max(0, 1 - flatness / 0.15)
            )

        # Acoustic — natural, low percussion and bass
        if pitch_p > 0.12 and perc < 0.10 and bass < 0.18 and entropy < 0.85:
            scores['Acoustic'] = (
                0.35 * min(pitch_p / 0.40, 1.0) +
                0.30 * max(0, 1 - perc / 0.10) +
                0.20 * min(mid / 0.45, 1.0) +
                0.15 * max(0, 1 - bass / 0.18)
            )

        # Ambient — very stable, quiet, smooth
        if stability < 0.40 and perc < 0.08:
            scores['Ambient'] = (
                0.40 * max(0, 1 - stability / 0.40) +
                0.25 * max(0, 1 - perc / 0.08) +
                0.20 * max(0, 1 - treble / 0.15) +
                0.15 * max(0, 1 - entropy / 0.65)
            )

        # Jazz — moderate entropy, melodic, light percussion
        if 0.68 < entropy < 0.88 and pitch_p > 0.15 and bass > 0.05:
            scores['Jazz'] = (
                0.35 * max(0, 1 - abs(entropy - 0.78) / 0.10) +
                0.30 * min(pitch_p / 0.40, 1.0) +
                0.20 * max(0, 1 - abs(bass - 0.12) / 0.08) +
                0.15 * max(0, 1 - perc / 0.12)
            )

        if not scores or max(scores.values()) < 0.15:
            return "Unknown", 0.0

        best  = max(scores, key=scores.get)
        score = min(scores[best], 1.0)
        logger.debug(
            "Heuristic genre: "
            + " ".join(f"{g}={v:.2f}" for g, v in
                       sorted(scores.items(), key=lambda x: -x[1]))
            + f" => {best} ({score:.2f})"
        )
        return best, float(score)

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def classify_audio(self, audio_data: np.ndarray) -> Dict[str, object]:
        """
        Full pipeline: extract features -> music/speech -> genre.

        Returns dict with:
            is_music, music_confidence, genre, genre_confidence, features
        """
        features = self.extract_features(audio_data)

        if not features:
            return {
                'is_music': True,
                'music_confidence': 0.5,
                'genre': 'Unknown',
                'genre_confidence': 0.0,
                'features': {}
            }

        is_music, music_conf = self.is_music_vs_speech(features)

        if is_music:
            genre, genre_conf = self.classify_genre(audio_data, features)
        else:
            genre      = 'Speech/Noise'
            genre_conf = float(1.0 - music_conf)

        return {
            'is_music':          is_music,
            'music_confidence':  float(music_conf),
            'genre':             genre,
            'genre_confidence':  float(genre_conf),
            'features':          features,
        }