# Audio Setup Guide - Works on Any Windows PC

This app automatically detects and works with your PC's audio setup. Choose the best option for YOUR system.

## ⚠️ CRITICAL FIRST STEP: Enable Microphone Permissions

**This must be done BEFORE anything else**, even though the app uses VB-Audio Cable or Stereo Mix, not your microphone.

Python's audio libraries need microphone permission to access ANY audio recording device. Without this, all audio tests will fail.

### Enable Microphone Permissions

1. **Open Windows Settings** (Windows Key + I)
2. Go to: **Privacy & security → Microphone**
3. Make sure **"Microphone access"** is turned ON
4. If you see "Python" listed, make sure its toggle is ON
5. Restart the app if it was already running

**If you skip this step, you'll see:**
```
[ERROR] - PortAudioError: Error opening InputStream
[ERROR] - TypeError: wait() got an unexpected keyword
```

---

## How the App Works

The app has **automatic device detection** that tries these options in order:

1. **Stereo Mix** (if available on your PC)
2. **VB-Audio Cable** (if installed)
3. **Microphone** (always available - fallback)

**You don't need to do anything** - it will use whatever works on your PC!

---

## Option 1: Stereo Mix (Best if Available - No Install Needed)

**Best for**: PCs that have Stereo Mix support built-in

### What is Stereo Mix?
A Windows audio feature that loops back system audio so your app can capture it. Many PCs have this, but not all audio drivers support it.

### Setup

1. **Check if Stereo Mix exists on your PC:**
   ```
   Settings → System → Sound → Volume mixer
   Scroll down to "Advanced"
   Look for "Stereo Mix" or "What U Hear"
   ```

2. **If you see it:**
   - If disabled (greyed out): Right-click and select "Enable"
   - If enabled (blue): You're done! Run the app

3. **Run the app:**
   ```bash
   python main.py
   ```

4. **Play music** - you should see audio detection in the logs:
   ```
   RMS: -35.2 dB | State: sound | ACTIVE
   ```

### If Stereo Mix is Not Available

- Your audio driver doesn't support it
- Update your audio driver, OR
- Use **Option 2: VB-Audio Cable** below

### Advantages
- ✅ No additional software
- ✅ Native Windows feature
- ✅ Lowest CPU usage
- ✅ Works on most modern PCs

---

## Option 2: VB-Audio Cable (Recommended - Works on Any PC)

**Best for**: Any PC where Stereo Mix isn't available

VB-Audio Cable creates a virtual audio device that loops system audio back into your PC so the app can capture it.

### Prerequisites
- Download from: https://vb-audio.com/Cable/
- Install and restart Windows

### Setup with Loopback Listening

This is the **recommended setup** that works on virtually any Windows PC:

#### Step 1: Configure VB-Audio Cable Control Panel

