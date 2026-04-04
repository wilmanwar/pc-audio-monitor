# Audio Setup Guide for Any PC Configuration

This app works on **any Windows PC**, but the audio capture method depends on your system's capabilities. This guide helps you choose the right setup for your PC.

## Quick Audio Setup Flowchart

```
Does your PC have Stereo Mix enabled?
├─ YES → Use Stereo Mix (Best option - easiest)
├─ NO  → Do you have VB-Audio Cable installed?
│       ├─ YES (Want Simple) → Use VB-Audio Cable (Simple, no mixer)
│       ├─ YES (Want Full Control) → Use VoiceMeeter + Cable (Mixer features)
│       ├─ NO (Want To Install) → Install VoiceMeeter (Recommended)
│       └─ NO (Don't Want Install) → Use Microphone fallback
└─ BLOCKED → Check audio driver or enable in BIOS
```

---

## Option 1: Stereo Mix (Easiest - No Additional Software)

**Best for**: Capturing all system audio with minimal setup

### Requirements
- Audio driver that supports Stereo Mix
- Most NVIDIA, Realtek, and modern audio drivers support this

### Setup Instructions

1. **Enable Stereo Mix in Windows Settings**
   ```
   Settings → System → Sound → Volume mixer
   Scroll down to "Advanced"
   Look for your audio device under "Input devices"
   If you see "Stereo Mix" or "WASAPI Loopback" → Click "Enable"
   ```

2. **Run the App**
   ```bash
   python main.py
   ```

3. **Verify It's Working**
   - Play music or a video
   - Check the logs for sound detection:
     ```
     RMS: -35.2 dB | State: sound | ACTIVE
     ```
   - Stop the audio, wait 30 seconds (default interval)
   - Should show: `State: silence`

### Troubleshooting Stereo Mix

**"Stereo Mix is not in my Sound Settings"**

The driver might not support it or it's disabled. Try:

1. Right-click speaker icon → Sound settings
2. Scroll to "Advanced" → "Volume mixer"
3. Look for disabled devices (might show as greyed out)
4. If found, right-click and enable it

**If still not visible:**
- Your audio driver doesn't support Stereo Mix
- Update your audio driver (see Option 2)
- Use the VoiceMeeter option below

---

## Option 2: VoiceMeeter + Voicemeeter Point Devices (Recommended for Most Users)

**Best for**: System audio capture without native Stereo Mix, or for advanced routing

### What is VoiceMeeter?
Virtual audio mixer that creates virtual audio devices you can record from. Works on virtually all Windows systems.

### Installation

1. **Download VoiceMeeter**
   - Visit: https://vb-audio.com/Voicemeeter/
   - Download "Voicemeeter Standard" (free)
   - Run installer, restart when done

2. **Configure VoiceMeeter for System Audio**
   - Open VoiceMeeter (should auto-start after restart)
   - You'll see a mixer window with sliders
   - Set your main audio output to route through VoiceMeeter:
     - In VoiceMeeter, find your audio device
     - Enable routing so system sounds go through it
     - Check "Monitor Output" on the device

3. **Set Voicemeeter as Default Output (Optional but Recommended)**
   - Windows Settings → Sound → Advanced → Volume mixer
   - Find your output device
   - Set as default
   - Apps will now route through VoiceMeeter

4. **Test Audio Routing**
   - Play a video or music
   - You should hear it normally
   - VoiceMeeter slider should move

### Run the PC Audio Monitor App

```bash
python main.py
```

The app will automatically detect and use Voicemeeter Point devices.

**Expected output:**
```
Found Virtual Audio Device: Voicemeeter Out 5 (Voicemeeter Point 5) (ID: 67)
Device 67 using sample rate: 44100 Hz
Monitor ready. Waiting for audio status changes...
```

### Why This Works
- Voicemeeter Point devices are compatible with the sounddevice library
- They provide clean system audio capture
- Available on any Windows system with VoiceMeeter installed

---

## Option 2b: VB-Audio Cable Only (Simpler Alternative, No VoiceMeeter)

**Best for**: Users who have VB-Audio Cable installed but want to avoid VoiceMeeter complexity

### What is VB-Audio Cable?
A virtual audio cable that routes audio from applications through a loopback device. The app can read from the cable directly without needing VoiceMeeter's mixer.

### Installation

1. **Check if VB-Audio Cable is installed**
   - Open Windows Settings → Sound
   - Look for "CABLE Input" or "CABLE Output" devices
   - If visible, you already have it installed

2. **If Not Installed**
   - Visit: https://vb-audio.com/Cable/
   - Download VB-Audio Cable
   - Run installer, restart when done

### Setup (Simple Method)

1. **Route System Audio to Cable**
   - Open Windows Settings → Sound
   - Click "Volume mixer"
   - For your application (YouTube, Spotify, etc):
     - Set output to `CABLE Input` or `CABLE Output`

2. **Enable Monitoring (So You Can Hear It)**
   - Right-click CABLE Output device → Properties
   - Advanced tab
   - Check "Listen to this device"
   - Select your speakers as the playback device

3. **Run the App**
   ```bash
   python main.py
   ```

### Test It

While music is playing:
```bash
python test_audio_devices.py
```

Look for `CABLE Output` or `CABLE Input` with a high audio level.

