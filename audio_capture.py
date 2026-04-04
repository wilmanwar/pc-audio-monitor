"""Audio capture module for detecting system audio levels."""

import sounddevice as sd
import numpy as np
import logging
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
        self.device_id = self._find_loopback_device()
        
    def _find_loopback_device(self) -> Optional[int]:
        """
        Find the WASAPI loopback device (Stereo Mix).
        Falls back to default input device if Stereo Mix not found.
        
        Returns:
            Device ID if found, None otherwise
        """
        try:
            devices = sd.query_devices()
            logger.info("Available audio devices:")
            for idx, device in enumerate(devices):
                logger.info(f"  [{idx}] {device['name']} (in: {device['max_input_channels']}, out: {device['max_output_channels']})")
            
            # Try to find Stereo Mix or loopback device
            for idx, device in enumerate(devices):
                name = device['name'].lower()
                if any(term in name for term in ['stereo mix', 'loopback', 'what u hear', 'wave out mix', 'virtual audio cable']):
                    if device['max_input_channels'] > 0:
                        logger.info(f"Found loopback device: {device['name']} (ID: {idx})")
                        return idx
            
            # Fallback to default input device
            try:
                default_input, default_output = sd.default.device
            except (TypeError, ValueError):
                default_input = sd.default.device
            
            if default_input is not None and isinstance(default_input, int) and default_input >= 0:
                logger.warning("Stereo Mix not found. Using default input device as fallback.")
                logger.warning("For best results, enable Stereo Mix on your audio device:")
                logger.warning("  1. Right-click speaker icon > Sound settings")
                logger.warning("  2. Advanced > Volume mixer")
                logger.warning("  3. Enable 'Stereo Mix' or 'WASAPI Loopback'")
                default_info = devices[default_input]
                logger.info(f"Using fallback device: {default_info['name']} (ID: {default_input})")
                return default_input
            
            logger.error("No suitable audio input device found!")
            return None
        except Exception as e:
            logger.error(f"Error finding loopback device: {e}")
            return None
    
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
            audio_data = sd.rec(
                int(self.samplerate * self.duration),
                samplerate=self.samplerate,
                channels=2,
                device=self.device_id,
                dtype='float32'
            )
            sd.wait()
            logger.debug(f"Recording complete. Shape: {audio_data.shape}, dtype: {audio_data.dtype}")
            return audio_data
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
