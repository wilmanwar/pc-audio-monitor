# Audio Detection Troubleshooting Guide

This guide helps you fix audio detection issues when setting up the PC Audio Monitor.

## Quick Diagnosis

Run this test to see which audio devices are available and working:

```bash
# While music/audio is playing:
python test_audio_devices.py
```

### Test Results Interpretation

**All devices show [ERROR] or [Quiet]?**
→ Go to: [Microphone Permissions Not Enabled](#microphone-permissions-not-enabled)

**Some CABLE devices show levels, others don't?**
→ Go to: [VB-Audio Cable Issues](#vb-audio-cable-issues)

**Microphone shows audio but CABLE doesn't?**
→ Go to: [Audio Routing Issues](#audio-routing-issues)

**No Stereo Mix, no CABLE, only microphone?**
→ Go to: [Limited Audio Options](#limited-audio-options)

---

## Problem 1: Microphone Permissions Not Enabled

### Symptoms
- All devices show `[ERROR or No Input]` or `[Quiet]`
- Error messages like:
  ```
  PortAudioError: Error opening InputStream
  PortAudioError: Invalid device [PaErrorCode -9996]
  TypeError: wait() got an unexpected keyword argument
  ```

### Root Cause
**Python needs microphone permission to access ANY audio recording device**, even though the app uses VB-Audio Cable or Stereo Mix, not your actual microphone.

### Solution

1. **Open Windows Settings**
   - Press: `Windows Key + I`
   - OR: Right-click Start → Settings

2. **Navigate to Microphone Settings**
   - Go to: **Privacy & security → Microphone**

3. **Enable Microphone Access**
   - Toggle: **"Microphone access"** to **ON**
   - If you see "Python" or "python.exe" listed:
     - Toggle **its switch to ON** as well

4. **Restart the App**
   - Close any running instances
   - Close terminal/command prompt
   - Open new terminal
   - Run: `python test_audio_devices.py`

5. **Verify It Works**
   - Should now see audio levels for CABLE and other devices
   - Should NOT show [ERROR] for all devices

### If Still Not Working

1. Check again: Settings → Privacy & security → Microphone
   - Confirm "Microphone access" is ON
   - Confirm Python's toggle is ON (if listed)

2. Restart Windows completely
   - This ensures permission changes take effect

3. Try again:
   ```bash
   python test_audio_devices.py
   ```

### Advanced: Allow All Apps

If Python isn't listed in Microphone permissions:

1. Settings → Privacy & security → Microphone
2. Make sure "Microphone access" is ON globally
3. This allows all Python instances to access audio

---

## Problem 2: VB-Audio Cable Issues

### Symptoms
- Microphone works but CABLE devices show errors
- `python test_audio_devices.py` shows:
  ```
  [1] CABLE Output (VB-Audio... [ERROR]
  [8] CABLE Output (VB-Audio... [ERROR]
  ```

### Root Cause
VB-Audio Cable drivers aren't properly initialized or your audio isn't routed to CABLE.

### Solution: Step 1 - Verify CABLE is Installed

1. **Check if CABLE appears in Sound Settings**
   - Settings → System → Sound → Volume mixer
   - Look for "CABLE" in recording devices
   - If NOT there: CABLE isn't installed or needs restart

2. **If CABLE doesn't appear:**
   ```
   Option A: Restart Windows
   - Reboot should register CABLE drivers
   
   Option B: Reinstall VB-Audio Cable
   - Download: https://vb-audio.com/Cable/
   - Run installer
   - Restart Windows
   ```

### Solution: Step 2 - Verify Audio Routing

1. **Set output device to CABLE**
   - Settings → System → Sound
   - Under "Output" section
   - Select: "CABLE Input" or "VB-Audio Cable"

2. **Enable loopback listening**
   - Settings → Sound → Volume mixer (scroll down)
   - Find CABLE recording device
   - Properties → Listen tab
   - Check: "Listen to this device"
   - Set playback to: Your speakers
   - Click Apply → OK

3. **Test audio routing**
   - Play music in browser/media player
   - You should HEAR it through speakers (loopback listening)
   - If you don't hear anything: Audio isn't routed to CABLE

### Solution: Step 3 - Control Panel Configuration

1. **Open VBCABLE_ControlPanel.exe**
   - Start menu → Search "VBCABLE Control Panel"
   - OR: C:\Program Files\VB-Audio\VB-Cable\VBCABLE_ControlPanel.exe

2. **Enable Windows Integration**
   - Look for "Windows Volume" or integration settings
   - Enable it if available
   - Apply settings
   - Restart the app

3. **Test again**
   ```bash
   python test_audio_devices.py
   ```

### Solution: Step 4 - Check Sample Rates

CABLE devices must use their native sample rate:

1. **Find device's native sample rate**
   ```bash
   python -c "import sounddevice as sd; d = sd.query_devices(1); print(f'Sample rate: {d[\"default_samplerate\"]}')"
   ```
   (Replace `1` with your CABLE device ID from test output)

2. **Verify Windows is using that rate**
   - Windows Sound Settings → Advanced
   - Check the sample rate matches

---

## Problem 3: Audio Routing Issues

### Symptoms
- Microphone records audio but CABLE doesn't
- "Listen to this device" should work but doesn't
- Music plays but app detects no audio

### Root Cause
Audio isn't being sent to the loopback input device (CABLE or Stereo Mix).

### Solution: Verify Current Output Device

1. **Check Windows Output Settings**
   ```
   Settings → System → Sound → Output
   What device is currently selected?
   ```

2. **If NOT set to CABLE:**
   - Click the dropdown
   - Select: "CABLE Input" or "VB-Audio Cable"
   - This sends ALL system audio to CABLE

3. **Start music/audio**
   - Play a YouTube video, Spotify, or media player

4. **Test detection**
   ```bash
   python test_audio_devices.py
   ```

### Verify "Listen to This Device"

1. **Sound Settings → Volume mixer**
   - Scroll to "Advanced"
   - Look for CABLE recording device

2. **Check "Listen to this device" is enabled**
   - Right-click CABLE device → Properties
   - Go to: "Listen" tab
   - Should be ☑ (checked)
   - Playback device: Your speakers
   - Apply → OK

3. **Test again**
   ```bash
   python test_audio_devices.py
   ```

### App-Specific Audio Output

Sometimes apps send audio to a specific device, not the Windows default:

1. **Check application's audio settings**
   - YouTube: Settings → Audio output device
   - Spotify: Settings → Audio device
   - Media Player: Settings → Sound device
   - Browser: System output or application-specific

2. **Set app to use Windows default**
   - Most apps will use Windows default output
   - If not, select your main speakers

3. **Verify loopback is working**
   - Play audio → You hear it through speakers?
   - If not: "Listen to this device" isn't working properly

---

## Problem 4: Limited Audio Options

### Symptoms
- No Stereo Mix available
- CABLE not installed or not working
- Only microphone available

### Options

**Option A: Install and Use VB-Audio Cable**
1. Download: https://vb-audio.com/Cable/
2. Install and restart Windows
3. Configure loopback (see Problem 2 above)
4. Follow VBCABLE_SETUP.md

**Option B: Enable Stereo Mix (if available)**
1. Settings → Sound → Volume mixer
2. Look for "Stereo Mix" or "What U Hear"
3. If you see it but disabled:
   - Right-click → Enable
4. Set as default recording device
5. Test: `python test_audio_devices.py`

**Option C: Update Audio Drivers**
- Stereo Mix might not appear if drivers are old
- Visit your audio driver manufacturer website
- Install latest drivers for your audio device
- Restart Windows
- Check for Stereo Mix again

**Option D: Use Microphone (Fallback)**
- If none of above work, app will use microphone
- Quality is lower but it works
- Speak near microphone for testing
- Run: `python test_audio_devices.py`

---

## Problem 5: CABLE Works Sometimes, Not Always

### Symptoms
- First run detects CABLE fine
- After some changes, CABLE stops working
- Error comes and goes unpredictably

### Root Cause
- CABLE driver got disabled
- Audio routing changed
- Windows permissions changed

### Solution: Full Reset

1. **Clear problematic settings**
   ```bash
   # Close the app
   # Open Sound Settings
   # Reset to Windows default speakers
   # Reset recording device to default
   ```

2. **Restart Windows**
   - Critical! Reboot after configuration changes

3. **Reopen VBCABLE_ControlPanel.exe**
   - Check Windows integration is enabled
   - Apply any settings
   - Close panel

4. **Reconfigure output in Sound Settings**
   - Set output to: "CABLE Input"
   - Set recording device to: "CABLE Output"
   - Enable "Listen to this device"
   - Set playback to: Your speakers

5. **Test**
   ```bash
   python test_audio_devices.py
   ```

---

## Verification Checklist

If audio detection isn't working, verify each step:

- [ ] **Microphone permissions enabled** (Settings → Privacy & security → Microphone)
  - [ ] "Microphone access" is ON
  - [ ] Python is toggled ON (if listed)

- [ ] **Audio output routed correctly**
  - [ ] Windows output set to CABLE or Stereo Mix
  - [ ] Music is playing while testing
  - [ ] You hear music through speakers (loopback)

- [ ] **Recording device configured**
  - [ ] "CABLE Output" or "Stereo Mix" is set as recording device
  - [ ] "Listen to this device" is enabled
  - [ ] Playback device set to speakers

- [ ] **VB-Audio Cable installed** (if using CABLE)
  - [ ] Appears in Sound Settings
  - [ ] VBCABLE_ControlPanel.exe runs
  - [ ] Windows integration enabled

- [ ] **Test successful**
  - [ ] Run: `python test_audio_devices.py`
  - [ ] CABLE shows audio levels (not [ERROR])
  - [ ] Audio level above -60 dB (device working)

---

## How to Debug Further

### Enable Debug Logging

Edit `.env`:
```
LOG_LEVEL=DEBUG
```

Run the app:
```bash
python main.py 2>&1 | Tee-Object -FilePath debug.log
```

This creates a `debug.log` file with detailed information about what audio devices were found.

### Check All Audio Devices

```bash
python detect_audio_devices.py
```

Shows all devices with recommendations for best setup.

### Contact Support

If you can't fix it:
1. Run: `python test_audio_devices.py` (with music playing)
2. Run: `python detect_audio_devices.py`
3. Save both outputs
4. Include screenshots of:
   - Sound Settings → Output
   - Sound Settings → Volume mixer
   - Sound Settings → Advanced
   - Sound Settings → Recording devices
5. Describe what you see in test outputs

---

## Common Error Messages

### "PortAudioError: Error opening InputStream: Invalid device [PaErrorCode -9996]"
→ **Microphone permissions disabled** (most likely)
→ Solution: Enable microphone permissions (Problem 1)

### "PortAudioError: Error opening InputStream: Invalid sample rate [PaErrorCode -9997]"
→ Device doesn't support the sample rate being used
→ Solution: Check device's native sample rate (Problem 2, Step 4)

### "PortAudioError: Undefined external error [PaErrorCode -9999]"
→ VB-Audio drivers not properly initialized
→ Solution: Reinstall VB-Audio Cable, restart Windows

### "TypeError: wait() got an unexpected keyword argument 'timeout'"
→ **Microphone permissions disabled** or audio library incompatibility
→ Solution: Enable microphone permissions, update sounddevice library

---

## Getting Help

**Before asking for help:**
1. Enable microphone permissions (critical!)
2. Restart Windows
3. Run: `python test_audio_devices.py`
4. Save the output
5. Provide the output along with your question

**Most audio issues are caused by:** Microphone permissions disabled (90%)

**Second most common:** Audio not routed to CABLE (8%)

**Everything else:** (2%)

Make sure to check the microphone permissions first!
