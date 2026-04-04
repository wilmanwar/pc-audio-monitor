#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Audio Device Detector - Helps find the best audio input device for your system.
Run this script to see what audio devices are available and get recommendations.
"""

import sounddevice as sd
import numpy as np
import sys
import io

# Force UTF-8 output on Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def analyze_device(device_id, device_info, test_recording=False):
    """Analyze a single audio device and try to record from it."""
    max_channels = device_info['max_input_channels']
    if max_channels == 0:
        return None
    
    recommendation = []
    device_name = device_info['name'].lower()
    
    # Score based on device name
    if any(x in device_name for x in ['stereo mix', 'wasapi', 'loopback', 'what u hear']):
        recommendation.append(("[***]", "Stereo Mix - Best system audio capture! (native Windows)"))
    elif any(x in device_name for x in ['cable output', 'cable input']):
        recommendation.append(("[***]", "VB-Audio Cable - Excellent system audio capture! (with loopback listening)"))
    elif any(x in device_name for x in ['microphone']):
        recommendation.append(("[*]", "Microphone - Fallback only (limited quality)"))
    
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
            print("    [?] Unknown device type")
    
    # Recommendations
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    
    # Check what's available
    stereo_mix = any('stereo mix' in c['name'].lower() or 'wasapi' in c['name'].lower() 
                     for c in candidates)
    cable = any('cable' in c['name'].lower() for c in candidates)
    
    print("\n[OK] AVAILABLE OPTIONS ON YOUR SYSTEM:\n")
    
    if stereo_mix:
        print("  1. [***] STEREO MIX")
        print("     [OK] Available on your PC")
        print("     [OK] Best option - native Windows loopback")
        print("     [OK] No additional software needed")
        print("     --> Use this! Just enable if not already.\n")
    else:
        print("  1. [***] STEREO MIX")
        print("     [NO] NOT available on your PC")
        print("     [NO] Either disabled or your audio driver doesn't support it")
        print("     --> Update audio driver or use VB-Audio Cable instead\n")
    
    if cable:
        print("  2. [***] VB-AUDIO CABLE")
        print("     [OK] Available on your PC (VB-Audio Cable is installed)")
        print("     [OK] Excellent system audio capture with loopback listening")
        if not stereo_mix:
            print("     --> Recommended! This is the best option if Stereo Mix is unavailable.\n")
        else:
            print()
    else:
        print("  2. [***] VB-AUDIO CABLE")
        print("     [NO] Not installed on your PC yet")
        print("     --> Download from https://vb-audio.com/Cable/\n")
    
    print("  3. [*] MICROPHONE (FALLBACK)")
    print("     [OK] Always available on any PC")
    print("     [NO] Limited quality (won't capture system audio clearly)")
    print("     --> Use only if other options aren't available.\n")
    
    # Quick start guide
    print("=" * 80)
    print("QUICK START GUIDE FOR YOUR SYSTEM")
    print("=" * 80)
    print()
    
    if stereo_mix:
        print("[OK] YOUR SYSTEM IS READY!")
        print()
        print("  1. No additional setup needed")
        print("  2. Just run: python main.py")
        print("  3. The app will automatically detect Stereo Mix")
        print()
    elif cable:
        print("[OK] YOUR SYSTEM IS READY!")
        print()
        print("  1. VB-Audio Cable is installed")
        print("  2. Open VBCABLE_ControlPanel.exe to configure")
        print("  3. Set output to CABLE in Windows Sound Settings")
        print("  4. Enable loopback listening in Sound Settings")
        print("  5. Run: python main.py")
        print()
    else:
        print("[!] YOUR SYSTEM NEEDS SETUP")
        print()
        print("  Best option: Install VB-Audio Cable")
        print("  1. Download from: https://vb-audio.com/Cable/")
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
    print("  - Read: AUDIO_SETUP_GUIDE.md (complete setup guide)")
    print("  - VB-Audio Cable setup: VBCABLE_SETUP.md")
    print("  - Troubleshooting: SETUP.md")
    print()

if __name__ == "__main__":
    main()
