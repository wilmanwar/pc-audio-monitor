#!/usr/bin/env python3
"""
Notification module for PC Audio Monitor.

Supports:
  - Home Assistant (local network or Nabu Casa cloud)
  - Pushover (push notifications to phone — works anywhere, no home network needed)

Configure via .env file. Both can be active simultaneously.
"""

import logging
import os
import requests
from typing import Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Home Assistant
# ---------------------------------------------------------------------------

class HomeAssistantNotifier:
    """Send alerts to Home Assistant via REST API."""

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

    def send_alert(self, reason: str, genre: str, confidence: float) -> bool:
        """
        Fire a Home Assistant event and update an input_boolean.

        Args:
            reason: Why the alert fired ("silence" or "speech/ad")
            genre: Last detected music genre
            confidence: Genre confidence 0-1
        """
        url = f"{self.base_url}/api/events/pc_audio_monitor_alert"
        payload = {
            "reason": reason,
            "last_genre": genre,
            "genre_confidence": round(confidence, 2),
            "message": f"Music interrupted: {reason} detected (was playing {genre})"
        }
        try:
            resp = requests.post(url, json=payload, headers=self.headers, timeout=10)
            resp.raise_for_status()
            logger.info(f"Home Assistant alert sent: {payload['message']}")
            return True
        except requests.RequestException as e:
            logger.error(f"Home Assistant alert failed: {e}")
            return False


# ---------------------------------------------------------------------------
# Pushover  (https://pushover.net — free tier: 10,000 msgs/month)
# ---------------------------------------------------------------------------

class PushoverNotifier:
    """
    Send push notifications via Pushover.

    Works anywhere — no home network required, delivers to your phone even
    when you're away. Free account supports up to 10,000 messages/month.

    Setup:
        1. Sign up at https://pushover.net (free)
        2. Create an Application/API token at https://pushover.net/apps/build
        3. Add to .env:
              PUSHOVER_TOKEN=your_app_token
              PUSHOVER_USER=your_user_key
    """

    API_URL = "https://api.pushover.net/1/messages.json"

    def __init__(self, token: str, user_key: str):
        self.token = token
        self.user_key = user_key

    @classmethod
    def from_env(cls) -> Optional["PushoverNotifier"]:
        token = os.getenv("PUSHOVER_TOKEN")
        user_key = os.getenv("PUSHOVER_USER")
        if not token or not user_key:
            return None
        return cls(token, user_key)

    def send_alert(self, reason: str, genre: str, confidence: float) -> bool:
        """
        Send push notification to your phone.

        Args:
            reason: "silence" or "speech/ad"
            genre: Last detected music genre
            confidence: Genre confidence 0-1
        """
        if reason == "silence":
            title = "🎵 Music Stopped"
            message = f"Music stopped playing. Last genre: {genre} ({confidence:.0%} confidence)"
        else:
            title = "📢 Music Interrupted"
            message = f"{genre} music was interrupted by {reason}"

        payload = {
            "token": self.token,
            "user": self.user_key,
            "title": title,
            "message": message,
            "priority": 0,   # -1=quiet, 0=normal, 1=high, 2=require ack
            "sound": "none",  # or "pushover", "classical", etc.
        }
        try:
            resp = requests.post(self.API_URL, data=payload, timeout=10)
            resp.raise_for_status()
            logger.info(f"Pushover alert sent: {title} — {message}")
            return True
        except requests.RequestException as e:
            logger.error(f"Pushover alert failed: {e}")
            return False


# ---------------------------------------------------------------------------
# Combined notifier — fires all configured channels
# ---------------------------------------------------------------------------

class MultiNotifier:
    """Wraps multiple notifiers; fires all that are configured."""

    def __init__(self):
        self.notifiers = []
        ha = HomeAssistantNotifier.from_env()
        if ha:
            self.notifiers.append(ha)
            logger.info("Home Assistant notifier enabled")
        else:
            logger.warning("Home Assistant not configured (HA_HOST / HA_TOKEN missing)")

        po = PushoverNotifier.from_env()
        if po:
            self.notifiers.append(po)
            logger.info("Pushover notifier enabled")
        else:
            logger.info("Pushover not configured (PUSHOVER_TOKEN / PUSHOVER_USER missing) — skipping")

        if not self.notifiers:
            logger.warning("No notification channels configured. Alerts will only be logged.")

    def send_alert(self, reason: str, genre: str, confidence: float) -> None:
        """Fire all configured notifiers."""
        for notifier in self.notifiers:
            notifier.send_alert(reason, genre, confidence)
