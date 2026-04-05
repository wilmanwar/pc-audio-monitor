"""Time-based alert scheduling — window hours are always interpreted as EST."""

import logging
import os
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

# EST = UTC-5, EDT = UTC-4.
# We use Python's built-in datetime to compute the current EST time without
# requiring pytz or zoneinfo (which may not be available on all Windows installs).
# DST in the US: second Sunday in March -> first Sunday in November.

def _now_est() -> datetime:
    """Return the current time as a naive datetime in US/Eastern (EST/EDT)."""
    utc_now = datetime.now(timezone.utc)

    # Determine DST offset for US Eastern:
    #   EDT (UTC-4): second Sun in March 02:00 -> first Sun in November 02:00
    #   EST (UTC-5): everything else
    year = utc_now.year

    # Second Sunday in March
    march1 = datetime(year, 3, 1, tzinfo=timezone.utc)
    # weekday(): Monday=0 ... Sunday=6
    days_to_sunday = (6 - march1.weekday()) % 7
    dst_start = march1 + timedelta(days=days_to_sunday + 7, hours=7)  # 02:00 EST = 07:00 UTC

    # First Sunday in November
    nov1 = datetime(year, 11, 1, tzinfo=timezone.utc)
    days_to_sunday = (6 - nov1.weekday()) % 7
    dst_end = nov1 + timedelta(days=days_to_sunday, hours=6)  # 02:00 EDT = 06:00 UTC

    if dst_start <= utc_now < dst_end:
        offset = timedelta(hours=-4)  # EDT
        tz_label = "EDT"
    else:
        offset = timedelta(hours=-5)  # EST
        tz_label = "EST"

    est_now = (utc_now + offset).replace(tzinfo=None)  # naive, in Eastern time
    return est_now


class AlertSchedule:
    """Manages Pushover alert availability based on time of day in EST."""

    def __init__(self, start_hour: int = 0, end_hour: int = 24):
        """
        Args:
            start_hour: Hour (EST) when alerts start (0-23, inclusive)
            end_hour:   Hour (EST) when alerts end (1-24, inclusive).
                        Use 24 to mean "until midnight".
        Examples:
            AlertSchedule(9, 17)   # 9am-5pm EST
            AlertSchedule(22, 6)   # 10pm-6am EST (overnight)
            AlertSchedule(0, 24)   # All day (default)
        """
        if not (0 <= start_hour <= 23):
            raise ValueError(f"start_hour must be 0-23, got {start_hour}")
        if not (1 <= end_hour <= 24):
            raise ValueError(f"end_hour must be 1-24, got {end_hour}")

        self.start_hour = start_hour
        self.end_hour = end_hour

    def is_alert_time(self) -> bool:
        """Return True if the current EST time is within the alert window."""
        current_hour = _now_est().hour

        if self.start_hour < self.end_hour:
            # Same-day range e.g. 9-17
            return self.start_hour <= current_hour < self.end_hour
        else:
            # Overnight range e.g. 22-6
            return current_hour >= self.start_hour or current_hour < self.end_hour

    def get_status(self) -> str:
        """Human-readable status string showing EST time."""
        est_now = _now_est()
        current_str = est_now.strftime("%H:%M EST")

        if self.start_hour < self.end_hour:
            window = f"{self.start_hour:02d}:00-{self.end_hour:02d}:00 EST"
        else:
            window = f"{self.start_hour:02d}:00-{self.end_hour:02d}:00 EST (overnight)"

        status = "ACTIVE" if self.is_alert_time() else "INACTIVE"
        return f"{status} | Now: {current_str} | Window: {window}"

    @staticmethod
    def from_env(
        start_env: str = 'ALERT_START_HOUR',
        end_env: str = 'ALERT_END_HOUR'
    ) -> 'AlertSchedule':
        """Create from environment variables (hours interpreted as EST)."""
        start = int(os.getenv(start_env, '0'))
        end = int(os.getenv(end_env, '24'))
        return AlertSchedule(start_hour=start, end_hour=end)
