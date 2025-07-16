"""
Om_E_Lm/ome/handlers/audio_handler.py

Handles audio streaming, filtering, and playback for the OM‑E voice assistant.

Main Purpose:
- Capture microphone input in frames (e.g., 50ms chunks)
- Apply pre-filters (HPF/BPF) to clean audio
- Provide filtered audio frames to downstream modules (VAD, STT)
- Play AI responses using TTS (OpenVoice V2, stub for now)

Key Features:
- Audio Capture: Uses sounddevice for cross-platform, low-latency mic input.
- Filtering: Applies high-pass and band-pass filters using scipy.signal.
- CLI Test: Can be run as a script to record, filter, save, and play back audio.
- Configurable: Reads device/sample rate from env.py if available, otherwise prompts user.

How to Use (Command Line):
    python -m Om_E_Lm.ome.handlers.audio_handler --test
    # Records 3 seconds of audio, applies filters, saves to temp_mic.wav, and plays back.

When to Use:
- As a foundational module for all audio input/output in the OM‑E pipeline.
- For testing mic setup and audio quality.
"""
import sounddevice as sd
import numpy as np
import soundfile as sf
from scipy.signal import butter, lfilter
import os
import sys

# --- ENV CONFIG HANDLING ---
ENV_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../env.py'))
AUDIO_SAMPLE_RATE = 16000
AUDIO_DEVICE = None
HPF_CUTOFF = 80
BPF_RANGE = (300, 3400)

# Try to load AUDIO_DEVICE from env.py
if os.path.exists(ENV_PATH):
    try:
        with open(ENV_PATH, 'r') as f:
            for line in f:
                if line.strip().startswith('AUDIO_DEVICE'):
                    AUDIO_DEVICE = int(line.split('=')[1].strip())
    except Exception as e:
        print(f"[audio_handler] Could not read AUDIO_DEVICE from env.py: {e}")

# If not set, prompt user to select device and save to env.py
if AUDIO_DEVICE is None:
    print("\nNo AUDIO_DEVICE set in env.py. Please select an input device:")
    devices = sd.query_devices()
    for idx, dev in enumerate(devices):
        print(f"{idx}: {dev['name']} (inputs: {dev['max_input_channels']}, outputs: {dev['max_output_channels']})")
    while True:
        try:
            idx = int(input("Enter device index for microphone input: "))
            if devices[idx]['max_input_channels'] >= 1:
                AUDIO_DEVICE = idx
                break
            else:
                print("Selected device does not support input. Try again.")
        except Exception:
            print("Invalid input. Enter a valid device index.")
    # Save to env.py
    try:
        lines = []
        if os.path.exists(ENV_PATH):
            with open(ENV_PATH, 'r') as f:
                lines = f.readlines()
        found = False
        for i, line in enumerate(lines):
            if line.strip().startswith('AUDIO_DEVICE'):
                lines[i] = f'AUDIO_DEVICE={AUDIO_DEVICE}\n'
                found = True
        if not found:
            lines.append(f'AUDIO_DEVICE={AUDIO_DEVICE}\n')
        with open(ENV_PATH, 'w') as f:
            f.writelines(lines)
        print(f"Saved AUDIO_DEVICE={AUDIO_DEVICE} to env.py")
    except Exception as e:
        print(f"[audio_handler] Could not save AUDIO_DEVICE to env.py: {e}")

def apply_filters(audio_chunk, sample_rate=AUDIO_SAMPLE_RATE):
    """
    Apply high-pass and band-pass filters to the audio chunk.
    Args:
        audio_chunk (np.ndarray): 1D array of audio samples (float32)
        sample_rate (int): Sample rate in Hz
    Returns:
        np.ndarray: Filtered audio chunk
    """
    # High-pass filter
    b, a = butter(1, HPF_CUTOFF / (0.5 * sample_rate), btype='high')
    filtered = lfilter(b, a, audio_chunk)
    # Band-pass filter
    b, a = butter(1, [BPF_RANGE[0] / (0.5 * sample_rate), BPF_RANGE[1] / (0.5 * sample_rate)], btype='band')
    filtered = lfilter(b, a, filtered)
    return filtered

def stream_audio(callback, duration=3, sample_rate=AUDIO_SAMPLE_RATE, device=AUDIO_DEVICE):
    """
    Stream audio from the microphone, apply filters, and pass to callback.
    Args:
        callback (function): Function to call with (filtered_audio, sample_rate)
        duration (float): Duration to record in seconds
        sample_rate (int): Sample rate in Hz
        device (int): Audio device index
    """
    print(f"Recording {duration}s of audio...")
    audio = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='float32', device=device)
    sd.wait()
    audio = audio.flatten()
    filtered = apply_filters(audio, sample_rate)
    callback(filtered, sample_rate)

def speak_text(text, voice="default"):
    """
    Placeholder: Play a WAV file as TTS output (to be replaced with OpenVoice).
    Args:
        text (str): Text to speak
        voice (str): Voice identifier (not used yet)
    """
    print(f"[speak_text] Would speak: {text}")
    # For now, just play response.wav if it exists
    try:
        data, sr = sf.read('Om_E_Lm/data/audio/response.wav')
        sd.play(data, sr)
        sd.wait()
    except Exception as e:
        print(f"[speak_text] Playback error: {e}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Test audio capture, filtering, and playback.")
    parser.add_argument('--test', action='store_true', help='Run a test: record, filter, save, and play back audio')
    args = parser.parse_args()
    if args.test:
        AUDIO_OUT_PATH = 'Om_E_Lm/data/audio/temp_mic.wav'
        def save_and_play(audio, sample_rate):
            print(f"Saving filtered audio to {AUDIO_OUT_PATH}")
            sf.write(AUDIO_OUT_PATH, audio, sample_rate)
            print("Playing back filtered audio...")
            sd.play(audio, sample_rate)
            sd.wait()
        stream_audio(save_and_play, duration=3)
        print("Test complete.")
    else:
        parser.print_help() 