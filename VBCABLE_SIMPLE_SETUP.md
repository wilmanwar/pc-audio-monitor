# VB-Audio Cable Only Setup (No VoiceMeeter)

This is the simplest way to use VB-Audio Cable with the PC Audio Monitor app.

## How It Works

The basic idea:
1. **System audio** goes to VB-Audio Cable OUTPUT
2. **App reads** from VB-Audio Cable INPUT  
3. **You hear it** by setting Cable as your playback device with monitoring enabled

## Setup Steps

### Step 1: Identify Your VB-Audio Cable Devices

From the app logs, you should see:
- `[4]` or similar: `CABLE Output (VB-Audio Virtual Cable)` - This is where audio GOES TO
- `[27]` or similar: `CABLE Output (VB-Audio Virtual Cable) - Full Version` - Same device, different channel count
- You might also see `CABLE Input` but we'll be reading from OUTPUT

### Step 2: Route System Audio to VB-Audio Cable

**Option A: Set Cable as Default Playback Device (Simplest)**

1. Open Windows **Sound Settings** (Settings → Sound)
2. Find **Volume mixer** or **App volume and device preferences**
3. For your application (YouTube, Spotify, etc):
   - Set the output device to `CABLE Input` or `CABLE Output`
4. You won't hear anything yet - that's OK, follow Step 3

**Option B: Use Windows Stereo Mix with Cable (If available)**

1. Right-click speaker icon in taskbar
2. Select "Open Volume mixer"
3. Under "App volume and device preferences"
4. Set application output to `CABLE Input`

### Step 3: Monitor the Cable Output

So you can hear your audio while the app captures it:

**Method 1: Use Cable Output Monitoring (Easiest)**
1. In your application output settings, select: `CABLE Output`
2. In Windows Sound settings, find `CABLE Output` device
3. Right-click → Properties
4. Go to "Advanced" tab
5. Enable **"Listen to this device"**
6. Select your speakers as the listen-to device

**Method 2: Route Both Speakers AND Cable (Advanced)**
Use a Windows audio router tool to send audio to both:
- Physical Speakers (so you hear it)
- CABLE Input (so the app captures it)

## Simple Test

Once configured:

```bash
# 1. Start playing music on your PC
# 2. While music is playing, check which device has audio:
python test_audio_devices.py

# 3. Look for "CABLE Output" with a HIGH audio level
# 4. If found, the app will auto-detect it and use it
# 5. If not, set in .env:
AUDIO_DEVICE_ID=4  # or whatever number shows the highest audio
```

## Why This Works

```
Your Application (YouTube, Spotify)
          |
          v
    CABLE Input
    (Virtual Cable)
          |
   _______|_______
   |             |
   v             v
CABLE Output   System Loopback
(To App)      (To Speakers via monitoring)
   ^             |
   |             v
   |        Your Speakers
   |        (You hear it!)
   |
PC Audio Monitor App
(Reads from CABLE Input/Output)
```

## If It Still Doesn't Work

**Possible Issue 1: Cable Not Set as Default**
- Check Windows Sound Settings
- Ensure application is routing to CABLE, not system default
- Restart application

**Possible Issue 2: Monitoring Not Enabled**
- Right-click CABLE Output device → Properties → Advanced
- Enable "Listen to this device"
- Select your speakers as the playback device

**Possible Issue 3: Cable Input vs Output Confusion**
- Try testing BOTH `CABLE Input` and `CABLE Output`
- They might be the same device listed twice
- Run `test_audio_devices.py` to see which one has audio

**Possible Issue 4: Cable Not Working**
- Reinstall VB-Audio Cable
- Restart Windows
- Check VB-Audio Cable is loaded (should see it in Sound Settings)

## Alternative: Just Use Microphone

If this is too complex, the app automatically falls back to your microphone:
- Always works (no setup needed)
- Good enough for many use cases
- Lower quality (picks up room noise)
- Just remove AUDIO_DEVICE_ID from .env and let it auto-select

## Quick Checklist

- [ ] VB-Audio Cable installed and showing in Sound Settings
- [ ] Application audio set to output to CABLE
- [ ] CABLE Output monitoring enabled (if using that method)
- [ ] Music is playing
- [ ] Run `python test_audio_devices.py` to verify
- [ ] Run `python main.py` and check for audio detection
