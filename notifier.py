#!/usr/bin/env python3
"""
Notification module for PC Audio Monitor.

Two distinct roles:
  - Home Assistant: receives a status update on EVERY poll cycle, always,
                    regardless of alert window. Used as a live dashboard sensor.
  - Pushover:       sends a push notification to your phone ONLY when music
                    has been absent long enough to trigger an alert, and only
                    within the configured time window (EST).

Configure via .env. Both can be active simultaneously.
"""

import logging
import os
import requests
from datetime import datetime, timezone, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Home Assistant — continuous status reporter (not gated by alert window)
# ---------------------------------------------------------------------------

class HomeAssistantNotifier:
    """
    Pushes the current monitoring status to Home Assistant on every poll.

    Uses two HA REST API calls per cycle:
      1. POST /api/events/pc_audio_monitor_status  — fires an event with full detail
      2. POST /api/states/sensor.pc_audio_monitor  — updates a sensor entity so you
         can build dashboards / automations against it in HA

    This runs unconditionally — no time-window gating, no cooldown.
    """

    def __init__(self, host: str, token: str, port: int = 8123, use_https: bool = False):
        scheme = "https" if use_https else "http"
        self.base_url = f"{scheme}://{host}:{port}"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    @classmethod
    def from_env(cls) -> Optional["HomeAssistantNotifier"]:
        host = os.getenv("HA_HOST")
        token = os.getenv("HA_TOKEN")
        if not host or not token:
            return None
        port = int(os.getenv("HA_PORT", "8123"))
        use_https = os.getenv("HA_HTTPS", "false").lower() in ("true", "1", "yes")
        return cls(host, token, port, use_https)

    def update_status(
        self,
        state: str,
        genre: str,
        genre_confidence: float,
        music_confidence: float,
        rms_db: float,
        interruption_seconds: Optional[float] = None,
        alert_after_seconds: int = 180,
        raw_genre: str = "Unknown",
        raw_genre_confidence: float = 0.0,
    ) -> bool:
        """
        Send current poll status to HA. Called every monitoring cycle.

        Args:
            state:                 Current audio state ("music", "not_music", "silence")
            genre:                 Stable genre label (majority-voted)
            genre_confidence:      Genre confidence 0-1
            music_confidence:      Raw music classifier confidence 0-1
            rms_db:                Current RMS level in dB
            interruption_seconds:  Seconds since music stopped (None if music playing)
            alert_after_seconds:   Threshold before alert fires (for progress display)
            raw_genre:             Per-check genre before smoothing
            raw_genre_confidence:  Per-check genre confidence before smoothing
        """
        now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # Alert progress: 0.0 = just stopped, 1.0 = alert about to fire
        if interruption_seconds is not None and alert_after_seconds > 0:
            alert_progress = min(round(interruption_seconds / alert_after_seconds, 2), 1.0)
            alert_remaining = max(int(alert_after_seconds - interruption_seconds), 0)
        else:
            alert_progress = 0.0
            alert_remaining = alert_after_seconds

        attributes = {
            "state": state,
            "genre": genre,
            "genre_confidence": round(float(genre_confidence), 2),
            "raw_genre": raw_genre,
            "raw_genre_confidence": round(float(raw_genre_confidence), 2),
            "music_confidence": round(float(music_confidence), 2),
            "rms_db": round(float(rms_db), 1),
            "alert_progress": float(alert_progress),
            "alert_remaining_seconds": int(alert_remaining),
            "last_updated": now_utc,
            "friendly_name": "PC Audio Monitor",
            "icon": "mdi:music-note" if state == "music" else "mdi:music-note-off",
        }
        if interruption_seconds is not None:
            attributes["interruption_seconds"] = int(interruption_seconds)

        # 1. Main status sensor
        sensor_url = f"{self.base_url}/api/states/sensor.pc_audio_monitor"
        sensor_payload = {
            "state": state,
            "attributes": attributes,
        }

        # 2. Dedicated genre sensor — state IS the genre so HA logs it in history.
        #    When not playing music, state is the audio state (silence / not_music).
        genre_state = genre if state == "music" else state
        genre_sensor_url = f"{self.base_url}/api/states/sensor.pc_audio_monitor_genre"
        genre_sensor_payload = {
            "state": genre_state,
            "attributes": {
                "friendly_name": "PC Audio Genre",
                "icon": "mdi:music-clef-treble",
                "genre_confidence": round(float(genre_confidence), 2),
                "music_state": state,
                "last_updated": now_utc,
            },
        }

        # 3. Music confidence sensor — numeric, good for history graphs and gauges
        confidence_sensor_url = f"{self.base_url}/api/states/sensor.pc_audio_monitor_confidence"
        confidence_sensor_payload = {
            "state": round(float(music_confidence), 2),
            "attributes": {
                "friendly_name": "PC Audio Music Confidence",
                "icon": "mdi:percent",
                "unit_of_measurement": "%",
                "last_updated": now_utc,
            },
        }

        # 4. Event for automations
        event_url = f"{self.base_url}/api/events/pc_audio_monitor_status"
        event_payload = attributes.copy()

        success = True
        for url, payload, label in [
            (sensor_url, sensor_payload, "status sensor"),
            (genre_sensor_url, genre_sensor_payload, "genre sensor"),
            (confidence_sensor_url, confidence_sensor_payload, "confidence sensor"),
            (event_url, event_payload, "event"),
        ]:
            try:
                resp = requests.post(url, json=payload, headers=self.headers, timeout=5)
                resp.raise_for_status()
                logger.debug(f"HA {label} updated: state={state} genre={genre_state}")
            except requests.RequestException as e:
                logger.warning(f"HA {label} update failed: {e}")
                success = False

        return success

    def send_alert(self, reason: str, genre: str, confidence: float) -> bool:
        """
        Fire a dedicated alert event in HA and update a persistent alert sensor.
        The sensor keeps the last alert details visible on the dashboard at all times.
        """
        now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        message = f"Music interrupted: {reason} (was playing {genre})"

        # 1. Fire event (for automations)
        event_url = f"{self.base_url}/api/events/pc_audio_monitor_alert"
        event_payload = {
            "reason": reason,
            "last_genre": genre,
            "genre_confidence": round(float(confidence), 2),
            "message": message,
            "fired_at": now_utc,
        }

        # 2. Persist alert to a sensor so it shows in history and on the dashboard
        sensor_url = f"{self.base_url}/api/states/sensor.pc_audio_monitor_last_alert"
        sensor_payload = {
            "state": reason,   # "silence" or "speech/sound" — shows on timeline
            "attributes": {
                "friendly_name": "PC Audio Last Alert",
                "icon": "mdi:bell-alert",
                "last_genre": genre,
                "genre_confidence": round(float(confidence), 2),
                "message": message,
                "fired_at": now_utc,
            },
        }

        success = True
        for url, payload, label in [
            (event_url, event_payload, "alert event"),
            (sensor_url, sensor_payload, "alert sensor"),
        ]:
            try:
                resp = requests.post(url, json=payload, headers=self.headers, timeout=5)
                resp.raise_for_status()
                logger.info(f"HA {label} updated: {message}")
            except requests.RequestException as e:
                logger.error(f"HA {label} failed: {e}")
                success = False

        return success


