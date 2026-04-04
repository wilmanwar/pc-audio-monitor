#!/usr/bin/env python3
"""Check available audio APIs."""

import sounddevice as sd

print("Available audio APIs:")
print(sd.query_hostapis())
print()

# List which one is default
default_api = sd.default.hostapi
print(f"Default API: {sd.query_hostapis(default_api)['name']}")
