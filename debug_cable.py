#!/usr/bin/env python3
"""Debug audio capture to see actual audio data."""

import sounddevice as sd
import numpy as np
import time

print("Testing CABLE Output device directly...")
print()

device_id = 1  # CABLE Output
device_info = sd.query_devices(device_id)
print(f"Device: {device_info['name']}")
print(f"  Channels: {device_info['max_input_channels']} input, {device_info['max_output_channels']} output")
print()

# Try different configurations
configs = [
    {"channels": 1, "name": "Mono"},
    {"channels": 2, "name": "Stereo"},
    {"channels": 4, "name": "4 Channels"},
]

for config in configs:
    print(f"Testing {config['name']} ({config['channels']} channels)...")
    try:
        # Record 2 seconds of audio
        duration = 2.0
        sample_rate = 44100
        
        audio_data = sd.rec(
            int(sample_rate * duration),
            samplerate=sample_rate,
            channels=config['channels'],
            device=device_id,
            dtype='float32',
            blocksize=2048
        )
        
        # Show recording in progress
        for i in range(4):
            time.sleep(0.5)
            print(f"  Recording... {int((i+1)*0.5*2)}s")
        
        sd.wait(timeout=3.0)
        
        # Calculate statistics
        if audio_data.ndim > 1:
            print(f"  Shape: {audio_data.shape}")
            for ch in range(min(2, audio_data.shape[1])):
                ch_data = audio_data[:, ch]
                rms = np.sqrt(np.mean(np.square(ch_data)))
                rms_db = 20 * np.log10(rms) if rms > 0 else -np.inf
                peak = np.max(np.abs(ch_data))
                print(f"    Ch {ch}: RMS={rms_db:7.1f} dB, Peak={peak:.4f}")
        else:
            rms = np.sqrt(np.mean(np.square(audio_data)))
            rms_db = 20 * np.log10(rms) if rms > 0 else -np.inf
            peak = np.max(np.abs(audio_data))
            print(f"  Mono: RMS={rms_db:7.1f} dB, Peak={peak:.4f}")
        
        print()
    except Exception as e:
        print(f"  Error: {type(e).__name__}: {e}")
        print()

print("Done!")
