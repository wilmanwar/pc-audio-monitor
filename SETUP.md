# PC Audio Monitor → Home Assistant Setup Guide

This guide walks you through getting the PC Audio Monitor running and connected to Home Assistant.

## Quick Start (5 minutes)

### 1. Install Python Dependencies
```bash
cd C:\path\to\test-one
pip install -r requirements.txt
```

### 2. Get Home Assistant API Token
1. Open Home Assistant web interface (192.168.68.30:8123)
2. Click your profile icon (bottom left)
3. Click "Create Token" at the bottom
4. Copy the token (long string of characters)

### 3. Configure the App
```bash
# Copy the example config
copy .env.example .env

# Edit .env and fill in:
# - HA_HOST: 192.168.68.30 (or your HA IP)
# - HA_TOKEN: Paste the token from step 2
# - ALERT_START_HOUR: 9 (don't alert before 9am)
# - ALERT_END_HOUR: 23 (don't alert after 11pm)
```

### 4. Run the App
```bash
python main.py
```

You should see:
```
Monitor ready. Waiting for audio status changes...
RMS:  -99.68 dB | State: silence  | ACTIVE | Current: 14:00 | Window: 09:00 - 23:00
```

## Detailed Setup

### Windows Stereo Mix (Recommended)

For the app to detect **all system audio**, you should enable Stereo Mix:

1. **Right-click speaker icon** → "Open Sound settings"
2. Go to **Advanced** → **Volume mixer**
3. Find your main audio device and look for **Stereo Mix** or **WASAPI Loopback**
4. If disabled, **Enable** it
5. Set it as your default recording device:
   - Right-click speaker icon
   - Click "Sound settings"
   - Under "Input devices", find Stereo Mix and check if it's working

**Without Stereo Mix**: The app will fall back to using your microphone as input (less ideal).

### Home Assistant Configuration

#### Create Long-Lived Access Token
1. Go to Home Assistant: `http://192.168.68.30:8123`
2. Click your **Profile** (bottom left corner)
3. Scroll to "Long-Lived Access Tokens"
4. Click **"Create Token"**
5. Name: "PC Audio Monitor"
6. Copy the entire token string

#### Test Connection
Run the test script to verify Home Assistant is reachable:
```bash
python test_ha_integration.py
```

Expected output:
```
Notifier configured:
  Host: 192.168.68.30:8123
  Service: notify.notify
  Protocol: http
Sending test alert...
SUCCESS: Alert sent to Home Assistant!
```

### Configuration Options

Edit `.env` to customize behavior:

| Setting | Default | Range | Description |
|---------|---------|-------|-------------|
| `HA_HOST` | 192.168.68.30 | IP/hostname | Home Assistant address |
| `HA_PORT` | 8123 | 1-65535 | Home Assistant port |
| `HA_TOKEN` | (required) | string | Long-lived access token |
| `AUDIO_THRESHOLD_DB` | -40 | -60 to -20 | Audio detection sensitivity (lower = more sensitive) |
| `MONITOR_INTERVAL_SECONDS` | 60 | 5-300 | How often to check audio status |
| `AUDIO_CHUNK_DURATION_SECONDS` | 2 | 1-5 | Recording duration per check |
| `ALERT_COOLDOWN_SECONDS` | 60 | 10-3600 | Min seconds between alerts (prevents spam) |
| `ALERT_START_HOUR` | 0 | 0-23 | When alerts start (24-hour format) |
| `ALERT_END_HOUR` | 24 | 1-24 | When alerts end (24-hour format) |
| `LOG_LEVEL` | INFO | DEBUG/INFO/WARNING/ERROR | Logging verbosity |
| `LOG_FILE` | pc_audio_monitor.log | filename | Log file name |

#### Alert Schedule Examples

**Don't alert at 1am-8am** (sleep hours):
```
ALERT_START_HOUR=8
ALERT_END_HOUR=24
```

**Only 9am-5pm** (work hours):
```
ALERT_START_HOUR=9
ALERT_END_HOUR=17
```

**10pm-6am** (overnight only):
```
ALERT_START_HOUR=22
ALERT_END_HOUR=6
```

**All day** (default):
```
ALERT_START_HOUR=0
ALERT_END_HOUR=24
```

### Understanding the Output

When running, you'll see log lines like:
```
RMS:  -45.32 dB | State: sound    | ACTIVE | Current: 14:00 | Window: 09:00 - 23:00
```

- **RMS**: Volume level in decibels (lower = quieter)
- **State**: `sound` = audio detected, `silence` = no audio
- **ACTIVE/INACTIVE**: Whether alerts are currently enabled by schedule
- **Current**: Current time (24-hour format)
- **Window**: Alert active time window

When sound stops during alert window:
```
ALERT: Sound has stopped! Notifying Home Assistant...
```

## Troubleshooting

### "No loopback device found"
- Stereo Mix not enabled on your audio device
- The app will fall back to microphone input
- To fix: Enable Stereo Mix following instructions above

### "Connection error to Home Assistant"
- Check `HA_HOST` is correct (try `ping 192.168.68.30`)
- Verify port `HA_PORT` is correct (usually 8123)
- Make sure Home Assistant is running

### "Failed to send alert: HTTP 401"
- Invalid or expired `HA_TOKEN`
- Create a new token following "Create Long-Lived Access Token" above

### "Failed to send alert: HTTP 404"
- Wrong notify service name
- Check `HA_NOTIFY_SERVICE` setting (usually `notify.notify`)
- Try: Go to Home Assistant > Developer Tools > Call Service, search for "notify"

### App exits immediately
- Check `pc_audio_monitor.log` for detailed error messages
- Run with `LOG_LEVEL=DEBUG` for more info
- Make sure all required environment variables are set in `.env`

### No alerts when sound stops
- Check if current time is in alert window: Look at log output
- Verify alert cooldown hasn't blocked it (minimum 60s between alerts by default)
- Test with `test_ha_integration.py` to verify HA connection
- Check Home Assistant notification history

## Running as a Windows Service (Advanced)

To run the app automatically at startup:

1. Install NSSM (Non-Sucking Service Manager):
   ```bash
   winget install NSSM
   ```

2. Register the app as a service:
   ```bash
   nssm install PCMonitor "C:\path\to\test-one\main.py"
   nssm set PCMonitor AppDirectory "C:\path\to\test-one"
   ```

3. Start the service:
   ```bash
   nssm start PCMonitor
   ```

4. Check status:
   ```bash
   nssm status PCMonitor
   ```

## Logs

The app writes logs to `pc_audio_monitor.log` in the app directory.

View recent logs:
```bash
Get-Content pc_audio_monitor.log -Tail 50
```

Enable debug logging for troubleshooting:
```
LOG_LEVEL=DEBUG
```

## Files

- `main.py` - Application entry point and monitoring loop
- `audio_capture.py` - Audio detection using sounddevice
- `audio_monitor.py` - State machine for sound/silence detection
- `alert_schedule.py` - Time-based alert scheduling
- `ha_notifier.py` - Home Assistant REST API integration
- `test_ha_integration.py` - Test script for Home Assistant connection
- `.env` - Configuration (copy from .env.example)
- `README.md` - Quick reference
- `SETUP.md` - This detailed guide

## Support

- Check logs: `pc_audio_monitor.log`
- Enable DEBUG logging: `LOG_LEVEL=DEBUG` in .env
- Verify Home Assistant connection with `test_ha_integration.py`
- Check Home Assistant notify services available