### Why This Works
- VB-Audio Cable creates a loopback device
- Audio routed to the cable doesn't leave your PC
- The app can read directly from the cable's input
- Simpler than VoiceMeeter if you don't need mixer features

### If It Doesn't Work

**Check 1: Is audio routing to the cable?**
- Run `test_audio_devices.py` with music playing
- If CABLE doesn't show high audio levels, audio isn't routing to it
- Double-check Windows Sound Settings

**Check 2: Enable Cable monitoring**
- CABLE Output device → Properties
- Advanced tab → Listen to this device
- This lets you hear the audio

**Check 3: Try both Cable Input and Cable Output**
- Some systems show them separately
- Run the test tool to find which one has audio

---

## Option 3: Microphone Fallback (Works Everywhere, Limited Quality)

**Best for**: Temporary testing, or when other options aren't available

### How It Works
If Stereo Mix isn't available and VoiceMeeter isn't installed, the app automatically falls back to your microphone.

**Limitations:**
- Only detects audio near the microphone
- Won't capture system audio clearly
- Best for detecting someone speaking near the PC
- Not ideal for monitoring speaker output

### Setup

Just run the app:
```bash
python main.py
```

It will use your default microphone input automatically.

**Expected output:**
```
Stereo Mix / Virtual audio device not found.
Using default input device as fallback (usually microphone).
Using fallback device: Microphone Array (Synaptics Audio)
```

---

## Troubleshooting Audio Device Detection

### How to Find Your Audio Devices

The app lists all available devices on startup. Look for:

1. **Run the app**
   ```bash
   python main.py
   ```

2. **Find your device in the output**
   ```
   Available audio devices:
     [0] Microsoft Sound Mapper - Input (in: 2, out: 0)
     [1] Microphone Array (Synaptics Aud (in: 4, out: 0)
     [67] Voicemeeter Out 5 (Voicemeeter Point 5) (in: 8, out: 0)
   ...
   ```

3. **Look for (in: > 0)**
   - This means the device has input channels (can be recorded from)
   - Our app uses devices with input channels

### Understanding Device Names

- **Stereo Mix, WASAPI, What U Hear, Loopback** → System audio
- **Voicemeeter Out, Voicemeeter Point** → VoiceMeeter virtual devices
- **CABLE Output, CABLE Input** → VB-Audio Cable devices
- **Microphone Array, Microphone** → Mic input (fallback only)
- **Speakers, Output** → Speaker output (not usable for recording)

### Force Specific Device

If the app selects the wrong device:

1. Edit `.env`:
   ```
   AUDIO_DEVICE_ID=67
   ```

2. Replace `67` with the device ID from the startup output

3. Restart the app

---

## Comparison Table

| Method | Quality | Setup Ease | Works Everywhere | Additional Software |
|--------|---------|-----------|------------------|-------------------|
| **Stereo Mix** | Excellent | ⭐⭐⭐ (Easy) | ~70% of systems | None |
| **VoiceMeeter Point** | Excellent | ⭐⭐ (Medium) | 100% of systems | VoiceMeeter (Free) |
| **Microphone** | Fair | ⭐⭐⭐⭐⭐ (Easiest) | 100% of systems | None |

---

## FAQ

### Q: Which option should I use?
**A:** 
1. Try Stereo Mix first (easiest)
2. If that doesn't work, use VoiceMeeter
3. Use Microphone fallback only for testing

### Q: Can I switch between audio sources?
**A:** Yes! The app auto-detects in order:
1. Stereo Mix (if available)
2. Voicemeeter Point devices (if VoiceMeeter installed)
3. Microphone (always available)

Just restart the app after enabling/disabling options.

### Q: Why does the app show "silence" when music is playing?
**A:** 
- Audio might not be routed to the selected device
- Check device selection in startup output
- Try enabling VoiceMeeter for better audio routing
- Increase `AUDIO_THRESHOLD_DB` in `.env` if audio is very quiet

### Q: Does VoiceMeeter affect my normal audio?
**A:** No, VoiceMeeter is a mixer that sits between apps and audio. Audio still plays normally. You hear everything as usual.

### Q: Can I use this on a work PC with restricted audio settings?
**A:** 
- Stereo Mix: Might be disabled by admin
- VoiceMeeter: Should work unless software installation is blocked
- Microphone: Always works unless explicitly disabled

Contact your IT department if features are blocked.

### Q: What's the difference between "CABLE" and "Voicemeeter Point"?
**A:**
- **VB-Audio CABLE**: Advanced virtual audio cable (more complex setup)
- **Voicemeeter Point**: Built-in with VoiceMeeter (simpler, works better with this app)

Use Voicemeeter Point (recommended).

---

## Advanced: Manual Device Selection

If auto-detection isn't working, manually specify your device:

1. **List all devices**
   ```bash
   python -c "import sounddevice as sd; [print(f'{i}: {d[\"name\"]} (in: {d[\"max_input_channels\"]})') for i, d in enumerate(sd.query_devices())]"
   ```

2. **Find a device with input channels (in: > 0)**

3. **Set in `.env`**
   ```
   AUDIO_DEVICE_ID=67
   ```

4. **Restart the app**

---

## See Also

- **SETUP.md** - Full setup instructions
- **STEREO_MIX_ALTERNATIVES.md** - More audio alternatives
- **README.md** - Quick reference
- **IMPLEMENTATION.md** - How the app works
