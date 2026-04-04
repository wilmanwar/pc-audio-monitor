#!/usr/bin/env python3
"""
Audio Device Detector - Helps find the best audio input device for your system.
Run this script to see what audio devices are available and get recommendations.
"""

import sounddevice as sd
import numpy as np
import sys

def analyze_device(device_id, device_info, test_recording=False):
    """Analyze a single audio device and try to record from it."""
    max_channels = device_info['max_input_channels']
    if max_channels == 0:
        return None
    
    recommendation = []
    device_name = device_info['name'].lower()
    
    # Score based on device name
    if any(x in device_name for x in ['stereo mix', 'wasapi', 'loopback', 'what u hear']):
        recommendation.append(("⭐⭐⭐", "Stereo Mix - Best system audio capture!"))
    elif any(x in device_name for x in ['voicemeeter point']):
        recommendation.append(("⭐⭐⭐", "Voicemeeter Point - Excellent system audio capture!"))
    elif any(x in device_name for x in ['voicemeeter out']):
        recommendation.append(("⭐⭐", "VoiceMeeter VAIO - Good (install Voicemeeter first)"))
    elif any(x in device_name for x in ['cable output', 'cable input']):
        recommendation.append(("⭐⭐", "VB-Audio Cable - Good (install VB-Audio Cable)"))
    elif any(x in device_name for x in ['microphone']):
        recommendation.append(("⭐", "Microphone - Fallback only (won't capture system audio)"))
    
    # Try to record and test
    works = None
    if test_recording:
        try:
            audio_data = sd.rec(int(44100 * 0.5), samplerate=44100, channels=1, 
                              device=device_id, dtype='float32')
            sd.wait()
            works = True
        except Exception as e:
            works = False
    
    return {
        'device_id': device_id,
        'name': device_info['name'],
        'channels': max_channels,
        'sample_rate': device_info['default_samplerate'],
        'recommendation': recommendation,
        'works': works
    }

def main():
    print("=" * 80)
    print("PC Audio Monitor - Device Detection Utility")
    print("=" * 80)
    print()
    
    try:
        devices = sd.query_devices()
    except Exception as e:
        print(f"ERROR: Could not query audio devices: {e}")
        sys.exit(1)
    
    print(f"Found {len(devices)} audio devices on this system.\n")
    
    # Find input devices with recommendations
    candidates = []
    
    for idx, device in enumerate(devices):
        if device['max_input_channels'] > 0:
            result = analyze_device(idx, device, test_recording=False)
            if result:
                candidates.append(result)
    
    if not candidates:
        print("ERROR: No audio input devices found!")
        sys.exit(1)
    
    # Display input devices
    print("AUDIO INPUT DEVICES:")
    print("-" * 80)
    
    for item in candidates:
        print(f"\n[{item['device_id']}] {item['name']}")
        print(f"    Channels: {item['channels']} | Sample Rate: {int(item['sample_rate'])} Hz")
        if item['recommendation']:
            for stars, desc in item['recommendation']:
                print(f"    {stars} {desc}")
        else:
            print("    ℹ️  Unknown device type")
    
    # Recommendations
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    
    # Check what's available
    stereo_mix = any('stereo mix' in c['name'].lower() or 'wasapi' in c['name'].lower() 
                     for c in candidates)
    voicemeeter_point = any('voicemeeter point' in c['name'].lower() for c in candidates)
    voicemeeter_vaio = any('voicemeeter out' in c['name'].lower() for c in candidates)
    
    print("\n✓ AVAILABLE OPTIONS ON YOUR SYSTEM:\n")
    
    if stereo_mix:
        print("  1. ⭐⭐⭐ STEREO MIX")
        print("     ✓ Available on your PC")
        print("     ✓ Best option - captures all system audio")
        print("     ✓ Already enabled")
        print("     → Use this! No additional software needed.\n")
    else:
        print("  1. ⭐⭐⭐ STEREO MIX")
        print("     ✗ NOT available on your PC")
        print("     ✗ Either disabled, or your audio driver doesn't support it")
        print("     → Try enabling in Sound Settings or update your audio driver\n")
    
    if voicemeeter_point:
        print("  2. ⭐⭐⭐ VOICEMEETER POINT DEVICES")
        print("     ✓ Available on your PC (VoiceMeeter is installed)")
        print("     ✓ Excellent system audio capture")
        if not stereo_mix:
            print("     → Recommended! This is the best option if Stereo Mix is unavailable.\n")
        else:
            print()
    elif voicemeeter_vaio:
        print("  2. ⭐⭐⭐ VOICEMEETER (VAIO VERSION)")
        print("     ✓ Voicemeeter VAIO is installed")
        print("     ℹ️  This app works better with Voicemeeter Point")
        print("     → Consider upgrading to the latest Voicemeeter version.\n")
    else:
        print("  2. ⭐⭐⭐ VOICEMEETER (NOT INSTALLED)")
        print("     ✗ Not on your PC yet")
        print("     → Consider installing from https://vb-audio.com/Voicemeeter/\n")
    
    print("  3. ⭐ MICROPHONE (FALLBACK)")
    print("     ✓ Always available on any PC")
    print("     ✗ Won't capture system audio clearly")
    print("     → Use only if other options aren't available.\n")
    
    # Quick start guide
    print("=" * 80)
    print("QUICK START GUIDE FOR YOUR SYSTEM")
    print("=" * 80)
    print()
    
    if stereo_mix:
        print("✓ YOUR SYSTEM IS READY!")
        print()
        print("  1. No additional setup needed")
        print("  2. Just run: python main.py")
        print("  3. The app will automatically detect Stereo Mix")
        print()
    elif voicemeeter_point:
        print("✓ YOUR SYSTEM IS READY!")
        print()
        print("  1. VoiceMeeter Point devices detected")
        print("  2. Just run: python main.py")
        print("  3. The app will automatically use Voicemeeter Point")
        print()
    else:
        print("⚠️  YOUR SYSTEM NEEDS SETUP")
        print()
        print("  Best option: Install VoiceMeeter")
        print("  1. Download from: https://vb-audio.com/Voicemeeter/")
        print("  2. Install and restart Windows")
        print("  3. Run: python main.py")
        print()
        print("  Alternative: Enable Stereo Mix")
        print("  1. Settings → Sound → Advanced → Volume mixer")
        print("  2. Look for 'Stereo Mix' and enable it")
        print("  3. Run: python main.py")
        print()
    
    # Troubleshooting
    print("=" * 80)
    print("NEED HELP?")
    print("=" * 80)
    print()
    print("  • Read: AUDIO_SETUP_GUIDE.md")
    print("  • More help: SETUP.md")
    print("  • Audio alternatives: STEREO_MIX_ALTERNATIVES.md")
    print()

if __name__ == "__main__":
    main()
