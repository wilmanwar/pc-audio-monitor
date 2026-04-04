# VoiceMeeter Audio Routing Guide

## The Problem

You routed your audio to "Output A (Speakers)" and "Output B (VB-Audio Cable)", but the PC Audio Monitor app can't hear it because:

- **Output A** sends audio OUT to your physical speakers (no loopback)
- **Output B** sends audio OUT to VB-Audio Cable (but we need Cable INPUT)
- **The app reads FROM input devices**, not output devices

## The Solution: Add Voicemeeter Point as an Input

In VoiceMeeter, you need to route audio to **Voicemeeter Point**, which is the input that the app can read from.

### Step 1: Check Your Current Routing

Right now in VoiceMeeter:
- Output A (Speakers) ✓ (this is fine, keeps your audio playing)
- Output B (VB-Audio Cable) ✗ (this goes OUT, not IN)

### Step 2: Add Voicemeeter Point Input

In VoiceMeeter mixer window:

1. **Left side (Virtual Inputs)**: You should see "Voicemeeter VAIO"
2. **Bottom section**: Look for output options - you'll see "A", "B", "Hardware Out"
3. **Check the OUTPUT BUTTONS** for "Voicemeeter Point 5" or similar

The easiest fix:

**Option A: Route to Both Speakers AND Voicemeeter Point**

1. In your main application (e.g., YouTube/Spotify):
   - Make sure it's set to output to "Speakers" (Windows default) or directly to VoiceMeeter input
   
2. In VoiceMeeter mixer, for the audio source:
   - Check "A" (Speakers) ✓
   - Check "B" (VB-Audio Cable) ✓  [optional - for mixing]
   - **Check "Voicemeeter Out" buttons** to route to Voicemeeter Point inputs

**Option B: Just Use the Microphone (Temporary)**

If VoiceMeeter routing is confusing, the app will fall back to your microphone, which works but isn't ideal.

## Why This Works

The **Voicemeeter Point devices** are special - they're **virtual inputs built into VoiceMeeter** that receive audio internally. When you configure VoiceMeeter to route to them, the audio never leaves the computer - it stays internal and the app can read it.

## Diagram

```
Your Application (YouTube, Spotify, etc)
         |
         v
   Speakers         <-- audio plays (you hear it)
         |
    VoiceMeeter     <-- intercepts audio routing
         |
    _____|_____________________
    |         |         |       |
    v         v         v       v
 Output A   Output B  Voicemeeter  Hardware Out
 (Spkr)    (Cable)     Point     (speakers)
 (OUT)     (OUT)       (IN)       (OUT)
                       ^
                       |
            PC Audio Monitor
            (reads from this!)
```

## Quick Fix

1. In Windows, ensure audio is playing (not muted)
2. In VoiceMeeter, check that "Voicemeeter Point" outputs are enabled
3. Run the PC Audio Monitor app
4. Run `python test_audio_devices.py` while music is playing to verify

If still not working, check VoiceMeeter's documentation on routing virtual inputs.

## Alternative: Just Use Microphone

If this is too complex, the app will automatically fall back to using your microphone, which always works (though not as clean for system audio).

---

**Next Step**: Update .env to disable auto-detect and just use the standard device priority selection:

```
AUTO_DETECT_AUDIO=false
AUDIO_DEVICE_ID=  # leave blank for auto-selection
```

Then run: `python main.py`
