#!/usr/bin/env python3
"""Test device 17 with correct sample rate."""

import sounddevice as sd
import numpy as np
import time

print("Testing device 17 with 48000 Hz...")
print()

device_id = 17

print("Make sure music is playing...")
print()

try:
    # Record 2 seconds at 48000 Hz
    print("Recording 2 seconds of audio at 48kHz...")
    audio_data = sd.rec(
        96000,  # 2 seconds at 48000 Hz
        samplerate=48000,
        channels=2,
        device=device_id,
        dtype='float32',
        blocksize=2048
    )
    
    # Wait
    for i in range(4):
        time.sleep(0.5)
        print(f"  ... {(i+1)*0.5:.1f}s")
    
    sd.wait(timeout=3.0)
    print("Recording complete!")
    print()
    
    # Analyze
    if audio_data.ndim > 1:
        print(f"Audio shape: {audio_data.shape}")
        rms_values = []
        for ch in range(audio_data.shape[1]):
            ch_data = audio_data[:, ch]
            rms = np.sqrt(np.mean(np.square(ch_data)))
            rms_db = 20 * np.log10(rms) if rms > 0 else -np.inf
            peak = np.max(np.abs(ch_data))
            rms_values.append(rms_db)
            print(f"  Channel {ch}: RMS={rms_db:7.1f} dB, Peak={peak:.4f}")
        avg_db = np.mean(rms_values)
    else:
        rms = np.sqrt(np.mean(np.square(audio_data)))
        rms_db = 20 * np.log10(rms) if rms > 0 else -np.inf
        avg_db = rms_db
        print(f"RMS: {rms_db:.1f} dB")
    
    print()
    if avg_db > -60:
        print("SUCCESS! This device works and is receiving audio!")
        print(f"Use device 17 at 48000 Hz sample rate")
    else:
        print("Device opened but audio level is very low/no audio. Check routing.")

except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
