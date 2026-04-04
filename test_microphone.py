#!/usr/bin/env python3
"""Test if microphone recording works at all."""

import sounddevice as sd
import numpy as np
import time

print("Testing microphone to verify recording works...")
print("SPEAK INTO YOUR MICROPHONE NOW!")
print()

device_id = 2  # Microphone Array

try:
    print("Recording 2 seconds...")
    audio_data = sd.rec(
        88200,  # 2 seconds at 44100 Hz
        samplerate=44100,
        channels=1,
        device=device_id,
        dtype='float32'
    )
    
    sd.wait()  # Wait for recording to complete
    print("Recording complete!")
    print()
    
    rms = np.sqrt(np.mean(np.square(audio_data)))
    rms_db = 20 * np.log10(rms) if rms > 0 else -np.inf
    peak = np.max(np.abs(audio_data))
    
    print(f"Microphone RMS: {rms_db:.1f} dB")
    print(f"Microphone Peak: {peak:.4f}")
    
    if rms_db > -60:
        print("✓ Microphone recording works!")
    else:
        print("✗ Microphone recorded but very quiet")

except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
