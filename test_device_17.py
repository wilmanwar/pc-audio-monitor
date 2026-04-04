#!/usr/bin/env python3
"""Test the 2-channel CABLE Output device."""

import sounddevice as sd
import numpy as np
import time

print("Testing device 17: CABLE Output (2-channel version)...")
print()

device_id = 17
device_info = sd.query_devices(device_id)
print(f"Device: {device_info['name']}")
print(f"  Input channels: {device_info['max_input_channels']}")
print(f"  Output channels: {device_info['max_output_channels']}")
print()

print("Make sure music is playing...")
print()

try:
    # Record 2 seconds
    print("Recording 2 seconds of audio...")
    audio_data = sd.rec(
        88200,  # 2 seconds at 44100 Hz
        samplerate=44100,
        channels=2,
        device=device_id,
        dtype='float32',
        blocksize=2048
    )
    
    # Wait with visual feedback
    for i in range(4):
        time.sleep(0.5)
        print(f"  ... {(i+1)*0.5:.1f}s")
    
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
    else:
        rms = np.sqrt(np.mean(np.square(audio_data)))
        rms_db = 20 * np.log10(rms) if rms > 0 else -np.inf
        print(f"RMS: {rms_db:.1f} dB")
    
    print()
    if rms_db > -60:
        print("SUCCESS! This device works and is receiving audio!")
        print(f"Set AUDIO_DEVICE_ID=17 in .env to use this device")
    else:
        print("Device opened but no audio detected. Check routing.")

except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
