# VB-Audio Cable Setup Guide (Recommended)

This is the recommended setup for system audio capture on any Windows PC.

## Prerequisites

- VB-Audio Cable installed (download from https://vb-audio.com/Cable/)
- Windows Sound Settings access
- **CRITICAL: Microphone permissions must be enabled** (see Step 0 below)

## Step-by-Step Setup

### Step 0: Enable Microphone Permissions (CRITICAL!)

**Why this is needed:** Python's audio library needs microphone permissions to access ANY audio recording device, even though the PC Audio Monitor uses VB-Audio Cable, not the microphone. Without this, the app cannot access audio devices.

1. **Open Windows Settings**
   - Press `Windows Key + I`
   - Go to: Settings → Privacy & security → Microphone

2. **Grant microphone access to Python**
   - Look for "Python" or "python.exe" in the app list
   - Make sure it shows as "Allowed" (toggle ON)
   - If Python isn't listed, restart the app and it should appear

3. **Alternative: Enable for all apps**
   - If you don't see Python listed, enable "Microphone access" globally
   - This allows all applications to use audio recording

4. **Verify it worked**
   - Run: `python test_audio_devices.py` (with music playing)
   - If you see device levels (not just [ERROR]), permissions are working

**Without this step, you'll see errors like:**
```
PortAudioError: Error opening InputStream
TypeError: wait() got an unexpected keyword argument 'timeout'
```

### Step 1: Install VB-Audio Cable

1. Download from: https://vb-audio.com/Cable/
2. Run the installer
3. Restart Windows when prompted
4. VB-Audio Cable should now appear in your Sound Settings

### Step 2: Configure VB-Audio Cable Control Panel

1. **Open VBCABLE_ControlPanel.exe**
   - In Windows Start menu, search for "VBCABLE Control Panel"
   - Or find it in `C:\Program Files\VB-Audio\VB-Cable`

2. **Enable Windows Volume Mixer Integration**
   - In the Control Panel, look for options to enable Windows mixer control
   - This allows you to control VB-Audio through Windows Sound Settings
   - Apply settings

### Step 3: Configure Windows Sound Settings

#### 3a: Set VB-Audio Cable as Your Sound Output Device

1. **Open Windows Sound Settings**
   - Right-click the speaker icon in the taskbar
   - Select "Open Sound settings"
   - OR: Settings → System → Sound

2. **Set Default Output Device**
   - Under "Output" section
   - Click the dropdown
   - Select: **"CABLE Input"** or **"VB-Audio Cable"**
   - This sends all system audio to VB-Audio Cable

#### 3b: Enable Loopback Listening

1. **Find VB-Audio Cable in Recording Devices**
   - In Sound Settings, scroll down to "Advanced"
   - Click "Volume mixer"
   - Look for recording devices, find **"VB-Audio Cable"** or **"CABLE Output"**

2. **Enable "Listen to this device"**
   - Right-click the VB-Audio Cable recording device → Properties
   - Go to the "Listen" tab
   - Check: **"Listen to this device"**
   - Set the playback device to: **Your speakers** (so you can hear it)
   - Click Apply → OK

### Step 4: Test the Setup

**While music is playing:**

```bash
python test_audio_devices.py
```

You should see `CABLE Input` or `CABLE Output` with a high audio level (above -60 dB).

If you see it detected, you're done! The app will automatically use it.

### Step 5: Run the PC Audio Monitor

```bash
python main.py
```

**Expected output:**
```
Found Virtual Audio Device: CABLE Output (VB-Audio Virtual Cable) (ID: 4)
Device 4 using sample rate: 44100 Hz
Monitor ready. Waiting for audio status changes...
```

The app will now detect when system audio stops and alert Home Assistant.

## How It Works

```
Your Application (YouTube, Spotify, Browser)
    |
    v
Windows Sets Output to: VB-Audio Cable
    |
    +----> PC Audio Monitor reads from here
    |
    +----> "Listen to this device" setting
           └----> Routes audio back to speakers
                  (so you hear it)
```

## Troubleshooting

### "CABLE not appearing in Sound Settings"

1. Restart Windows
2. Open VBCABLE_ControlPanel.exe
3. Check if Windows integration is enabled
4. If still missing, reinstall VB-Audio Cable:
   - Uninstall from Programs
   - Delete any remaining VB-Audio folders
   - Restart Windows
   - Reinstall VB-Audio Cable
   - Restart again

### "Audio not detected by test_audio_devices.py"

1. Verify output is set to VB-Audio Cable:
   - Sound Settings → Output dropdown
   - Should show CABLE as selected

2. Check "Listen to this device":
   - Sound Settings → Volume mixer
   - Find CABLE recording device
   - Enable "Listen to this device"
   - Verify playback device is set to speakers

3. Restart the application outputting audio (browser, media player)

### "I hear nothing when music is playing"

1. Check "Listen to this device" is enabled:
   - CABLE recording device → Properties → Listen tab
   - Should be checked

2. Verify playback device:
   - When "Listen to this device" is enabled
   - Select your speakers as the playback device

3. Check speaker volume:
   - Windows volume mixer shows correct levels
   - Physical speaker volume is turned up

### "VBCABLE_ControlPanel.exe won't open"

1. Try running as Administrator:
   - Right-click VBCABLE_ControlPanel.exe → Run as administrator

2. Check installation:
   - Go to: C:\Program Files\VB-Audio\VB-Cable\
   - If folder doesn't exist, VB-Audio isn't installed properly
   - Reinstall VB-Audio Cable

### "Audio test fails with PortAudioError or TypeError"

**This almost always means microphone permissions are disabled!**

1. Check Windows microphone permissions:
   - Settings → Privacy & security → Microphone
   - Make sure "Microphone access" is ON
   - If Python is listed, make sure its toggle is ON

2. Restart the Python app after enabling permissions

3. Verify with:
   ```bash
   python test_audio_devices.py
   ```
   - Should now show audio levels for CABLE devices
   - Should NOT show [ERROR] for all devices

## Quick Checklist

- [ ] **Microphone permissions enabled** (Settings → Privacy & security → Microphone)
- [ ] VB-Audio Cable installed (appears in Sound Settings)
- [ ] VBCABLE_ControlPanel.exe opened and configured
- [ ] Windows output device set to "CABLE Input" or "VB-Audio Cable"
- [ ] CABLE device "Listen to this device" enabled
- [ ] Playback device for listening set to your speakers
- [ ] Tested with: `python test_audio_devices.py`
- [ ] Music is playing when running tests
- [ ] App running: `python main.py`

## Advanced: Manual Device ID

If for some reason the app doesn't auto-detect CABLE:

1. Run: `python test_audio_devices.py` (with music playing)
2. Find the CABLE device and its ID number
3. Edit `.env` file:
   ```
   AUDIO_DEVICE_ID=4
   ```
4. Save and restart the app

## That's It!

Your PC Audio Monitor will now:
- ✅ Detect when system audio stops
- ✅ Send alerts to Home Assistant
- ✅ Work with the "Listen to this device" loopback setup
- ✅ Automatically use VB-Audio Cable when available
