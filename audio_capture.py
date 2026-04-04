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
        self.device_id = self._find_loopback_device()
        
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
                # Stereo Mix variants
                ('stereo mix', 1),
                ('wave out mix', 1),
                ('what u hear', 1),
                ('loopback', 1),
                ('wasapi', 1),
                # Virtual audio cables
                ('vb-audio', 2),
                ('virtual cable', 2),
                ('voicemeeter', 2),
                ('virtual audio', 2),
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
