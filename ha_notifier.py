"""Home Assistant integration for sending notifications."""

import logging
import os
from typing import Optional
import requests

logger = logging.getLogger(__name__)


class HomeAssistantNotifier:
    """Sends notifications to Home Assistant."""
    
    def __init__(
        self,
        host: str,
        port: int = 8123,
        token: str = "",
        use_https: bool = False,
        notify_service: str = "notify.notify"
    ):
        """
        Initialize Home Assistant notifier.
        
        Args:
            host: Home Assistant IP or hostname
            port: Port (usually 8123)
            token: Long-lived access token
            use_https: Use HTTPS instead of HTTP
            notify_service: Notification service name (e.g., 'notify.notify')
        """
        self.host = host
        self.port = port
        self.token = token
        self.notify_service = notify_service
        self.protocol = "https" if use_https else "http"
        self.base_url = f"{self.protocol}://{host}:{port}/api"
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        })
    
    def send_alert(
        self,
        title: str = "PC Audio Alert",
        message: str = "Sound has stopped"
    ) -> bool:
        """
        Send notification to Home Assistant.
        
        Args:
            title: Notification title
            message: Notification message
            
        Returns:
            True if successful, False otherwise
        """
        try:
            url = f"{self.base_url}/services/{self.notify_service.replace('.', '/')}"
            payload = {
                "title": title,
                "message": message
            }
            
            logger.debug(f"Sending to {url}: {payload}")
            response = self.session.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"Alert sent successfully")
                return True
            else:
                logger.error(f"Failed to send alert: HTTP {response.status_code} - {response.text}")
                return False
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error to Home Assistant: {e}")
            return False
        except requests.exceptions.Timeout:
            logger.error("Timeout connecting to Home Assistant")
            return False
        except Exception as e:
            logger.error(f"Error sending notification: {e}", exc_info=True)
            return False
    
    @staticmethod
    def from_env() -> Optional['HomeAssistantNotifier']:
        """
        Create notifier from environment variables.
        
        Expected variables:
            HA_HOST: Home Assistant IP/hostname
            HA_PORT: Port (default 8123)
            HA_TOKEN: Long-lived access token
            HA_NOTIFY_SERVICE: Service name (default notify.notify)
        
        Returns:
            HomeAssistantNotifier instance or None if required vars missing
        """
        host = os.getenv('HA_HOST')
        if not host:
            logger.error("HA_HOST environment variable not set")
            return None
        
        token = os.getenv('HA_TOKEN')
        if not token:
            logger.error("HA_TOKEN environment variable not set")
            return None
        
        port = int(os.getenv('HA_PORT', '8123'))
        notify_service = os.getenv('HA_NOTIFY_SERVICE', 'notify.notify')
        
        return HomeAssistantNotifier(
            host=host,
            port=port,
            token=token,
            notify_service=notify_service
        )
