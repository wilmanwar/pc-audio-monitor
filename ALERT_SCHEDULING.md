# Alert Scheduling Feature

Your app now supports **time-based alert control** - the key feature you requested!

## The Problem You Wanted Solved

> "I don't want to be alerted at 1am"

## The Solution

The `alert_schedule.py` module provides intelligent time-based alert management.

### How It Works

The app checks the current time **before** sending alerts. If the time is outside the configured alert window, the alert is suppressed silently.

### Configuration

Edit `.env` to set your alert window:

```
ALERT_START_HOUR=9
ALERT_END_HOUR=23
```

This means alerts are **active from 9am to 11pm** and suppressed **midnight to 9am**.

### Examples

**No alerts from midnight to 9am** (sleep 12 hours):
```
ALERT_START_HOUR=9
ALERT_END_HOUR=24
```

**Only work hours (9am-5pm)**:
```
ALERT_START_HOUR=9
ALERT_END_HOUR=17
```

**No alerts during dinner (5pm-8pm)**:
```
ALERT_START_HOUR=8
ALERT_END_HOUR=17
ALERT_START_HOUR=20
ALERT_END_HOUR=24
```
(Note: For multiple windows, you'd need to run multiple instances or modify the code)

**Overnight monitoring only (10pm-6am)**:
```
ALERT_START_HOUR=22
ALERT_END_HOUR=6
```

**All day (default, never suppress)**:
```
ALERT_START_HOUR=0
ALERT_END_HOUR=24
```

### What Happens

**Scenario 1: Sound stops at 2:00 PM (within alert window 9-23)**
```
RMS: -45.32 dB | State: sound    | ACTIVE | Current: 14:00 | Window: 09:00 - 23:00
[Sound stops]
RMS: -99.68 dB | State: silence  | ACTIVE | Current: 14:00 | Window: 09:00 - 23:00
ALERT: Sound has stopped! Notifying Home Assistant...
[Notification sent to Home Assistant]
```

**Scenario 2: Sound stops at 1:00 AM (outside alert window 9-23)**
```
RMS: -45.32 dB | State: sound    | INACTIVE | Current: 01:00 | Window: 09:00 - 23:00
[Sound stops]
RMS: -99.68 dB | State: silence  | INACTIVE | Current: 01:00 | Window: 09:00 - 23:00
Alert suppressed (outside alert window): INACTIVE | Current: 01:00 | Window: 09:00 - 23:00
[No notification sent - you stay asleep!]
```

### Log Output Interpretation

When monitoring, you'll see status like:
```
ACTIVE   | Current: 14:00 | Window: 09:00 - 23:00
```
- **ACTIVE** - Alerts would be sent if sound stopped now
- **INACTIVE** - Alerts are blocked by the schedule

```
INACTIVE | Current: 01:00 | Window: 09:00 - 23:00
```
- Currently 1:00 AM
- Alert window is 9am-11pm
- Alerts are NOT active right now

## Implementation Details

The feature is implemented in `alert_schedule.py`:

```python
class AlertSchedule:
    def __init__(self, start_hour=0, end_hour=24):
        # Initialize with alert window
        
    def is_alert_time(self) -> bool:
        # Returns True if current time is in window
        
    def get_status(self) -> str:
        # Returns human-readable status
```

Used in `audio_monitor.py`:

```python
audio_monitor = AudioMonitor(
    on_sound_stopped=notify,
    alert_schedule=alert_schedule  # Pass schedule to monitor
)
```

When sound stops:

```python
def _trigger_alert(self):
    # Check if current time is in alert window
    if not self.alert_schedule.is_alert_time():
        logger.info(f"Alert suppressed: {self.alert_schedule.get_status()}")
        return
    
    # Send alert only if within window
    self.on_sound_stopped()
```

## Advanced Usage

### Weekday/Weekend Differentiation (Optional Enhancement)

To extend this, you could modify `AlertSchedule`:

```python
from datetime import datetime

class AlertSchedule:
    def is_alert_time(self) -> bool:
        now = datetime.now()
        
        # Weekdays: 9am-5pm
        if now.weekday() < 5:  # Monday-Friday
            return 9 <= now.hour < 17
        
        # Weekends: 10am-10pm
        else:  # Saturday-Sunday
            return 10 <= now.hour < 22
```

### Holiday Blackout Dates (Optional Enhancement)

```python
HOLIDAY_DATES = ['2026-12-25', '2026-01-01']  # Christmas, New Year

if datetime.now().strftime('%Y-%m-%d') in HOLIDAY_DATES:
    return False  # Never alert on holidays
```

## Testing the Feature

Test the alert scheduling:

```bash
python -c "
from alert_schedule import AlertSchedule
from datetime import datetime

# Current time
print('Current time:', datetime.now().strftime('%H:%M'))

# Test different schedules
schedules = [
    (0, 24, 'All day'),
    (9, 17, 'Business hours'),
    (9, 23, 'No midnight-9am'),
    (22, 6, 'Overnight only'),
]

for start, end, label in schedules:
    s = AlertSchedule(start, end)
    print(f'{label:20s} {s.get_status()}')
"
```

## Summary

You now have full control over when the app sends alerts:

- **No midnight interruptions** - Set ALERT_START_HOUR=9
- **Work hours only** - Set ALERT_START_HOUR=9, ALERT_END_HOUR=17
- **Custom windows** - Set any start/end hour (0-23)
- **Status logging** - See current alert status in real-time logs

The app monitors audio 24/7, but only alerts during your configured window!

---

See `.env.example` for configuration options and SETUP.md for examples.
