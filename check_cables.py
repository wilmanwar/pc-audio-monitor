#!/usr/bin/env python3
import sounddevice as sd

devices = sd.query_devices()
print("VB-Audio Cable devices:")
for i, d in enumerate(devices):
    if 'cable' in d['name'].lower():
        print(f"  {i}: {d['name']} (in: {d['max_input_channels']}, out: {d['max_output_channels']})")
