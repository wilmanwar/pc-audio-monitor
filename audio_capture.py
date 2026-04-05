"""Audio capture module for detecting system audio levels."""

import sounddevice as sd
import numpy as np
import logging
import os
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


class AudioCapture:
    """Captures and analyzes system audio using WASAPI loopback."""

    def __init__(self, threshold_db: float = -50, duration: float = 2.0,
                 samplerate: int = 44100, auto_detect: bool = False,
                 silence_threshold_db: float = -75):
        """
        Args:
            threshold_db:          Low-volume warning level in dB. Audio below
                                   this is still classified (may be quiet music).
                                   Used for logging only (default -50).
            silence_threshold_db:  True silence threshold. Below this the signal
                                   is device noise floor — skip classifier entirely
                                   (default -75).
        """
        self.threshold_db = threshold_db
        self.silence_threshold_db = silence_threshold_db
        self.duration = duration
        self.samplerate = samplerate
        self.device_id = None

        if auto_detect:
            self.device_id = self._auto_detect_active_audio()

        if self.device_id is None:
            self.device_id = self._find_loopback_device()

        if self.device_id is not None:
            self._query_device_samplerate()

    def _auto_detect_active_audio(self) -> Optional[int]:
        logger.info("=" * 80)
        logger.info("AUTO-DETECTING ACTIVE AUDIO SOURCE")
        logger.info("=" * 80)
        logger.info("Scanning audio devices for active sound...")
        logger.info("Please keep your music/audio playing.")
        logger.info("")

        devices = sd.query_devices()
        device_levels = {}

        priority_names = [
            'voicemeeter point',
            'stereo mix',
            'what u hear',
            'wave out mix',
            'loopback',
            'voicemeeter out',
            'cable output',
            'microphone',
        ]

        candidates = []
        for priority_name in priority_names:
            for idx, device in enumerate(devices):
                if device['max_input_channels'] == 0:
                    continue
                if priority_name.lower() in device['name'].lower():
                    candidates.append((idx, device['name']))

        tested = set()
        for idx, device_name in candidates:
            if idx in tested:
                continue
            tested.add(idx)

            short_name = device_name[:50] if len(device_name) > 50 else device_name
            logger.info(f"Testing [{idx:3d}] {short_name:50s} - Testing...")

            try:
                audio_data = sd.rec(
                    int(44100 * 0.5),
                    samplerate=44100,
                    channels=2,
                    device=idx,
                    dtype='float32',
                    blocksize=2048
                )
                sd.wait(timeout=2.0)

                if audio_data.ndim > 1:
                    audio_data = np.mean(audio_data, axis=1)
                rms = np.sqrt(np.mean(np.square(audio_data)))
                rms_db = 20 * np.log10(rms) if rms > 0 else -np.inf
                device_levels[idx] = (device_name, rms_db)
                logger.info(f"  Result: {rms_db:7.1f} dB")
            except Exception as e:
                logger.info(f"  Skipped ({type(e).__name__})")

        logger.info("")

        if not device_levels:
            logger.warning("Auto-detect failed on all devices. Using priority-based selection instead.")
            return None

        active_devices = [
            (idx, name, level)
            for idx, (name, level) in device_levels.items()
            if level > -np.inf and level > -60
        ]

        if not active_devices:
            logger.warning("No active audio detected above -60 dB threshold.")
            logger.info("Using priority-based device selection instead.")
            return None

        active_devices.sort(key=lambda x: x[2], reverse=True)
        best_idx, best_name, best_level = active_devices[0]

        logger.info("=" * 80)
        logger.info("ACTIVE AUDIO AUTO-DETECTED!")
        logger.info(f"Device ID {best_idx}: {best_name}")
        logger.info(f"Audio Level: {best_level:.1f} dB")
        logger.info("=" * 80)
        logger.info("")

        return best_idx

    def _find_loopback_device(self) -> Optional[int]:
        try:
            device_override = os.getenv('AUDIO_DEVICE_ID')
            if device_override and device_override.isdigit():
                logger.info(f"Using override device from AUDIO_DEVICE_ID: {device_override}")
                return int(device_override)

            devices = sd.query_devices()
            logger.info("Available audio devices:")
            for idx, device in enumerate(devices):
                logger.info(f"  [{idx}] {device['name']} (in: {device['max_input_channels']}, out: {device['max_output_channels']})")

            priority_keywords = [
                ('stereo mix', 1),
                ('wave out mix', 1),
                ('what u hear', 1),
                ('loopback', 1),
                ('wasapi', 1),
                ('cable', 2),
            ]

            best_device = None
            best_priority = 999

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
                device_type = "Stereo Mix" if best_priority == 1 else "VB-Audio Cable"
                logger.info(f"Found {device_type}: {device_name} (ID: {best_device})")
                return best_device

            try:
                default_input, default_output = sd.default.device
            except (TypeError, ValueError):
                default_input = sd.default.device

            if default_input is not None and isinstance(default_input, int) and default_input >= 0:
                logger.warning("Stereo Mix / VB-Audio Cable device not found.")
                logger.warning("Using default input device as fallback (usually microphone).")
                default_info = devices[default_input]
                logger.info(f"Using fallback device: {default_info['name']} (ID: {default_input})")
                return default_input

            logger.error("No suitable audio input device found!")
            return None

        except Exception as e:
            logger.error(f"Error finding loopback device: {e}")
            return None

    def _query_device_samplerate(self) -> None:
        try:
            device_info = sd.query_devices(self.device_id)
            default_sr = device_info.get('default_samplerate', 44100)
            self.samplerate = int(default_sr)
            logger.info(f"Device {self.device_id} using sample rate: {self.samplerate} Hz")
        except Exception as e:
            logger.warning(f"Could not query device sample rate, using default 44100: {e}")

    def capture_audio(self) -> np.ndarray:
        """Capture audio from loopback device, trying channel configs until one works."""
        if self.device_id is None:
            raise RuntimeError("No loopback device found. Please enable Stereo Mix on your audio device.")

        try:
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
                    logger.debug(f"Recording complete: shape={audio_data.shape}")
                    return audio_data
                except Exception as e:
                    logger.debug(f"{channels}-channel recording failed: {e}")
                    continue

            raise RuntimeError(f"Could not capture audio from device {self.device_id}")

        except Exception as e:
            logger.error(f"Error capturing audio: {e}")
            raise

    def capture_raw(self) -> np.ndarray:
        """
        Capture audio and return as a flat mono float32 array for classification.

        Reuses capture_audio() (which handles device selection and channel
        fallback) and converts the result to mono.

        Returns:
            1-D float32 numpy array, empty array on failure.
        """
        try:
            audio_data = self.capture_audio()
            if audio_data.ndim > 1:
                audio_data = np.mean(audio_data, axis=1)
            return audio_data.astype(np.float32)
        except Exception as e:
            logger.error(f"capture_raw failed: {e}")
            return np.array([], dtype=np.float32)

    def calculate_rms_db(self, audio_data: np.ndarray) -> float:
        """Calculate RMS level in dB."""
        if audio_data.ndim > 1:
            audio_data = np.mean(audio_data, axis=1)

        rms = np.sqrt(np.mean(np.square(audio_data)))
        if rms > 0:
            rms_db = 20 * np.log10(rms)
        else:
            rms_db = -np.inf

        logger.debug(f"RMS level: {rms_db:.2f} dB (silence threshold: {self.silence_threshold_db} dB)")
        return float(rms_db)

    def capture_and_analyze(self) -> Tuple[bool, bool, float, np.ndarray]:
        """
        Capture one audio chunk and return everything main.py needs.

        Audio is captured ONCE and reused for both the RMS check and
        the classifier — avoids capturing two separate chunks per cycle.

        Two thresholds:
          silence_threshold_db: True silence / device noise floor (default -75 dB).
              Below this = no signal worth analyzing at all.
          threshold_db:         Low-volume warning level (default -50 dB).
              Audio below this is still classified — it may be quiet music.
              The value is passed through so callers can log it, but it does
              NOT block classification.

        Returns:
            has_any_audio:  False only when RMS is below silence_threshold_db
            is_low_volume:  True when RMS is between silence and threshold_db
                            (quiet but not silent — useful for logging)
            rms_db:         RMS level in dB
            raw_audio:      Flat mono float32 array ready for the classifier
                            (empty array if capture failed)
        """
        try:
            audio_data = self.capture_audio()
            rms_db = self.calculate_rms_db(audio_data)

            has_any_audio = rms_db > self.silence_threshold_db
            is_low_volume = has_any_audio and (rms_db <= self.threshold_db)

            if has_any_audio:
                if audio_data.ndim > 1:
                    raw = np.mean(audio_data, axis=1).astype(np.float32)
                else:
                    raw = audio_data.astype(np.float32)
            else:
                raw = np.array([], dtype=np.float32)

            return has_any_audio, is_low_volume, rms_db, raw

        except Exception as e:
            logger.error(f"Error in capture_and_analyze: {e}")
            return False, False, -np.inf, np.array([], dtype=np.float32)

    def has_audio(self) -> Tuple[bool, float]:
        """
        Legacy method kept for compatibility.
        Prefer capture_and_analyze() for new code.
        """
        try:
            audio_data = self.capture_audio()
            rms_db = self.calculate_rms_db(audio_data)
            has_audio = rms_db > self.silence_threshold_db
            return has_audio, rms_db
        except Exception as e:
            logger.error(f"Error in has_audio: {e}")
            return False, -np.inf