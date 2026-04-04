#!/usr/bin/env python3
"""
Music Genre and Type Classification Module

Classifies audio into:
1. Music vs Non-Music (speech, ambient, notifications, etc.)
2. Music genres (Classical, Pop, Rock, Jazz, Electronic, Acoustic, etc.)

Uses spectral, temporal, and rhythm features for classification.
"""

import numpy as np
import logging
from typing import Dict, Tuple, Optional

logger = logging.getLogger(__name__)


class MusicClassifier:
    """Classifies audio as music/non-music and identifies music genres."""
    
    def __init__(self, samplerate: int = 44100):
        """
        Initialize music classifier.
        
        Args:
            samplerate: Sample rate in Hz (44100 or 48000 typical)
        """
        self.samplerate = samplerate
    
    def extract_features(self, audio_data: np.ndarray) -> Dict[str, float]:
        """
        Extract audio features for classification.
        
        Features extracted:
        - Spectral: entropy, centroid, rolloff, flux
        - Temporal: zero crossing rate, RMS energy
        - Harmonic: harmonic-to-noise ratio, pitch stability
        - Rhythmic: beat strength, tempo indicators
        
        Args:
            audio_data: Audio samples (numpy array)
            
        Returns:
            Dictionary of features
        """
        if audio_data.ndim > 1:
            audio_data = np.mean(audio_data, axis=1)
        
        if len(audio_data) < 1000:
            return {}
        
        features = {}
        
        try:
            # SPECTRAL FEATURES
            window = np.hanning(len(audio_data))
            windowed = audio_data * window
            fft = np.fft.rfft(windowed)
            freqs = np.fft.rfftfreq(len(windowed), 1.0 / self.samplerate)
            magnitude = np.abs(fft)
            
            # Spectral Entropy (0=organized, 1=random)
            # Music: 0.3-0.6, Speech: 0.6-0.9
            normalized_mag = magnitude / (np.sum(magnitude) + 1e-10)
            spectral_entropy = -np.sum(normalized_mag[normalized_mag > 0] * np.log2(normalized_mag[normalized_mag > 0] + 1e-10))
            max_entropy = np.log2(len(magnitude))
            features['spectral_entropy'] = spectral_entropy / max_entropy if max_entropy > 0 else 0
            
            # Spectral Centroid (center of mass of spectrum)
            # Low = bass-heavy (rock, hip-hop), High = treble-heavy (classical strings)
            total_energy = np.sum(magnitude)
            if total_energy > 0:
                features['spectral_centroid'] = np.sum(freqs * magnitude) / total_energy
            else:
                features['spectral_centroid'] = 0
            
            # Spectral Rolloff (frequency below which 95% of energy)
            cum_energy = np.cumsum(magnitude)
            energy_95 = 0.95 * total_energy
            rolloff_idx = np.where(cum_energy >= energy_95)[0]
            features['spectral_rolloff'] = freqs[rolloff_idx[0]] if len(rolloff_idx) > 0 else 0
            
            # Spectral Flux (change between consecutive frames)
            # Speech/music transitions = high flux
            chunk_size = int(self.samplerate * 0.02)  # 20ms chunks
            fluxes = []
            prev_mag = None
            for i in range(0, len(audio_data) - chunk_size, chunk_size):
                chunk = audio_data[i:i+chunk_size]
                chunk_windowed = chunk * np.hanning(len(chunk))
                chunk_fft = np.abs(np.fft.rfft(chunk_windowed))
                if prev_mag is not None:
                    flux = np.sqrt(np.sum((chunk_fft - prev_mag) ** 2))
                    fluxes.append(flux)
                prev_mag = chunk_fft
            features['spectral_flux'] = np.mean(fluxes) if fluxes else 0
            
            # TEMPORAL FEATURES
            # Zero Crossing Rate (number of times signal crosses zero)
            # Low = smooth (music), High = noisy (speech, noise)
            zcr = np.sum(np.abs(np.diff(np.sign(audio_data)))) / (2 * len(audio_data))
            features['zero_crossing_rate'] = zcr
            
            # RMS Energy
            features['rms_energy'] = np.sqrt(np.mean(audio_data ** 2))
            
            # Energy Stability (std of energy over time)
            # Low = stable (music), High = variable (speech)
            energy_frames = []
            for i in range(0, len(audio_data) - chunk_size, chunk_size // 2):
                chunk = audio_data[i:i+chunk_size]
                energy_frames.append(np.sqrt(np.mean(chunk ** 2)))
            features['energy_stability'] = np.std(energy_frames) / (np.mean(energy_frames) + 1e-10)
            
            # HARMONIC FEATURES
            # Spectral Peaks (how many harmonic peaks)
            # Music: many peaks, Speech: fewer organized peaks
            peaks = magnitude > (np.mean(magnitude) * 0.5)
            features['harmonic_peaks'] = np.sum(peaks) / len(magnitude)
            
            # Brightness (proportion of energy above 2kHz)
            brightness_mask = freqs > 2000
            if np.sum(brightness_mask) > 0:
                features['brightness'] = np.sum(magnitude[brightness_mask]) / total_energy
            else:
                features['brightness'] = 0
            
            # Presence (proportion of energy between 2-4kHz, typical for instruments)
            presence_mask = (freqs > 2000) & (freqs < 4000)
            if np.sum(presence_mask) > 0:
                features['presence'] = np.sum(magnitude[presence_mask]) / total_energy
            else:
                features['presence'] = 0
            
            # GENRE-SPECIFIC FEATURES
            # Percussion (high-frequency content in 5-20kHz range)
            percussion_mask = (freqs > 5000) & (freqs < 20000)
            if np.sum(percussion_mask) > 0:
                features['percussion_content'] = np.sum(magnitude[percussion_mask]) / total_energy
            else:
                features['percussion_content'] = 0
            
            # Bass (energy in 20-250Hz)
            bass_mask = (freqs > 20) & (freqs < 250)
            if np.sum(bass_mask) > 0:
                features['bass_content'] = np.sum(magnitude[bass_mask]) / total_energy
            else:
                features['bass_content'] = 0
            
            # Midrange (energy in 250-2000Hz, typical for vocals and melody)
            mid_mask = (freqs > 250) & (freqs < 2000)
            if np.sum(mid_mask) > 0:
                features['mid_content'] = np.sum(magnitude[mid_mask]) / total_energy
            else:
                features['mid_content'] = 0
            
            logger.debug(f"Extracted features: {features}")
            return features
            
        except Exception as e:
            logger.error(f"Error extracting features: {e}")
            return {}
    
    def is_music_vs_speech(self, features: Dict[str, float]) -> Tuple[bool, float]:
        """
        Classify audio as music vs speech/non-music.
        
        Returns:
            (is_music: bool, confidence: float 0-1)
        """
        if not features:
            return True, 0.5  # Default to music if can't analyze
        
        try:
            entropy = features.get('spectral_entropy', 0.5)
            zcr = features.get('zero_crossing_rate', 0.0)
            energy_stability = features.get('energy_stability', 0.5)
            harmonic_peaks = features.get('harmonic_peaks', 0.1)
            mid_content = features.get('mid_content', 0.3)
            
            # Music classification rules:
            # 1. Moderate-high mid content (vocals, instruments) = music
            # 2. Organized spectral content (low entropy or harmonic peaks) = music
            # 3. Either low ZCR OR stable energy = music
            
            # Adjusted thresholds based on real classical music data
            has_mid_content = mid_content > 0.4  # Classical: 82% mid content
            is_organized = entropy < 0.75 or harmonic_peaks > 0.08  # Speech: 0.68+ entropy
            has_smooth_zcr = zcr < 0.08  # Classical: 0.041 ZCR
            
            # Music score: combination of features
            music_score = 0.0
            music_score += 0.4 if has_mid_content else 0.0
            music_score += 0.35 if is_organized else 0.0
            music_score += 0.25 if has_smooth_zcr else 0.0
            
            is_music = music_score >= 0.5  # Lower threshold
            confidence = music_score
            
            logger.debug(
                f"Music vs Speech: entropy={entropy:.3f}, zcr={zcr:.4f}, "
                f"mid={mid_content:.3f}, peaks={harmonic_peaks:.3f}, "
                f"mid_ok={has_mid_content}, organized={is_organized}, smooth={has_smooth_zcr} "
                f"→ music={is_music} (score={confidence:.2f})"
            )
            
            return is_music, confidence
            
        except Exception as e:
            logger.error(f"Error in music classification: {e}")
            return True, 0.5
    
    def classify_genre(self, features: Dict[str, float]) -> Tuple[str, float]:
        """
        Classify music genre based on audio features.
        
        Returns:
            (genre: str, confidence: float 0-1)
        
        Genres detected:
        - Classical: Low bass, high mid, complex spectrum
        - Pop: Balanced spectrum, moderate percussion
        - Rock: High bass, high percussion, stable rhythm
        - Jazz: Complex spectral patterns, moderate tempo
        - Electronic: Bright spectrum, high percussion
        - Acoustic: Low bass, natural harmonic structure
        - Ambient: Very low energy variation, smooth spectrum
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
            centroid = features.get('spectral_centroid', 2000)
            
            scores = {}
            
            # Classical: Low bass, high mid/treble, complex but stable
            # Characteristics: Violins, pianos, instruments with harmonic content
            # Range: entropy 0.68-0.79, mid 0.48-0.82, bass 0.07-0.27, treble 0.10-0.24
            scores['Classical'] = (
                0.30 * (1 - min(bass / 0.5, 1.0)) +  # Relatively low bass
                0.30 * (mid if mid > 0.4 else 0.0) +  # Moderate-high mid
                0.25 * (1 - abs(entropy - 0.75)) +  # Mid-range entropy (0.68-0.79)
                0.15 * (treble if treble > 0.08 else 0.0)  # Treble presence
            )
            
            # Pop: Balanced spectrum, moderate percussion, smooth
            # Characteristics: Vocals, drums, synths
            scores['Pop'] = (
                0.3 * (1 - abs(bass - 0.3)) +  # Moderate bass
                0.2 * (1 - abs(mid - 0.4)) +  # Moderate-high mid
                0.3 * (1 - min(percussion, 1.0)) +  # Moderate percussion
                0.2 * (1 - entropy)  # Low entropy (smooth)
            )
            
            # Rock: High bass, high percussion, strong rhythm
            # Characteristics: Drums, electric guitars, bass guitar
            scores['Rock'] = (
                0.4 * min(bass, 1.0) +  # High bass
                0.4 * min(percussion, 1.0) +  # High percussion
                0.2 * (1 - entropy)  # Lower entropy
            )
            
            # Electronic: Bright spectrum, high percussion, synthetic quality
            # Characteristics: Synths, electronic drums, digital processing
            scores['Electronic'] = (
                0.3 * treble +  # High brightness
                0.3 * min(percussion, 1.0) +  # High percussion
                0.2 * (entropy if entropy > 0.6 else 1.0 - entropy) +  # Variable but bright
                0.2 * (1 - min(bass, 0.5))  # Not too much bass
            )
            
            # Acoustic: Natural spectrum, low bass, harmonic
            # Characteristics: Guitar, piano, acoustic instruments
            scores['Acoustic'] = (
                0.3 * (1 - min(bass, 1.0)) +  # Low bass
                0.3 * (1 - min(percussion, 0.3)) +  # Low percussion
                0.2 * (1 - entropy) +  # Low entropy (organized)
                0.2 * (mid if mid > 0.3 else 0.0)  # Presence in mid
            )
            
            # Ambient: Very smooth, low energy variation, low frequency
            # Characteristics: Atmospheric, pads, field recordings
            scores['Ambient'] = (
                0.4 * (1 - min(energy_stability, 1.0)) +  # Very stable
                0.3 * (1 - entropy) +  # Low entropy
                0.2 * (1 - treble) +  # Low brightness
                0.1 * (1 - percussion)  # Low percussion
            )
            
            # Jazz: Complex spectrum, moderate tempo, syncopation
            # Characteristics: Complex chords, improvisation, varied instruments
            scores['Jazz'] = (
                0.4 * (entropy if entropy > 0.5 else 0.5) +  # Complex spectrum
                0.3 * (1 - min(abs(bass - 0.2), 1.0)) +  # Moderate-low bass
                0.3 * (1 - min(percussion, 0.5))  # Moderate percussion (drums)
            )
            
            # Find best matching genre
            best_genre = max(scores, key=scores.get)
            confidence = min(scores[best_genre], 1.0)
            
            logger.debug(
                f"Genre classification scores: {scores} "
                f"→ {best_genre} (confidence={confidence:.2f})"
            )
            
            return best_genre, confidence
            
        except Exception as e:
            logger.error(f"Error in genre classification: {e}")
            return "Unknown", 0.0
    
    def classify_audio(self, audio_data: np.ndarray) -> Dict[str, any]:
        """
        Complete classification of audio.
        
        Args:
            audio_data: Audio samples (numpy array)
            
        Returns:
            Dictionary with classification results
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
            genre = 'Speech/Noise'
            genre_conf = 1.0 - music_conf
        
        return {
            'is_music': is_music,
            'music_confidence': music_conf,
            'genre': genre,
            'genre_confidence': genre_conf,
            'features': features
        }
