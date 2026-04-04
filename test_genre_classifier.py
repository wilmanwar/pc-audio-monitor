#!/usr/bin/env python3
"""Test music genre classifier on live audio input."""

import sys
import sounddevice as sd
import numpy as np
from music_classifier import MusicClassifier
import time

def test_music_classifier(duration: float = 5.0, device_id: int = 1, num_tests: int = 1):
    """
    Test music classifier on live audio input.
    
    Args:
        duration: Recording duration in seconds
        device_id: Audio device ID to record from
        num_tests: Number of tests to run (for testing multiple genres)
    """
    print("=" * 80)
    print("MUSIC GENRE CLASSIFIER TEST")
    print("=" * 80)
    print()
    
    classifier = MusicClassifier(samplerate=44100)
    
    results = []
    
    for test_num in range(num_tests):
        if num_tests > 1:
            print(f"\n--- Test {test_num + 1}/{num_tests} ---")
            genre_hint = input("What genre/type are you about to play? (e.g., Classical, Pop, Rock, Jazz, Electronic, Speech): ").strip()
        else:
            genre_hint = ""
        
        print(f"Recording for {duration} seconds from device {device_id}...")
        if not genre_hint:
            print("Play different types of audio to test detection:")
            print("  - Music (classical, pop, rock, electronic, etc.)")
            print("  - Speech/Conversation")
            print("  - Ambient/Noise")
        else:
            print(f"Play: {genre_hint}")
        print()
        
        try:
            # Record audio
            audio_data = sd.rec(
                int(44100 * duration),
                samplerate=44100,
                channels=1,
                device=device_id,
                dtype='float32'
            )
            sd.wait()
        
        print("Recording complete!")
        print()
        
        # Classify
        print("Analyzing audio...")
        print()
        
        result = classifier.classify_audio(audio_data)
        
        # Display results
        print("-" * 80)
        print("CLASSIFICATION RESULTS")
        print("-" * 80)
        print()
        
        print(f"Music vs Non-Music:")
        print(f"  Is Music: {result['is_music']}")
        print(f"  Confidence: {result['music_confidence']:.1%}")
        print()
        
        print(f"Genre Classification:")
        print(f"  Genre: {result['genre']}")
        print(f"  Confidence: {result['genre_confidence']:.1%}")
        print()
        
        print("Feature Analysis:")
        features = result['features']
        if features:
            print(f"  Spectral Entropy: {features.get('spectral_entropy', 0):.3f} (0=organized, 1=random)")
            print(f"  Zero Crossing Rate: {features.get('zero_crossing_rate', 0):.4f}")
            print(f"  Energy Stability: {features.get('energy_stability', 0):.3f} (0=stable)")
            print(f"  Harmonic Peaks: {features.get('harmonic_peaks', 0):.3f}")
            print(f"  Spectral Centroid: {features.get('spectral_centroid', 0):.0f} Hz")
            print()
            
            print("Frequency Content:")
            print(f"  Bass (20-250Hz): {features.get('bass_content', 0):.1%}")
            print(f"  Midrange (250-2kHz): {features.get('mid_content', 0):.1%}")
            print(f"  Treble (>2kHz): {features.get('brightness', 0):.1%}")
            print(f"  Percussion (5-20kHz): {features.get('percussion_content', 0):.1%}")
        print()
        
        print("-" * 80)
        
        # Interpretation
        print()
        print("INTERPRETATION:")
        if not result['is_music']:
            print(f"⊘ Detected as {result['genre']} (not music)")
            print("  The audio contains speech, noise, or other non-musical content")
        else:
            print(f"✓ Detected as {result['genre']} music")
            if result['genre_confidence'] > 0.7:
                print(f"  High confidence ({result['genre_confidence']:.0%})")
            elif result['genre_confidence'] > 0.5:
                print(f"  Moderate confidence ({result['genre_confidence']:.0%})")
            else:
                print(f"  Low confidence ({result['genre_confidence']:.0%}) - genre unclear")
        
        print()
        
        # Store results
        results.append({
            'expected': genre_hint,
            'detected': result['genre'],
            'confidence': result['genre_confidence'],
            'is_music': result['is_music'],
            'features': features
        })
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Summary if multiple tests
    if num_tests > 1:
        print("\n" + "=" * 80)
        print("SUMMARY OF ALL TESTS")
        print("=" * 80)
        print()
        print(f"{'Expected':<15} {'Detected':<15} {'Confidence':<12} {'Match':<10}")
        print("-" * 80)
        
        correct = 0
        for result in results:
            expected = result['expected'][:14] if result['expected'] else "Unknown"
            detected = result['detected'][:14]
            confidence = result['confidence']
            match = "✓" if (expected.lower() in detected.lower() or detected.lower() in expected.lower()) else "✗"
            if match == "✓":
                correct += 1
            print(f"{expected:<15} {detected:<15} {confidence:>10.0%}  {match:>8}")
        
        print("-" * 80)
        accuracy = (correct / num_tests * 100) if num_tests > 0 else 0
        print(f"Accuracy: {correct}/{num_tests} ({accuracy:.0f}%)")
        print()
    
    return 0


if __name__ == "__main__":
    # Check arguments
    device_id = 1  # Default: CABLE Output
    num_tests = 1
    
    if len(sys.argv) > 1:
        try:
            device_id = int(sys.argv[1])
        except ValueError:
            print(f"Usage: python test_genre_classifier.py [device_id] [num_tests]")
            print(f"Examples:")
            print(f"  python test_genre_classifier.py                # Single test, default device")
            print(f"  python test_genre_classifier.py 1             # Single test, device 1")
            print(f"  python test_genre_classifier.py 1 5           # 5 tests, device 1 (for tuning)")
            print()
            return 1
    
    if len(sys.argv) > 2:
        try:
            num_tests = int(sys.argv[2])
        except ValueError:
            pass
    
    sys.exit(test_music_classifier(duration=5.0, device_id=device_id, num_tests=num_tests))
