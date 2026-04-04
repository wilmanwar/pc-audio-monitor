#!/usr/bin/env python3
"""Test device 17 using WASAPI explicitly."""

import sounddevice as sd
import numpy as np
import time

print("Device information:")
d = sd.query_devices(17)
for key, value in d.items():
    print(f"  {key}: {value}")
print()

print("Testing device 17 (WASAPI, should be CABLE Output 2-ch)...")
print("Make sure music is playing...")
print()

try:
    # Use the device's native sample rate
    sr = int(d['default_samplerate'])
    channels = 2
    
    print(f"Recording 2 seconds at {sr} Hz, 2 channels...")
    audio_data = sd.rec(
        sr * 2,  # 2 seconds
        samplerate=sr,
        channels=channels,
        device=17,
        dtype='float32',
        blocksize=2048
    )
    
    time.sleep(2.1)
    sd.wait(timeout=3.0)
    print("Recording complete!")
    print()
    
    # Analyze
    if audio_data.ndim > 1:
        print(f"Audio shape: {audio_data.shape}")
        for ch in range(audio_data.shape[1]):
            ch_data = audio_data[:, ch]
            rms = np.sqrt(np.mean(np.square(ch_data)))
            rms_db = 20 * np.log10(rms) if rms > 0 else -np.inf
            peak = np.max(np.abs(ch_data))
            print(f"  Channel {ch}: RMS={rms_db:7.1f} dB, Peak={peak:.4f}")
    
    print()
    print("SUCCESS - Device works!")

except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
