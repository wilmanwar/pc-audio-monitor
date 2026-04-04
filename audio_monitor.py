"""State machine for tracking audio state and managing transitions."""

import logging
from enum import Enum
from typing import Callable, Optional
from datetime import datetime, timedelta
from alert_schedule import AlertSchedule

logger = logging.getLogger(__name__)


class AudioState(Enum):
    """Possible audio states."""
    SOUND = "sound"
    SILENCE = "silence"
    UNKNOWN = "unknown"


class AudioMonitor:
    """Tracks audio state and triggers alerts on music-to-silence transitions."""
    
    def __init__(
        self,
        on_sound_stopped: Callable[[], None],
        cooldown_seconds: int = 60,
        initial_state: AudioState = AudioState.UNKNOWN,
        alert_schedule: Optional[AlertSchedule] = None
    ):
        """
        Initialize the monitor.
        
        Args:
            on_sound_stopped: Callback function to execute when sound stops
            cooldown_seconds: Minimum seconds between alerts (prevents spam)
            initial_state: Starting state (UNKNOWN means we'll detect it on first check)
            alert_schedule: AlertSchedule object for time-based alert control (optional)
        """
        self.on_sound_stopped = on_sound_stopped
        self.cooldown_seconds = cooldown_seconds
        self.current_state = initial_state
        self.last_alert_time = None
        self.alert_schedule = alert_schedule or AlertSchedule()
        
    def update(self, has_audio: bool) -> None:
        """
        Update the monitor with new audio detection status.
        
        Triggers alert if: sound was present, now is silence, and cooldown expired.
        
        Args:
            has_audio: Whether audio is currently detected
        """
        new_state = AudioState.SOUND if has_audio else AudioState.SILENCE
        
        # Check for state transition
        if self.current_state == AudioState.SOUND and new_state == AudioState.SILENCE:
            logger.info("Audio state changed: SOUND -> SILENCE")
            self._trigger_alert()
        
        if new_state != self.current_state:
            logger.info(f"Audio state: {new_state.value}")
            self.current_state = new_state
    
    def _trigger_alert(self) -> None:
        """Trigger alert if cooldown has expired and alert time is active."""
        # Check if alerts are enabled by schedule
        if not self.alert_schedule.is_alert_time():
            logger.info(f"Alert suppressed (outside alert window): {self.alert_schedule.get_status()}")
            return
        
        now = datetime.now()
        
        # Check cooldown
        if self.last_alert_time is not None:
            time_since_last_alert = (now - self.last_alert_time).total_seconds()
            if time_since_last_alert < self.cooldown_seconds:
                logger.debug(f"Alert in cooldown ({time_since_last_alert:.0f}s / {self.cooldown_seconds}s)")
                return
        
        # Execute callback
        try:
            logger.info("ALERT: Sound has stopped! Notifying Home Assistant...")
            self.on_sound_stopped()
            self.last_alert_time = now
        except Exception as e:
            logger.error(f"Error executing alert callback: {e}", exc_info=True)
