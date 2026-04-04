#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Audio Device Test Tool - Test which devices are receiving system audio.

This script helps you figure out which audio device is getting your system audio.
Play music/audio and run this script to see which devices detect sound.
"""

import sounddevice as sd
import numpy as np
import sys
import io
import time

# Force UTF-8 output on Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_device(device_id, duration=2.0, sample_rate=44100):
    """Test a single device to see if it has audio."""
    device_info = sd.query_devices(device_id)
    
    if device_info['max_input_channels'] == 0:
        return None
    
    try:
        # Record audio - use the device's native channels if available
        channels = min(2, device_info['max_input_channels'])
        
        # Record a sample
        audio_data = sd.rec(
            int(sample_rate * duration),
            samplerate=sample_rate,
            channels=channels,
            device=device_id,
            dtype='float32',
            blocksize=2048
        )
        # Wait for recording to complete
        sd.wait()
        
        # Calculate RMS level
        if audio_data.ndim > 1:
            audio_data = np.mean(audio_data, axis=1)
        
        rms = np.sqrt(np.mean(np.square(audio_data)))
        rms_db = 20 * np.log10(rms) if rms > 0 else -np.inf
        
        return rms_db
    except Exception as e:
        import traceback
        return None


def main():
    print("=" * 80)
    print("AUDIO DEVICE TEST TOOL")
    print("=" * 80)
    print()
    print("This will test each audio device to see if it's receiving system audio.")
    print()
    
    devices = sd.query_devices()
    
    # Get list of input devices
    input_devices = []
    for idx, device in enumerate(devices):
        if device['max_input_channels'] > 0:
            input_devices.append(idx)
    
    if not input_devices:
        print("ERROR: No audio input devices found!")
        return 1
    
    print(f"Found {len(input_devices)} audio input devices.")
    print()
    print("START PLAYING YOUR MUSIC/AUDIO NOW")
    print("Testing each device for 2 seconds...")
    print()
    print("-" * 80)
    
    results = []
    for idx in input_devices:
        device = devices[idx]
        device_name = device['name']
        short_name = device_name[:60] if len(device_name) > 60 else device_name
        
        print(f"[{idx:3d}] {short_name:60s}", end="", flush=True)
        level = test_device(idx, duration=2.0)
        
        if level is not None:
            status = " [OK]  " if level > -50 else " [Quiet]"
            print(f" {status} {level:7.1f} dB")
            results.append((idx, device_name, level))
        else:
            print(" [ERROR or No Input]")
    
    print("-" * 80)
    print()
    
    # Show results
    if not results:
        print("No devices recorded audio.")
        print()
        print("Possible reasons:")
        print("  1. Your music/audio wasn't playing during the test")
        print("  2. Your audio routing isn't set up correctly")
        print("     - For Stereo Mix: Check Windows Sound settings (advanced tab)")
        print("     - For VB-Audio Cable: Run VBCABLE_ControlPanel.exe and enable loopback")
        print("     - For Microphone: Speak into your microphone during the test")
        print()
        return 1
    
    # Sort by audio level
    results.sort(key=lambda x: x[2], reverse=True)
    
    print("DEVICES WITH DETECTED AUDIO:")
    print()
    for idx, name, level in results:
        if level > -60:
            print(f"*** BEST: Device {idx}: {name}")
            print(f"    Audio level: {level:.1f} dB")
            print()
    
    if results[0][2] > -50:
        device_id = results[0][0]
        print("RECOMMENDATION:")
        print(f"  Use AUDIO_DEVICE_ID={device_id} in your .env file")
        print()
        print("Or just use the default AUTO_DETECT_AUDIO=false setting")
        print("and the app will automatically use the best available device.")
    else:
        print("WARNING: Audio levels detected but all below -50 dB (very quiet)")
        print("Check your audio routing and playback volume")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
