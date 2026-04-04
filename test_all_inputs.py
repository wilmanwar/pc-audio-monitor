#!/usr/bin/env python3
"""Check all input devices."""

import sounddevice as sd
import numpy as np
import time

devices = sd.query_devices()

print("Testing all INPUT devices...")
print()

for i, d in enumerate(devices):
    if d['max_input_channels'] == 0:
        continue
    
    name = d['name']
    in_ch = d['max_input_channels']
    
    print(f"[{i:2d}] {name:60s} ", end="", flush=True)
    
    # Try to record
    try:
        channels = min(2, in_ch)
        audio_data = sd.rec(
            44100,  # 1 second
            samplerate=44100,
            channels=channels,
            device=i,
            dtype='float32',
            blocksize=2048
        )
        time.sleep(1.1)
        sd.wait(timeout=1.0)
        
        # Calculate RMS
        if audio_data.ndim > 1:
            audio_data = np.mean(audio_data, axis=1)
        
        rms = np.sqrt(np.mean(np.square(audio_data)))
        rms_db = 20 * np.log10(rms) if rms > 0 else -np.inf
        
        status = "[OK]" if rms_db > -80 else "[FAIL]"
        print(f"{status} {rms_db:7.1f} dB")
    except Exception as e:
        print(f"[ERROR]")

print()
print("Devices showing [OK] with dB > -60 are working and have audio.")