# ---------------------------------------------------------------------------
# Pushover — alert-only, gated by time window (EST)
# ---------------------------------------------------------------------------

class PushoverNotifier:
    """
    Sends push notifications to your phone via Pushover.

    Works anywhere — no home network required.
    Free account: 10,000 messages/month.

    Setup:
        1. Sign up at https://pushover.net (free)
        2. Create an app at https://pushover.net/apps/build -> get PUSHOVER_TOKEN
        3. Add to .env:
              PUSHOVER_TOKEN=your_app_api_token
              PUSHOVER_USER=your_user_key
    """

    API_URL = "https://api.pushover.net/1/messages.json"

    def __init__(self, token: str, user_key: str):
        self.token = token
        self.user_key = user_key

    @classmethod
    def from_env(cls) -> Optional["PushoverNotifier"]:
        token = os.getenv("PUSHOVER_TOKEN", "").strip()
        user_key = os.getenv("PUSHOVER_USER", "").strip()
        if not token or not user_key:
            return None
        instance = cls(token, user_key)
        instance._validate()
        return instance

    def _validate(self) -> None:
        """Verify credentials at startup by calling the Pushover validate endpoint."""
        try:
            resp = requests.post(
                "https://api.pushover.net/1/users/validate.json",
                data={"token": self.token, "user": self.user_key},
                timeout=10,
            )
            detail = resp.json()
            if detail.get("status") == 1:
                logger.info("Pushover credentials validated OK")
            else:
                errors = detail.get("errors", ["unknown error"])
                logger.error(
                    f"Pushover credential validation FAILED: {errors} | "
                    f"Check PUSHOVER_TOKEN and PUSHOVER_USER in your .env"
                )
        except Exception as e:
            logger.warning(f"Pushover validation check failed (network issue?): {e}")

    def send_alert(self, reason: str, genre: str, confidence: float) -> bool:
        """Send push notification. Called only when alert threshold is crossed."""
        if reason == "silence":
            title = "Music Stopped"
            message = f"No music detected. Last playing: {genre} ({confidence:.0%})"
        else:
            title = "Music Interrupted"
            message = f"{genre} music interrupted by {reason}"

        payload = {
            "token": self.token,
            "user": self.user_key,
            "title": title,
            "message": message,
            "priority": 0,    # -1=quiet, 0=normal, 1=high, 2=require acknowledgement
            "sound": "none",
        }
        try:
            resp = requests.post(self.API_URL, data=payload, timeout=10)
            if not resp.ok:
                # Pushover returns JSON with an "errors" list explaining the problem
                try:
                    detail = resp.json()
                    errors = detail.get("errors", [resp.text])
                except Exception:
                    errors = [resp.text]
                logger.error(
                    f"Pushover rejected request (HTTP {resp.status_code}): {errors} | "
                    f"Check PUSHOVER_TOKEN and PUSHOVER_USER in your .env"
                )
                return False
            logger.info(f"Pushover alert sent: {title} - {message}")
            return True
        except requests.RequestException as e:
            logger.error(f"Pushover connection error: {e}")
            return False


