"""State machine for tracking audio state and managing transitions."""
import logging
from collections import deque, Counter
from enum import Enum
from typing import Callable, Optional, Deque, Tuple
from datetime import datetime
from alert_schedule import AlertSchedule

logger = logging.getLogger(__name__)


class AudioState(Enum):
    """Possible audio states."""
    MUSIC = "music"        # Music detected
    NOT_MUSIC = "not_music"  # Sound present but not music (speech, noise, ads)
    SILENCE = "silence"    # No audio above threshold
    UNKNOWN = "unknown"    # Initial state before first detection


class AudioMonitor:
    """
    Tracks audio state and fires an alert when music has been absent
    (silence or non-music) for a configurable number of seconds.

    Genre is reported as a rolling majority vote over recent checks so it
    stays stable rather than flipping every 5 seconds.
    """

    def __init__(
        self,
        on_music_interrupted: Callable[[str, str, float], None],
        cooldown_seconds: int = 300,
        alert_after_seconds: int = 180,
        genre_window: int = 12,
        initial_state: AudioState = AudioState.UNKNOWN,
        alert_schedule: Optional[AlertSchedule] = None,
    ):
        """
        Args:
            on_music_interrupted: Callback(reason, stable_genre, genre_confidence).
                Called once music has been absent for alert_after_seconds.
            cooldown_seconds: Minimum gap between successive alerts (default 5 min).
            alert_after_seconds: How long music must be absent before alerting
                (default 180 s = 3 minutes).
            genre_window: Number of recent checks used for the rolling genre vote
                (default 12; at 5-s intervals that's the last 60 seconds).
            initial_state: Starting state.
            alert_schedule: AlertSchedule for time-of-day gating.
        """
        self.on_music_interrupted = on_music_interrupted
        self.cooldown_seconds = cooldown_seconds
        self.alert_after_seconds = alert_after_seconds
        self.current_state = initial_state
        self.last_alert_time: Optional[datetime] = None
        self.alert_schedule = alert_schedule or AlertSchedule()

        # --- Genre rolling window ---
        # Stores (genre, confidence) tuples for the last `genre_window` music checks.
        self._genre_window: int = genre_window
        self._genre_history: Deque[Tuple[str, float]] = deque(maxlen=genre_window)

        # --- Prolonged-interruption timer ---
        # Set to datetime when music first stops; cleared when music resumes.
        self._interruption_since: Optional[datetime] = None
        self._interruption_reason: str = "unknown"
        self._alert_fired_for_current_interruption: bool = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update(self, has_audio: bool, is_music: bool, music_confidence: float,
               genre: str, genre_confidence: float) -> None:
        """
        Feed the latest classification result into the monitor.

        Args:
            has_audio: True if RMS is above the silence threshold.
            is_music: True if the classifier identified music.
            music_confidence: Classifier confidence 0-1.
            genre: Raw per-check genre string.
            genre_confidence: Per-check genre confidence 0-1.
        """
        # --- Determine the new raw state ---
        if not has_audio:
            new_state = AudioState.SILENCE
        elif is_music:
            new_state = AudioState.MUSIC
        else:
            new_state = AudioState.NOT_MUSIC

        # --- Update genre history when music is playing ---
        if new_state == AudioState.MUSIC:
            self._genre_history.append((genre, genre_confidence))

        stable_genre, stable_conf = self._stable_genre()

        # --- Handle state transitions ---
        if new_state != self.current_state:
            logger.info(
                f"Audio state: {self.current_state.value} -> {new_state.value} "
                f"| raw_genre={genre} ({genre_confidence:.0%}) "
                f"| stable_genre={stable_genre} ({stable_conf:.0%}) "
                f"| music_conf={music_confidence:.2f}"
            )

        if new_state == AudioState.MUSIC:
            # Music is back — cancel any pending interruption timer
            if self._interruption_since is not None:
                elapsed = (datetime.now() - self._interruption_since).total_seconds()
                logger.info(
                    f"Music resumed after {elapsed:.0f}s of {self._interruption_reason}. "
                    f"No alert fired." if not self._alert_fired_for_current_interruption
                    else f"Music resumed after {elapsed:.0f}s."
                )
                self._interruption_since = None
                self._alert_fired_for_current_interruption = False
        else:
            # Not music (silence or non-music)
            reason = "silence" if new_state == AudioState.SILENCE else "speech/sound"

            if self._interruption_since is None:
                # Music just stopped — start the timer
                if self.current_state == AudioState.MUSIC:
                    self._interruption_since = datetime.now()
                    self._interruption_reason = reason
                    self._alert_fired_for_current_interruption = False
                    logger.info(
                        f"Music stopped ({reason}). "
                        f"Alert will fire if no music for {self.alert_after_seconds}s."
                    )
                elif self.current_state == AudioState.UNKNOWN:
                    # App just started and there's no music — don't alert until
                    # we've seen music at least once.
                    pass
            else:
                # Timer already running — update reason if it changed
                if reason != self._interruption_reason:
                    logger.info(f"Interruption type changed: {self._interruption_reason} -> {reason}")
                    self._interruption_reason = reason

                # Check whether we've passed the alert threshold
                elapsed = (datetime.now() - self._interruption_since).total_seconds()
                remaining = self.alert_after_seconds - elapsed
                if not self._alert_fired_for_current_interruption:
                    if elapsed >= self.alert_after_seconds:
                        self._trigger_alert(self._interruption_reason, stable_genre, stable_conf)
                    else:
                        logger.debug(
                            f"Interruption timer: {elapsed:.0f}s / {self.alert_after_seconds}s "
                            f"({remaining:.0f}s remaining)"
                        )

        self.current_state = new_state

    def stable_genre_summary(self) -> str:
        """Return a human-readable summary of the current stable genre."""
        genre, conf = self._stable_genre()
        if not genre:
            return "No genre data yet"
        return f"{genre} ({conf:.0%} avg confidence, last {len(self._genre_history)} checks)"

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _stable_genre(self) -> Tuple[str, float]:
        """
        Compute the stable genre using a majority vote over the rolling window.

        Returns the most common genre in recent history along with the average
        confidence for that genre across the window.
        """
        if not self._genre_history:
            return "Unknown", 0.0

        # Count votes
        genre_votes = Counter(g for g, _ in self._genre_history)
        top_genre = genre_votes.most_common(1)[0][0]

        # Average confidence for the winning genre
        confs = [c for g, c in self._genre_history if g == top_genre]
        avg_conf = sum(confs) / len(confs) if confs else 0.0

        return top_genre, avg_conf

    def _trigger_alert(self, reason: str, genre: str, confidence: float) -> None:
        """Fire the alert callback if schedule and cooldown allow."""
        if not self.alert_schedule.is_alert_time():
            logger.info(f"Alert suppressed (outside alert window): {self.alert_schedule.get_status()}")
            return

        now = datetime.now()
        if self.last_alert_time is not None:
            elapsed = (now - self.last_alert_time).total_seconds()
            if elapsed < self.cooldown_seconds:
                logger.debug(f"Alert in cooldown ({elapsed:.0f}s / {self.cooldown_seconds}s)")
                return

        elapsed_since_stop = (
            (now - self._interruption_since).total_seconds()
            if self._interruption_since else 0
        )

        try:
            logger.info(
                f"ALERT: No music for {elapsed_since_stop:.0f}s "
                f"(reason={reason}, last genre={genre} {confidence:.0%})"
            )
            self.on_music_interrupted(reason, genre, confidence)
            self.last_alert_time = now
            self._alert_fired_for_current_interruption = True
        except Exception as e:
            logger.error(f"Error executing alert callback: {e}", exc_info=True)
