#!/usr/bin/env python3
import sounddevice as sd

d = sd.query_devices(17)
print(f"Default sample rate: {d['default_samplerate']}")
