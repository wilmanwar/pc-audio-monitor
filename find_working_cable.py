#!/usr/bin/env python3
"""Find which CABLE device actually works."""

import sounddevice as sd
import numpy as np
import time

devices = sd.query_devices()

print("Testing all CABLE devices for recording capability...")
print()

cable_devices = []
for i, d in enumerate(devices):
    if 'cable' in d['name'].lower():
        cable_devices.append((i, d))

for idx, device in cable_devices:
    name = device['name']
    in_ch = device['max_input_channels']
    out_ch = device['max_output_channels']
    
    print(f"[{idx:2d}] {name:50s} in:{in_ch:2d} out:{out_ch:2d} ", end="", flush=True)
    
    if in_ch == 0:
        print("[ SKIP - output only ]")
        continue
    
    # Try to open and record a tiny sample
    try:
        channels = min(2, in_ch)
        audio_data = sd.rec(
            44100,  # 1 second
            samplerate=44100,
            channels=channels,
            device=idx,
            dtype='float32'
        )
        time.sleep(1.1)
        sd.wait()
        
        # Calculate RMS
        if audio_data.ndim > 1:
            audio_data = np.mean(audio_data, axis=1)
        
        rms = np.sqrt(np.mean(np.square(audio_data)))
        rms_db = 20 * np.log10(rms) if rms > 0 else -np.inf
        
        print(f"[ OK - {rms_db:6.1f} dB ]")
    except Exception as e:
        error_msg = str(e)
        if 'PaErrorCode -9999' in error_msg:
            print(f"[ FAIL - PortAudio -9999 error ]")
        else:
            print(f"[ FAIL - {type(e).__name__} ]")

print()
print("Look for device with [ OK ] status above.")
