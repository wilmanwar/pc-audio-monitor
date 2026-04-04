#!/usr/bin/env python3
"""
Music Genre and Type Classification Module

Classifies audio into:
1. Music vs Non-Music (speech, ambient, notifications, ads, etc.)
2. Music genres (Classical, Pop, Rock, Jazz, Electronic, Acoustic, Ambient)

Uses spectral, temporal, and harmonic features for classification.
"""

import numpy as np
import logging
from typing import Dict, Tuple, Optional

logger = logging.getLogger(__name__)


class MusicClassifier:
    """Classifies audio as music/non-music and identifies music genres."""

    def __init__(self, samplerate: int = 44100):
        self.samplerate = samplerate

    def extract_features(self, audio_data: np.ndarray) -> Dict[str, float]:
        """Extract spectral, temporal, harmonic, and rhythmic features."""
        if audio_data.ndim > 1:
            audio_data = np.mean(audio_data, axis=1)

        if len(audio_data) < 1000:
            return {}

        features = {}

        try:
            chunk_size = int(self.samplerate * 0.02)  # 20ms chunks

            # --- SPECTRAL FEATURES ---
            window = np.hanning(len(audio_data))
            windowed = audio_data * window
            fft = np.fft.rfft(windowed)
            freqs = np.fft.rfftfreq(len(windowed), 1.0 / self.samplerate)
            magnitude = np.abs(fft)
            total_energy = np.sum(magnitude) + 1e-10

            # Spectral Entropy: music ~0.5-0.75, speech ~0.7-0.9
            norm_mag = magnitude / total_energy
            spectral_entropy = -np.sum(norm_mag[norm_mag > 0] * np.log2(norm_mag[norm_mag > 0] + 1e-10))
            max_entropy = np.log2(len(magnitude))
            features['spectral_entropy'] = spectral_entropy / max_entropy if max_entropy > 0 else 0

            # Spectral Centroid
            features['spectral_centroid'] = np.sum(freqs * magnitude) / total_energy

            # Spectral Rolloff (95% energy)
            cum_energy = np.cumsum(magnitude)
            rolloff_idx = np.where(cum_energy >= 0.95 * total_energy)[0]
            features['spectral_rolloff'] = freqs[rolloff_idx[0]] if len(rolloff_idx) > 0 else 0

            # Spectral Flux (frame-to-frame change)
            fluxes = []
            prev_mag = None
            for i in range(0, len(audio_data) - chunk_size, chunk_size):
                chunk_fft = np.abs(np.fft.rfft(audio_data[i:i+chunk_size] * np.hanning(chunk_size)))
                if prev_mag is not None:
                    fluxes.append(np.sqrt(np.sum((chunk_fft - prev_mag) ** 2)))
                prev_mag = chunk_fft
            features['spectral_flux'] = np.mean(fluxes) if fluxes else 0

            # --- TEMPORAL FEATURES ---
            # Zero Crossing Rate: speech ~0.05-0.15, music ~0.01-0.08
            features['zero_crossing_rate'] = np.sum(
                np.abs(np.diff(np.sign(audio_data)))
            ) / (2 * len(audio_data))

            features['rms_energy'] = float(np.sqrt(np.mean(audio_data ** 2)))

            # Energy Stability over frames
            energy_frames = [
                np.sqrt(np.mean(audio_data[i:i+chunk_size] ** 2))
                for i in range(0, len(audio_data) - chunk_size, chunk_size // 2)
            ]
            mean_e = np.mean(energy_frames) + 1e-10
            features['energy_stability'] = float(np.std(energy_frames) / mean_e)

            # --- SPEECH BURSTINESS ---
            # Speech has sharp energy bursts between words and syllables.
            # We measure the proportion of 20ms frames that are "near-silent"
            # (< 10% of mean energy). Music flows; speech is full of micro-gaps.
            silence_threshold = mean_e * 0.10
            silent_frames = sum(1 for e in energy_frames if e < silence_threshold)
            features['burst_ratio'] = float(silent_frames / len(energy_frames)) if energy_frames else 0.0

            # --- HARMONIC FEATURES ---
            features['harmonic_peaks'] = float(np.sum(magnitude > np.mean(magnitude) * 0.5) / len(magnitude))

            brightness_mask = freqs > 2000
            features['brightness'] = float(np.sum(magnitude[brightness_mask]) / total_energy) if brightness_mask.any() else 0

            presence_mask = (freqs > 2000) & (freqs < 4000)
            features['presence'] = float(np.sum(magnitude[presence_mask]) / total_energy) if presence_mask.any() else 0

            # --- SPECTRAL FLATNESS ---
            # Measures how noise-like vs tonal the spectrum is.
            # Tonal (music): low flatness — energy concentrated in harmonic peaks.
            # Noisy (speech between words, unvoiced consonants): high flatness.
            # Computed per-band so voiced speech (low flatness in speech band)
            # doesn't fool us — we look at the full spectrum.
            eps = 1e-10
            mag_pos = magnitude[magnitude > 0]
            if len(mag_pos) > 1:
                geo_mean = np.exp(np.mean(np.log(mag_pos + eps)))
                arith_mean = np.mean(mag_pos)
                features['spectral_flatness'] = float(geo_mean / (arith_mean + eps))
            else:
                features['spectral_flatness'] = 1.0  # flat = noise-like

            # --- BAND ENERGY RATIOS ---
            def band_energy(low, high):
                mask = (freqs >= low) & (freqs < high)
                return float(np.sum(magnitude[mask]) / total_energy) if mask.any() else 0.0

            features['bass_content'] = band_energy(20, 250)
            features['mid_content'] = band_energy(250, 2000)
            features['percussion_content'] = band_energy(5000, 20000)

            # Speech-band energy (300-3400 Hz is telephone/speech bandwidth)
            features['speech_band'] = band_energy(300, 3400)

            # Sub-bass absence: speech has almost nothing below 100 Hz;
            # music (even acoustic) usually has some room tone / instrument body
            features['sub_bass'] = band_energy(20, 100)

            # Harmonic periodicity via autocorrelation
            try:
                ac_len = min(len(audio_data), 4096)
                ac = np.correlate(audio_data[:ac_len], audio_data[:ac_len], mode='full')
                ac = ac[len(ac)//2:]
                ac = ac / (ac[0] + 1e-10)
                min_lag = int(self.samplerate / 1000)
                max_lag = int(self.samplerate / 50)
                if max_lag < len(ac):
                    peak_ac = float(np.max(ac[min_lag:max_lag]))
                else:
                    peak_ac = 0.0
                features['pitch_periodicity'] = max(0.0, peak_ac)
            except Exception:
                features['pitch_periodicity'] = 0.0

            logger.debug(f"Features: {features}")
            return features

        except Exception as e:
            logger.error(f"Error extracting features: {e}")
            return {}

    def is_music_vs_speech(self, features: Dict[str, float]) -> Tuple[bool, float]:
        """
        Classify audio as music vs speech/non-music.

        Strategy: accumulate independent evidence on both sides, then apply
        two hard veto rules that catch podcasts even when they look musical:

          VETO 1 — High burst ratio:
            If more than 30% of 20ms frames are near-silent, the audio is
            bursty like speech (words with gaps), not continuous like music.

          VETO 2 — High spectral flatness + speech-band dominance:
            Voiced speech has a flat spectrum between its formant peaks.
            When flatness is high AND speech-band energy dominates, it's speech
            even if pitch_periodicity is non-zero (resonant voice).

        After vetos, standard weighted scoring decides borderline cases.
        """
        if not features:
            return True, 0.5

        try:
            entropy          = features.get('spectral_entropy', 0.5)
            zcr              = features.get('zero_crossing_rate', 0.05)
            energy_stability = features.get('energy_stability', 0.5)
            harmonic_peaks   = features.get('harmonic_peaks', 0.1)
            speech_band      = features.get('speech_band', 0.3)
            pitch_periodicity= features.get('pitch_periodicity', 0.0)
            bass_content     = features.get('bass_content', 0.1)
            sub_bass         = features.get('sub_bass', 0.0)
            burst_ratio      = features.get('burst_ratio', 0.0)
            spectral_flatness= features.get('spectral_flatness', 0.5)

            # ----------------------------------------------------------------
            # HARD VETO 1: Burstiness
            # Music flows. Speech has gaps between syllables and words.
            # If >30% of short frames are near-silent it's almost certainly speech.
            # ----------------------------------------------------------------
            burst_veto = burst_ratio > 0.30

            # ----------------------------------------------------------------
            # HARD VETO 2: Flat spectrum + speech-band dominance
            # Resonant / laughing voices can have decent pitch_periodicity,
            # but their spectrum is much flatter than a musical instrument
            # (which has strong harmonics with quiet inharmonic gaps).
            # ----------------------------------------------------------------
            flatness_veto = (spectral_flatness > 0.15) and (speech_band > 0.55)

            if burst_veto or flatness_veto:
                reason = "burst" if burst_veto else "flatness+speech_band"
                logger.debug(f"Speech VETO fired ({reason}): burst={burst_ratio:.2f} "
                             f"flat={spectral_flatness:.3f} speech_band={speech_band:.2f}")
                # Confidence reflects how strongly the veto fired
                veto_conf = max(
                    min(burst_ratio / 0.30, 1.0) if burst_veto else 0.0,
                    min((spectral_flatness / 0.15) * (speech_band / 0.55), 1.0) if flatness_veto else 0.0
                )
                return False, 0.60 + 0.40 * veto_conf

            # ----------------------------------------------------------------
            # SCORED EVIDENCE — both sides accumulate points independently
            # ----------------------------------------------------------------

            # Speech evidence
            speech_score = 0.0
            speech_score += 0.25 if zcr > 0.06 else (zcr / 0.06) * 0.25
            speech_score += 0.25 if speech_band > 0.60 else (speech_band / 0.60) * 0.15
            speech_score += 0.20 if entropy > 0.78 else 0.0
            speech_score += 0.15 if pitch_periodicity < 0.15 else 0.0
            speech_score += 0.15 if bass_content < 0.05 else 0.0

            # Music evidence
            music_score = 0.0
            music_score += 0.30 if pitch_periodicity > 0.20 else (pitch_periodicity / 0.20) * 0.30
            music_score += 0.20 if sub_bass > 0.02 else 0.0          # room tone / instrument body
            music_score += 0.20 if bass_content > 0.08 else 0.0
            music_score += 0.15 if spectral_flatness < 0.08 else 0.0  # tonal/peaky spectrum
            music_score += 0.15 if entropy < 0.75 else 0.0

            # Decision
            if speech_score >= 0.60:
                is_music, confidence = False, speech_score
            elif music_score >= 0.55:
                is_music, confidence = True, music_score
            elif music_score > speech_score:
                is_music, confidence = True, music_score
            else:
                is_music, confidence = False, speech_score

            logger.debug(
                f"Music={is_music} | music={music_score:.2f} speech={speech_score:.2f} "
                f"| zcr={zcr:.4f} entropy={entropy:.3f} pitch_p={pitch_periodicity:.3f} "
                f"bass={bass_content:.3f} sub={sub_bass:.3f} "
                f"burst={burst_ratio:.2f} flat={spectral_flatness:.3f} speech_band={speech_band:.2f}"
            )
            return is_music, confidence

        except Exception as e:
            logger.error(f"Error in music classification: {e}")
            return True, 0.5

    def classify_genre(self, features: Dict[str, float]) -> Tuple[str, float]:
        """
        Classify music genre. Returns (genre, confidence).

        Genres: Classical, Pop, Rock, Jazz, Electronic, Acoustic, Ambient
        """
        if not features:
            return "Unknown", 0.0

        try:
            bass = features.get('bass_content', 0.0)
            mid = features.get('mid_content', 0.0)
            treble = features.get('brightness', 0.0)
            percussion = features.get('percussion_content', 0.0)
            entropy = features.get('spectral_entropy', 0.5)
            energy_stability = features.get('energy_stability', 1.0)
            pitch_p = features.get('pitch_periodicity', 0.0)

            scores = {
                # Classical: strong pitch periodicity, high mid/treble, relatively low bass
                'Classical': (
                    0.35 * min(pitch_p * 2, 1.0) +
                    0.25 * (1 - min(bass / 0.4, 1.0)) +
                    0.25 * (mid if mid > 0.4 else 0.0) +
                    0.15 * (treble if treble > 0.08 else 0.0)
                ),
                # Pop: balanced, moderate percussion, strong vocals in mid
                'Pop': (
                    0.30 * (1 - abs(bass - 0.25)) +
                    0.25 * (1 - abs(mid - 0.45)) +
                    0.25 * min(percussion / 0.3, 1.0) +
                    0.20 * (1 - entropy)
                ),
                # Rock: high bass + percussion, electric guitar brightness
                'Rock': (
                    0.35 * min(bass / 0.3, 1.0) +
                    0.35 * min(percussion / 0.25, 1.0) +
                    0.20 * (treble if treble > 0.15 else 0.0) +
                    0.10 * (1 - entropy)
                ),
                # Electronic: very bright, heavy percussion, synthetic
                'Electronic': (
                    0.30 * min(treble / 0.25, 1.0) +
                    0.30 * min(percussion / 0.2, 1.0) +
                    0.25 * (entropy if entropy > 0.6 else 0.0) +
                    0.15 * (1 - min(bass / 0.4, 1.0))
                ),
                # Acoustic: natural sound, low bass/percussion, harmonic
                'Acoustic': (
                    0.30 * (1 - min(bass / 0.25, 1.0)) +
                    0.30 * (1 - min(percussion / 0.15, 1.0)) +
                    0.25 * min(pitch_p * 2, 1.0) +
                    0.15 * (mid if mid > 0.3 else 0.0)
                ),
                # Ambient: very stable energy, low everything, smooth
                'Ambient': (
                    0.40 * (1 - min(energy_stability, 1.0)) +
                    0.30 * (1 - entropy) +
                    0.20 * (1 - treble) +
                    0.10 * (1 - percussion)
                ),
                # Jazz: complex spectrum, moderate bass, improvisational
                'Jazz': (
                    0.35 * (entropy if 0.55 < entropy < 0.82 else 0.0) +
                    0.30 * (1 - min(abs(bass - 0.18), 1.0)) +
                    0.20 * min(pitch_p * 1.5, 1.0) +
                    0.15 * (1 - min(percussion / 0.25, 1.0))
                ),
            }

            best_genre = max(scores, key=scores.get)
            confidence = min(scores[best_genre], 1.0)

            logger.debug(f"Genre scores: {scores} -> {best_genre} ({confidence:.2f})")
            return best_genre, confidence

        except Exception as e:
            logger.error(f"Error in genre classification: {e}")
            return "Unknown", 0.0

    def classify_audio(self, audio_data: np.ndarray) -> Dict[str, object]:
        """
        Full classification pipeline.

        Returns dict with keys:
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
            genre, genre_conf = self.classify_genre(features)
        else:
            genre = 'Speech/Ad'
            genre_conf = 1.0 - music_conf

        return {
            'is_music': is_music,
            'music_confidence': music_conf,
            'genre': genre,
            'genre_confidence': genre_conf,
            'features': features
        }