"""Time-based alert scheduling for controlling when alerts are active."""

import logging
from datetime import datetime
from typing import Tuple

logger = logging.getLogger(__name__)


class AlertSchedule:
    """Manages alert availability based on time of day."""
    
    def __init__(self, start_hour: int = 0, end_hour: int = 24):
        """
        Initialize alert schedule.
        
        Args:
            start_hour: Hour when alerts start (0-23, inclusive)
            end_hour: Hour when alerts end (1-24, inclusive). 
                      Use 24 for inclusive until midnight.
        
        Examples:
            AlertSchedule(8, 22)   # 8am to 10pm
            AlertSchedule(9, 17)   # 9am to 5pm
            AlertSchedule(22, 6)   # 10pm to 6am (overnight)
            AlertSchedule(0, 24)   # All day (default)
        """
        if not (0 <= start_hour <= 23):
            raise ValueError(f"start_hour must be 0-23, got {start_hour}")
        if not (1 <= end_hour <= 24):
            raise ValueError(f"end_hour must be 1-24, got {end_hour}")
        
        # Note: end_hour == start_hour is invalid (would exclude all hours)
        
        self.start_hour = start_hour
        self.end_hour = end_hour
    
    def is_alert_time(self) -> bool:
        """
        Check if current time is within alert window.
        
        Returns:
            True if alerts are enabled, False otherwise
        """
        now = datetime.now()
        current_hour = now.hour
        
        # Handle same-day range (e.g., 9am-5pm)
        if self.start_hour < self.end_hour:
            is_active = self.start_hour <= current_hour < self.end_hour
        # Handle overnight range (e.g., 9pm-6am)
        else:
            is_active = current_hour >= self.start_hour or current_hour < self.end_hour
        
        return is_active
    
    def get_status(self) -> str:
        """Get human-readable status string."""
        now = datetime.now()
        current_hour = now.hour
        
        if self.start_hour < self.end_hour:
            window = f"{self.start_hour:02d}:00 - {self.end_hour:02d}:00"
        else:
            window = f"{self.start_hour:02d}:00 - {self.end_hour:02d}:00 (overnight)"
        
        status = "ACTIVE" if self.is_alert_time() else "INACTIVE"
        current = f"{current_hour:02d}:00"
        
        return f"{status} | Current: {current} | Window: {window}"
    
    @staticmethod
    def from_env(start_env: str = 'ALERT_START_HOUR', end_env: str = 'ALERT_END_HOUR') -> 'AlertSchedule':
        """
        Create schedule from environment variables.
        
        Args:
            start_env: Environment variable name for start hour (default: ALERT_START_HOUR)
            end_env: Environment variable name for end hour (default: ALERT_END_HOUR)
        
        Returns:
            AlertSchedule instance with defaults if env vars not set
        """
        import os
        
        start = int(os.getenv(start_env, '0'))
        end = int(os.getenv(end_env, '24'))
        
        return AlertSchedule(start_hour=start, end_hour=end)
