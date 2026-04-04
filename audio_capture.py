"""Audio capture module for detecting system audio levels."""

import sounddevice as sd
import numpy as np
import logging
import os
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


class AudioCapture:
    """Captures and analyzes system audio using WASAPI loopback."""
    
    def __init__(self, threshold_db: float = -40, duration: float = 2.0, samplerate: int = 44100):
        """
        Initialize audio capture.
        
        Args:
            threshold_db: RMS threshold in dB below which audio is considered silence (-60 to -20)
            duration: Recording duration in seconds per analysis window
            samplerate: Sample rate in Hz (44100 or 48000 typical)
        """
        self.threshold_db = threshold_db
        self.duration = duration
        self.samplerate = samplerate
        self.device_id = None
        self.device_id = self._find_loopback_device()
        # Query the device's native sample rate if available
        if self.device_id is not None:
            self._query_device_samplerate()
        
    def _find_loopback_device(self) -> Optional[int]:
        """
        Find the WASAPI loopback device (Stereo Mix) or alternative virtual audio device.
        Falls back to default input device if Stereo Mix not found.
        
        Search priority:
        1. Stereo Mix / WASAPI loopback
        2. Virtual audio devices (VB-Audio Cable, VoiceMeeter, etc)
        3. Default input device (microphone fallback)
        
        Returns:
            Device ID if found, None otherwise
        """
        try:
            # Check for environment override
            device_override = os.getenv('AUDIO_DEVICE_ID')
            if device_override and device_override.isdigit():
                logger.info(f"Using override device from AUDIO_DEVICE_ID: {device_override}")
                return int(device_override)
            
            devices = sd.query_devices()
            logger.info("Available audio devices:")
            for idx, device in enumerate(devices):
                logger.info(f"  [{idx}] {device['name']} (in: {device['max_input_channels']}, out: {device['max_output_channels']})")
            
            # Priority list for device names (in order of preference)
            priority_keywords = [
                # Stereo Mix / WASAPI loopback (highest priority)
                ('stereo mix', 1),
                ('wave out mix', 1),
                ('what u hear', 1),
                ('loopback', 1),
                ('wasapi', 1),
                # Voicemeeter Point - these work!
                ('voicemeeter point', 1.5),
                # VB-Audio Voicemeeter outputs (fallback)
                ('voicemeeter out', 3),
            ]
            
            best_device = None
            best_priority = 999
            
            # Find device with highest priority
            for idx, device in enumerate(devices):
                if device['max_input_channels'] == 0:
                    continue
                    
                name = device['name'].lower()
                
                for keyword, priority in priority_keywords:
                    if keyword in name:
                        if priority < best_priority:
                            best_device = idx
                            best_priority = priority
                            break
            
            if best_device is not None:
                device_name = devices[best_device]['name']
                device_type = "Stereo Mix" if best_priority == 1 else "Virtual Audio Device"
                logger.info(f"Found {device_type}: {device_name} (ID: {best_device})")
                return best_device
            
            # Fallback to default input device
            try:
                default_input, default_output = sd.default.device
            except (TypeError, ValueError):
                default_input = sd.default.device
            
            if default_input is not None and isinstance(default_input, int) and default_input >= 0:
                logger.warning("Stereo Mix / Virtual audio device not found.")
                logger.warning("Using default input device as fallback (usually microphone).")
                logger.warning("")
                logger.warning("For better system audio detection, consider:")
                logger.warning("  • Enable Stereo Mix in audio driver settings")
                logger.warning("  • Install VB-Audio Virtual Cable (https://vb-audio.com/Cable/)")
                logger.warning("  • Update your audio driver")
                logger.warning("  • See STEREO_MIX_ALTERNATIVES.md for other options")
                logger.warning("")
                default_info = devices[default_input]
                logger.info(f"Using fallback device: {default_info['name']} (ID: {default_input})")
                logger.info("You can force a device with: AUDIO_DEVICE_ID=<number> in .env")
                return default_input
            
            logger.error("No suitable audio input device found!")
            return None
        except Exception as e:
            logger.error(f"Error finding loopback device: {e}")
            return None
    
    def _query_device_samplerate(self) -> None:
        """Query device's default sample rate."""
        try:
            device_info = sd.query_devices(self.device_id)
            default_sr = device_info.get('default_samplerate', 44100)
            self.samplerate = int(default_sr)
            logger.info(f"Device {self.device_id} using sample rate: {self.samplerate} Hz")
        except Exception as e:
            logger.warning(f"Could not query device sample rate, using default 44100: {e}")
    
    def capture_audio(self) -> np.ndarray:
        """
        Capture audio from loopback device.
        
        Returns:
            Audio data as numpy array
            
        Raises:
            RuntimeError: If no loopback device is available
        """
        if self.device_id is None:
            raise RuntimeError("No loopback device found. Please enable Stereo Mix on your audio device.")
        
        try:
            logger.debug(f"Recording {self.duration}s from device {self.device_id}...")
            # Try multiple channel configurations for compatibility with multi-channel devices
            for channels in [1, 2, 4, 8]:
                try:
                    logger.debug(f"Attempting {channels}-channel recording...")
                    audio_data = sd.rec(
                        int(self.samplerate * self.duration),
                        samplerate=self.samplerate,
                        channels=channels,
                        device=self.device_id,
                        dtype='float32'
                    )
                    sd.wait()
                    logger.debug(f"Recording complete with {channels} channels. Shape: {audio_data.shape}, dtype: {audio_data.dtype}")
                    return audio_data
                except Exception as e:
                    logger.debug(f"{channels}-channel recording failed: {e}")
                    continue
            
            # If all channels failed, raise error
            raise RuntimeError(f"Could not capture audio from device {self.device_id} with any channel configuration")
        except Exception as e:
            logger.error(f"Error capturing audio: {e}")
            raise
    
    def calculate_rms_db(self, audio_data: np.ndarray) -> float:
        """
        Calculate RMS level in dB.
        
        Args:
            audio_data: Audio samples (numpy array)
            
        Returns:
            RMS level in dB (reference 1.0)
        """
        # Convert to mono if stereo
        if audio_data.ndim > 1:
            audio_data = np.mean(audio_data, axis=1)
        
        # Calculate RMS
        rms = np.sqrt(np.mean(np.square(audio_data)))
        
        # Convert to dB (prevent log(0))
        if rms > 0:
            rms_db = 20 * np.log10(rms)
        else:
            rms_db = -np.inf
        
        logger.debug(f"RMS level: {rms_db:.2f} dB (threshold: {self.threshold_db} dB)")
        return rms_db
    
    def is_music(self, audio_data: np.ndarray) -> bool:
        """
        Detect if audio contains music (vs speech, conversations, etc).
        
        Uses multiple frequency and temporal features:
        - Music: Steady harmonic content, consistent spectral shape, low variation
        - Speech: Variable energy bursts, high temporal variation, broad spectrum
        
        Args:
            audio_data: Audio samples (numpy array)
            
        Returns:
            True if audio appears to be music, False otherwise
        """
        try:
            # Convert to mono if stereo
            if audio_data.ndim > 1:
                audio_data = np.mean(audio_data, axis=1)
            
            # Split into chunks to analyze temporal variation
            chunk_size = int(self.samplerate * 0.5)  # 500ms chunks
            num_chunks = max(2, len(audio_data) // chunk_size)
            chunks = [audio_data[i*chunk_size:(i+1)*chunk_size] for i in range(num_chunks)]
            
            if not chunks or len(chunks[0]) < 100:
                return False
            
            # Analyze each chunk
            chunk_spectral_features = []
            chunk_energies = []
            
            for chunk in chunks:
                if len(chunk) < 100:
                    continue
                
                window = np.hanning(len(chunk))
                chunk_windowed = chunk * window
                
                fft = np.fft.rfft(chunk_windowed)
                freqs = np.fft.rfftfreq(len(chunk_windowed), 1.0 / self.samplerate)
                magnitude = np.abs(fft)
                
                # Music range: 100Hz - 10kHz
                music_min_freq = 100
                music_max_freq = 10000
                
                mask = (freqs >= music_min_freq) & (freqs <= music_max_freq)
                music_magnitude = magnitude[mask]
                music_freqs = freqs[mask]
                
                if len(music_magnitude) == 0:
                    continue
                
                total_energy = np.sum(music_magnitude)
                if total_energy == 0:
                    continue
                
                chunk_energies.append(total_energy)
                
                # Spectral entropy: Low for music (organized), high for speech (random)
                # Normalized so 0 = all energy in one frequency, 1 = uniform
                normalized_mag = music_magnitude / total_energy
                spectral_entropy = -np.sum(normalized_mag[normalized_mag > 0] * np.log2(normalized_mag[normalized_mag > 0] + 1e-10))
                max_entropy = np.log2(len(music_magnitude))
                normalized_entropy = spectral_entropy / max_entropy if max_entropy > 0 else 1.0
                
                # Spectral centroid (where most energy is)
                spectral_centroid = np.sum(music_freqs * music_magnitude) / total_energy
                
                # Peak detection
                peak_threshold = np.mean(music_magnitude) * 0.3
                peaks = music_magnitude > peak_threshold
                num_peaks = np.sum(peaks)
                peak_ratio = num_peaks / len(music_magnitude)
                
                chunk_spectral_features.append({
                    'entropy': normalized_entropy,
                    'centroid': spectral_centroid,
                    'peak_ratio': peak_ratio,
                    'total_energy': total_energy
                })
            
            if not chunk_spectral_features:
                return False
            
            # Extract features across chunks
            entropies = [f['entropy'] for f in chunk_spectral_features]
            centroids = [f['centroid'] for f in chunk_spectral_features]
            peak_ratios = [f['peak_ratio'] for f in chunk_spectral_features]
            
            # Music characteristics:
            # 1. Lower entropy (more organized, less random)
            # 2. Consistent spectral centroid (same instruments playing)
            # 3. Decent peak ratio (harmonic structure)
            # 4. Stable energy (not bursty like speech)
            
            avg_entropy = np.mean(entropies)
            entropy_variation = np.std(entropies)
            
            avg_centroid = np.mean(centroids)
            centroid_variation = np.std(centroids)
            
            avg_peak_ratio = np.mean(peak_ratios)
            
            energy_variation = np.std(chunk_energies) / (np.mean(chunk_energies) + 1e-10)
            
            # Decision logic:
            # Music: Very low entropy (highly organized, harmonic structure)
            # Speech/Conversation: HIGH entropy (0.75+), variable phonemes
            # Entropy is the primary discriminator - don't use just score
            
            is_low_entropy = avg_entropy < 0.65  # Music is very organized (entropy < 0.65)
            is_consistent = centroid_variation < 500  # Music has consistent frequency content
            is_peaky = avg_peak_ratio > 0.12  # Music has harmonic peaks
            is_stable = energy_variation < 0.8  # Music has stable energy, speech is bursty
            
            # CRITICAL: Low entropy + at least 2 other features = music
            # Speech has high entropy, so requiring low entropy first filters it out
            is_music_like = is_low_entropy and (sum([is_consistent, is_peaky, is_stable]) >= 2)
            
            logger.debug(
                f"Music detection: entropy={avg_entropy:.3f} (low={is_low_entropy}), "
                f"consistency={centroid_variation:.0f}Hz (consistent={is_consistent}), "
                f"peaks={avg_peak_ratio:.3f} (peaky={is_peaky}), "
                f"stability={energy_variation:.3f} (stable={is_stable}) "
                f"→ {is_music_like}"
            )
            
            return is_music_like
            
        except Exception as e:
            logger.error(f"Error in music detection: {e}")
            return True  # Default to music on error (don't filter out)
    
    def has_audio(self) -> Tuple[bool, float]:
        """
        Check if audio is currently being detected.
        
        Returns:
            Tuple of (has_audio: bool, rms_db: float)
        """
        try:
            audio_data = self.capture_audio()
            rms_db = self.calculate_rms_db(audio_data)
            has_audio = rms_db > self.threshold_db
            return has_audio, rms_db
        except Exception as e:
            logger.error(f"Error in has_audio: {e}")
            return False, -np.inf
