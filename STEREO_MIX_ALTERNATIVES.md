# Stereo Mix Alternatives Guide

If your audio device doesn't have Stereo Mix enabled or available, here are several solutions:

## Option 1: Microphone Fallback (Current Default)

The app already has a fallback that uses your microphone if Stereo Mix isn't found.

**Pros**:
- No additional software needed
- Works immediately
- Good for monitoring nearby sound

**Cons**:
- Only captures sound near the microphone
- Doesn't capture all system audio

**Use this for**: Testing, monitoring ambient sound, voice-based alerts

## Option 2: Virtual Audio Cable (Recommended)

Install a virtual audio device that captures all system audio.

### VB-Audio Virtual Cable (Free)

1. Download from: https://vb-audio.com/Cable/
2. Install and restart your PC
3. Configure:
   - Route system audio to "Cable Input"
   - Set "Cable Output" as recording device
4. The app will auto-detect it as `(VB-Audio Virtual Cable)`

**Pros**:
- Captures all system audio
- Works with any sound card
- Lightweight and free

**Cons**:
- Requires installation
- Takes a moment to configure

### VoiceMeeter (Free)

1. Download: https://vb-audio.com/Voicemeeter/
2. Install and restart
3. In VoiceMeeter:
   - Select your speakers as input
   - Set "VoiceMeeter Aux Input" as recording device
4. The app will detect it

**Pros**:
- More powerful mixing options
- Professional audio control
- Free version available

**Cons**:
- More complex setup
- Requires more configuration

## Option 3: Update Your Audio Driver

Sometimes Stereo Mix is hidden or disabled in the driver.

### For Realtek Audio

1. Download latest driver from: https://www.realtek.com/en/downloads/
2. Install and restart
3. Right-click speaker icon → Sound settings
4. Advanced → Volume mixer
5. Look for "Stereo Mix" - enable it if found

### For Other Manufacturers

Visit their support page:
- ASUS Audio
- Creative Sound Blaster
- Corsair HS series
- Turtle Beach
- etc.

Download latest drivers and reinstall.

## Option 4: Use Microphone for Monitoring

The app can monitor ambient sound through your microphone.

**Best for**:
- Detecting speech or alarms
- General noise detection
- Testing the app

**Configuration**:
```
# Already set up by default - just run:
python main.py

# The app will use your microphone automatically
```

## Option 5: Screen Capture Software

Some screen capture tools have loopback audio:

- **OBS Studio** (Free) - Can create virtual audio device
- **ShareX** (Free) - Has audio capture options
- **Bandicam** - Professional screen recording

These can route audio to virtual devices.

## How to Check What You Have

Run this to see your audio devices:

```bash
python -c "
import sounddevice as sd
devices = sd.query_devices()
print('Recording Devices:')
for i, dev in enumerate(devices):
    if dev['max_input_channels'] > 0:
        print(f'  [{i}] {dev[\"name\"]} (in: {dev[\"max_input_channels\"]})')
"
```

Look for:
- "Stereo Mix"
- "What U Hear"
- "Wave Out Mix"
- "Virtual Cable"
- "VoiceMeeter"
- "Microphone Array"

## Configuration for Specific Device

If you want to force use of a specific device, you can modify `.env`:

```
# Option 1: Auto-detect (current behavior)
AUDIO_DEVICE_ID=

# Option 2: Specify by number (from the list above)
AUDIO_DEVICE_ID=1   # Uses device [1]

# Option 3: Leave blank to use default input
AUDIO_DEVICE_ID=default
```

Then modify `audio_capture.py` to use it (see section below).

## Recommended Setup by Device Type

### Windows Laptop with Built-in Audio
**Option 1**: Microphone fallback (already enabled)
**Option 2**: Install VB-Audio Virtual Cable

### Windows PC with External Speakers
**Option 1**: Check if driver has Stereo Mix (update drivers)
**Option 2**: Install VB-Audio Virtual Cable
**Option 3**: Use OBS Studio for audio routing

### Gaming Headset (Corsair, SteelSeries, etc.)
**Option 1**: Check manufacturer drivers
**Option 2**: Use manufacturer's audio software
**Option 3**: Install VB-Audio Virtual Cable as backup

### USB Audio Interface (Audio Technica, Behringer, etc.)
**Option 1**: Check if interface has loopback option
**Option 2**: Use interface's control software
**Option 3**: Install VB-Audio Virtual Cable

## Troubleshooting

### "Still not seeing my virtual device"
- Restart Windows after installing
- Check Device Manager (Show hidden devices)
- Reinstall the virtual audio software

### "Audio detection still not working"
- Check your audio is actually playing out of the device
- Use `LOG_LEVEL=DEBUG` to see what device is being used
- Check pc_audio_monitor.log for errors

### "Volume is too quiet or loud"
- Adjust `AUDIO_THRESHOLD_DB` in .env
- Try more sensitive: `AUDIO_THRESHOLD_DB=-60`
- Try less sensitive: `AUDIO_THRESHOLD_DB=-20`

## Code Modification for Specific Device

If you want to hardcode a device number, edit `audio_capture.py`:

```python
# Change this line:
def _find_loopback_device(self) -> Optional[int]:
    # ... existing code ...

# To this for device [5]:
def _find_loopback_device(self) -> Optional[int]:
    return 5  # Force use of device [5]
```

Or set an environment variable:

```python
device_id = os.getenv('AUDIO_DEVICE_ID')
if device_id and device_id.isdigit():
    return int(device_id)
```

## Recommendation

**Best Solution**: Install **VB-Audio Virtual Cable** ($5 donation, works great)

- ✅ Captures all system audio
- ✅ Works with any sound card
- ✅ Simple one-time setup
- ✅ Lightweight and reliable
- ✅ The app auto-detects it

---

See SETUP.md for more help or check pc_audio_monitor.log for error messages.