# ---------------------------------------------------------------------------
# MultiNotifier — coordinates both channels with their separate responsibilities
# ---------------------------------------------------------------------------

class MultiNotifier:
    """
    Coordinates HA (always-on status) and Pushover (alert-only).

    Call update_status() on every poll cycle.
    Call send_alert() only when the alert threshold is crossed (AudioMonitor handles this).
    """

    def __init__(self):
        self.ha = HomeAssistantNotifier.from_env()
        if self.ha:
            logger.info("Home Assistant: enabled (continuous status reporting)")
        else:
            logger.warning("Home Assistant: not configured (HA_HOST / HA_TOKEN missing)")

        self.pushover = PushoverNotifier.from_env()
        if self.pushover:
            logger.info("Pushover: enabled (alert notifications)")
        else:
            logger.info("Pushover: not configured (PUSHOVER_TOKEN / PUSHOVER_USER missing) - skipping")

        if not self.ha and not self.pushover:
            logger.warning("No channels configured. Status and alerts will only be logged.")

    def update_status(
        self,
        state: str,
        genre: str,
        genre_confidence: float,
        music_confidence: float,
        rms_db: float,
        interruption_seconds: Optional[float] = None,
        alert_after_seconds: int = 180,
        raw_genre: str = "Unknown",
        raw_genre_confidence: float = 0.0,
    ) -> None:
        """
        Send live status to HA on every poll. No window gating, no cooldown.
        Pushover is NOT called here.
        """
        if self.ha:
            self.ha.update_status(
                state=state,
                genre=genre,
                genre_confidence=genre_confidence,
                music_confidence=music_confidence,
                rms_db=rms_db,
                interruption_seconds=interruption_seconds,
                alert_after_seconds=alert_after_seconds,
                raw_genre=raw_genre,
                raw_genre_confidence=raw_genre_confidence,
            )

    def send_alert(self, reason: str, genre: str, confidence: float) -> None:
        """
        Fire an alert. Called by AudioMonitor when music has been absent
        long enough. Pushover sends the phone notification; HA also gets
        a dedicated alert event for automations.
        """
        if self.pushover:
            self.pushover.send_alert(reason, genre, confidence)
        if self.ha:
            self.ha.send_alert(reason, genre, confidence)