1. Open **VBCABLE_ControlPanel.exe**
   - Search in Start menu: "VBCABLE Control Panel"
   - Or find in: `C:\Program Files\VB-Audio\VB-Cable\`

2. Enable Windows mixer integration (if available)
3. Apply settings

#### Step 2: Set VB-Audio as Output Device

1. **Open Windows Sound Settings**
   ```
   Settings → System → Sound
   ```

2. **Set output device to VB-Audio Cable**
   - Under "Output" section
   - Click the device dropdown
   - Select: **"CABLE Input"** or **"VB-Audio Cable"**
   - All system audio now goes to the cable

#### Step 3: Enable Loopback Listening

This lets you hear the audio while the app captures it:

1. **Find VB-Audio Cable recording device**
   ```
   Sound Settings → Volume mixer → Advanced
   Look for "CABLE Output" or "VB-Audio Cable"
   ```

2. **Enable listening:**
   - Right-click CABLE device → Properties
   - "Listen" tab
   - Check: **"Listen to this device"**
   - Set playback device to: **Your speakers**
   - Click Apply → OK

3. **Result:**
   - Audio goes to VB-Audio Cable (app captures it)
   - Audio loops back to speakers (you hear it)
   - Everything works!

#### Step 4: Test It

While music is playing:
```bash
python test_audio_devices.py
```

You should see `CABLE Output` with high audio level (above -45 dB)

#### Step 5: Run the App

```bash
python main.py
```

Expected output:
```
Found Virtual Audio Device: CABLE Output (VB-Audio Virtual Cable) (ID: 4)
Device 4 using sample rate: 44100 Hz
Monitor ready. Waiting for audio status changes...
```

### Advantages
- ✅ Works on virtually all Windows PCs
- ✅ Simple setup with Windows tools
- ✅ Clean audio capture
- ✅ No additional mixer software needed
- ✅ Affordable ($5 one-time, free alternatives exist)

### Troubleshooting

**Cable not showing in Sound Settings?**
- Restart Windows
- Reinstall VB-Audio Cable
- Run VBCABLE_ControlPanel.exe as Administrator

**No audio detected?**
- Verify output is set to CABLE in Sound Settings
- Verify "Listen to this device" is enabled
- Verify playback device is set to speakers
- Restart the application playing audio

**Hearing no audio?**
- Check "Listen to this device" is enabled
- Check playback device is set to your speakers
- Verify Windows volume isn't muted

---

## Option 3: Microphone Fallback (Works on Every PC)

**Best for**: Testing or temporary use

If Stereo Mix and VB-Audio Cable aren't available or configured, the app automatically uses your microphone.

### Limitations
- ❌ Only captures audio near the microphone
- ❌ Won't capture system audio clearly
- ❌ Limited for speaker monitoring

### Setup
Just run the app - it will use your default microphone automatically:

```bash
python main.py
```

---

## Automatic Device Detection

**The app automatically tries devices in this order:**

1. Stereo Mix (if enabled)
2. VB-Audio Cable (if installed)
3. Microphone (always available)

**It uses the first one it finds!**

You don't need to configure anything - just have one of these available and run:
```bash
python main.py
```

---

## Testing Your Setup

To see which device the app can hear audio from:

```bash
# While music/audio is playing, run:
python test_audio_devices.py
```

This shows all devices and their audio levels. Look for:
- **Stereo Mix** - if you see it, it's available
- **CABLE Output** - if VB-Audio Cable is detected
- **Microphone** - always shows up
- **Highest audio level** - this is what the app will use

Example output:
```
[0] Stereo Mix                    [ERROR or No Input]
[4] CABLE Output                  [OK]   -32.5 dB
[1] Microphone Array              [ERROR or No Input]
```

---

## Quick Decision Guide

| Your PC Has... | What To Do |
|---|---|
| Stereo Mix enabled | Just run `python main.py` |
| Stereo Mix but disabled | Enable it in Sound Settings, then run app |
| No Stereo Mix available | Install VB-Audio Cable |
| VB-Audio Cable installed | Enable loopback listening (see Option 2) |
| Nothing configured yet | Try Stereo Mix first, then VB-Audio Cable, or use microphone |

---

## Advanced: Manual Device Selection

If the app picks the wrong device:

1. Run: `python test_audio_devices.py` (with audio playing)
2. Find the correct device and its ID
3. Edit `.env`:
   ```
   AUDIO_DEVICE_ID=4
   ```
4. Save and run: `python main.py`

---

## Troubleshooting: "All Tests Show [ERROR]"

If `python test_audio_devices.py` shows errors for all devices:

### 1. Check Microphone Permissions (Most Common Cause!)

```
Settings → Privacy & security → Microphone
```
- Toggle: "Microphone access" to ON
- If Python is listed, toggle it to ON
- **Restart the app**

This is the most likely cause if nothing works!

### 2. Verify Your Audio Setup

- For Stereo Mix: Check it's enabled in Sound Settings
- For VB-Audio Cable: Check "Listen to this device" is enabled
- For Microphone: Make sure your microphone is plugged in

### 3. Restart Everything

```bash
# Stop the app (Ctrl+C)
# Restart Windows (important!)
# Run test again
python test_audio_devices.py
```

### 4. Check with Microphone Fallback

Try speaking into your microphone while running:
```bash
python test_audio_devices.py
```

If the microphone devices show audio, permissions are now working. Then check Stereo Mix or VB-Audio.

---

## Complete Setup Checklist

- [ ] **Microphone permissions ENABLED** (Settings → Privacy & security → Microphone)
- [ ] Audio device available (Stereo Mix, VB-Audio Cable, or Microphone)
- [ ] Tested with: `python test_audio_devices.py`
- [ ] Audio playing when testing
- [ ] App running: `python main.py`
- [ ] Logs show device detected
- [ ] Audio detection working

---

## For Different PC Configurations

This guide works because the app automatically adapts to YOUR PC:

**New PC with Stereo Mix?**
- Just run the app, it auto-detects

**PC without Stereo Mix?**
- Install VB-Audio Cable, enable loopback
- App auto-detects

**Want to test setup first?**
- Run `python test_audio_devices.py`
- See what devices work on YOUR PC

**Moving the app to another PC?**
- No changes needed!
- It auto-detects on that PC too
- (Just keep `.env` file with your Home Assistant settings)

---

## Need Help?

**Device not detected?**
- Run: `python test_audio_devices.py` (with audio playing)
- Check: Does any device show high audio level (above -45 dB)?
- If yes: That's the device to use
- If no: Audio might not be routing correctly

**Wrong device being used?**
- Note the correct device ID from test tool
- Set `AUDIO_DEVICE_ID=X` in `.env`
- Restart app

**App won't start?**
- Check: Python installed? (run: `python --version`)
- Check: Dependencies installed? (run: `pip install -r requirements.txt`)
- Check: Home Assistant configured? (see `.env.example`)

---

## Summary

This app works on **any Windows PC** because it:

✅ Auto-detects available audio devices  
✅ Uses the best option available on your PC  
✅ Falls back gracefully if some options aren't available  
✅ Works with Stereo Mix, VB-Audio Cable, or Microphone  
✅ No special configuration needed (unless you want to)  
✅ Portable - works when moved to different PCs  

**Just install, configure your audio option, and run!**
