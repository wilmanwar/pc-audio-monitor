#!/usr/bin/env python3
"""Check for Stereo Mix device."""

import sounddevice as sd
import numpy as np
import time

devices = sd.query_devices()

print("Looking for Stereo Mix or similar loopback devices...")
print()

stereo_mix_devices = []
for i, d in enumerate(devices):
    name = d['name'].lower()
    if any(keyword in name for keyword in ['stereo mix', 'wave out', 'what u hear', 'loopback']):
        if d['max_input_channels'] > 0:
            stereo_mix_devices.append((i, d))

if not stereo_mix_devices:
    print("No Stereo Mix device found!")
    print()
    print("Available INPUT devices:")
    for i, d in enumerate(devices):
        if d['max_input_channels'] > 0:
            print(f"  [{i}] {d['name']}")
    exit(1)

print(f"Found {len(stereo_mix_devices)} Stereo Mix device(s):")
print()

for idx, device in stereo_mix_devices:
    name = device['name']
    in_ch = device['max_input_channels']
    sr = device['default_samplerate']
    
    print(f"[{idx}] {name}")
    print(f"    Channels: {in_ch}, Sample Rate: {int(sr)} Hz")
    print(f"    Testing... ", end="", flush=True)
    
    try:
        # Try to record
        channels = min(2, in_ch)
        audio_data = sd.rec(
            int(sr * 2),  # 2 seconds
            samplerate=int(sr),
            channels=channels,
            device=idx,
            dtype='float32',
            blocksize=2048
        )
        time.sleep(2.1)
        sd.wait(timeout=3.0)
        
        # Calculate RMS
        if audio_data.ndim > 1:
            audio_data = np.mean(audio_data, axis=1)
        
        rms = np.sqrt(np.mean(np.square(audio_data)))
        rms_db = 20 * np.log10(rms) if rms > 0 else -np.inf
        
        status = "SUCCESS" if rms_db > -60 else f"Quiet ({rms_db:.1f} dB)"
        print(f"{status}")
    except Exception as e:
        print(f"ERROR - {type(e).__name__}")
    
    print()

print("Use the device marked SUCCESS above!")
