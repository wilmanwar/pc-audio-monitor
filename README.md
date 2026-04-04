# Windows PC Audio Monitor → Home Assistant

A Python application that monitors system audio on Windows and sends alerts to Home Assistant when sound stops.

## Features
- Monitors all PC audio output (system-level detection)
- Sends alerts to Home Assistant only when sound **stops** (not on startup)
- Very low audio sensitivity threshold
- Runs as a standalone Windows executable
- Configurable via `.env` file
- **Works without Stereo Mix** - auto-detects virtual audio devices or microphone fallback

## Requirements
- Windows 10/11
- Python 3.8+ (or use the packaged .exe)
- Audio device (Stereo Mix OR virtual audio device like VB-Audio Cable OR microphone)
- Home Assistant instance with API access
- Home Assistant long-lived access token

## Setup

### 1. Clone and Install Dependencies
```bash
git clone <repo>
cd test-one
pip install -r requirements.txt
```

### 2. Configure Home Assistant
1. Create a long-lived access token in Home Assistant
2. Copy `.env.example` to `.env`
3. Update `.env` with your Home Assistant details:
   ```
   HA_HOST=192.168.68.30
   HA_TOKEN=your_token_here
   ```

### 3. Enable Audio Detection

**The app automatically detects the best audio device on your PC.**

See [AUDIO_SETUP_GUIDE.md](AUDIO_SETUP_GUIDE.md) for your specific setup:

- ✅ **Stereo Mix** (easiest if available - native Windows)
- ✅ **VB-Audio Cable** (recommended - works on any PC with loopback)
- ✅ **Microphone** (fallback - always available)

**Quick options:**

1. **Stereo Mix (if available)**
   - Settings → Sound → Advanced → Volume mixer
   - Enable "Stereo Mix"
   - Done!

2. **VB-Audio Cable (recommended)**
   - Download: https://vb-audio.com/Cable/
   - Install and restart
   - Open VBCABLE_ControlPanel.exe
   - Set output to CABLE in Windows Sound Settings
   - Enable "Listen to this device" with loopback to speakers
   - Done!

3. **Microphone (fallback)**
   - App automatically uses it if nothing else is configured
   - Works but limited quality

**→ Full setup instructions and troubleshooting in [AUDIO_SETUP_GUIDE.md](AUDIO_SETUP_GUIDE.md)**

### 4. Run the App
```bash
python main.py
```

Or use the packaged executable:
```
pc-audio-monitor.exe
```

## Configuration
Edit `.env` to customize:
- `AUDIO_THRESHOLD_DB`: Sensitivity (-60 to -20, lower = more sensitive)
- `MONITOR_INTERVAL_SECONDS`: How often to check (default 60)
- `ALERT_START_HOUR` / `ALERT_END_HOUR`: When alerts are enabled (0-23 hours)
- `LOG_LEVEL`: INFO, DEBUG, WARNING, ERROR

### Alert Scheduling Examples
- **No alerts at 1am**: Set `ALERT_START_HOUR=2, ALERT_END_HOUR=24` (2am to midnight)
- **Only 9am-5pm**: Set `ALERT_START_HOUR=9, ALERT_END_HOUR=17`
- **Overnight alerts only**: Set `ALERT_START_HOUR=22, ALERT_END_HOUR=6` (10pm to 6am)
- **All day (default)**: Set `ALERT_START_HOUR=0, ALERT_END_HOUR=24`

## Troubleshooting
- Check `pc_audio_monitor.log` for error messages
- Run with `LOG_LEVEL=DEBUG` for detailed audio capture info
- Ensure Stereo Mix is enabled and set as default recording device

## Building the Executable
```bash
pyinstaller --onefile --windowed --add-data "requirements.txt:." main.py
```

The executable will be in the `dist/` folder.
