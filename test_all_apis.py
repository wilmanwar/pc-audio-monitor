#!/usr/bin/env python3
"""Test different API for audio input."""

import sounddevice as sd
import numpy as np
import time

print("Available audio APIs:")
apis = sd.query_hostapis()
for api in apis:
    print(f"  {api['name']}: devices {api['devices']}")
print()

# Try DirectSound (API 1) - device 7 should be microphone
print("Testing DirectSound API (device 7)...")
try:
    audio_data = sd.rec(
        44100,  # 1 second
        samplerate=44100,
        channels=1,
        device=7,  # DirectSound primary input
        dtype='float32',
        blocksize=2048
    )
    time.sleep(1.1)
    sd.wait(timeout=2.0)
    
    rms = np.sqrt(np.mean(np.square(audio_data)))
    rms_db = 20 * np.log10(rms) if rms > 0 else -np.inf
    print(f"  SUCCESS: {rms_db:.1f} dB")
except Exception as e:
    print(f"  ERROR: {type(e).__name__}")

print()
print("Testing WASAPI (device 17)...")
try:
    audio_data = sd.rec(
        48000,  # 1 second at 48k
        samplerate=48000,
        channels=2,
        device=17,  # WASAPI default input
        dtype='float32',
        blocksize=2048
    )
    time.sleep(1.1)
    sd.wait(timeout=2.0)
    
    if audio_data.ndim > 1:
        audio_data = np.mean(audio_data, axis=1)
    rms = np.sqrt(np.mean(np.square(audio_data)))
    rms_db = 20 * np.log10(rms) if rms > 0 else -np.inf
    print(f"  SUCCESS: {rms_db:.1f} dB")
except Exception as e:
    print(f"  ERROR: {type(e).__name__}")

print()
print("Testing WDM-KS (device 31)...")
try:
    d = sd.query_devices(31)
    sr = int(d['default_samplerate'])
    audio_data = sd.rec(
        sr,  # 1 second
        samplerate=sr,
        channels=min(2, d['max_input_channels']),
        device=31,  # WDM-KS default input
        dtype='float32',
        blocksize=2048
    )
    time.sleep(1.1)
    sd.wait(timeout=2.0)
    
    if audio_data.ndim > 1:
        audio_data = np.mean(audio_data, axis=1)
    rms = np.sqrt(np.mean(np.square(audio_data)))
    rms_db = 20 * np.log10(rms) if rms > 0 else -np.inf
    print(f"  SUCCESS: {rms_db:.1f} dB")
except Exception as e:
    print(f"  ERROR: {type(e).__name__}")
