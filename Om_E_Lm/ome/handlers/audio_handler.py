import sounddevice as sd
import numpy as np
import soundfile as sf
from scipy.signal import butter, lfilter
import os
import configparser

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
        # Read all lines, update or append AUDIO_DEVICE
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
    """Apply HPF and BPF to the audio chunk."""
    # High-pass filter
    b, a = butter(1, HPF_CUTOFF / (0.5 * sample_rate), btype='high')
    filtered = lfilter(b, a, audio_chunk)
    # Band-pass filter
    b, a = butter(1, [BPF_RANGE[0] / (0.5 * sample_rate), BPF_RANGE[1] / (0.5 * sample_rate)], btype='band')
    filtered = lfilter(b, a, filtered)
    return filtered


def stream_audio(callback, duration=3, sample_rate=AUDIO_SAMPLE_RATE, device=AUDIO_DEVICE):
    """Stream audio from mic, apply filters, and pass to callback."""
    print(f"Recording {duration}s of audio...")
    audio = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='float32', device=device)
    sd.wait()
    audio = audio.flatten()
    filtered = apply_filters(audio, sample_rate)
    callback(filtered, sample_rate)


def speak_text(text, voice="default"):
    """Placeholder: Play a WAV file as TTS output (to be replaced with OpenVoice)."""
    print(f"[speak_text] Would speak: {text}")
    # For now, just play response.wav if it exists
    try:
        data, sr = sf.read('Om_E_Lm/data/audio/response.wav')
        sd.play(data, sr)
        sd.wait()
    except Exception as e:
        print(f"[speak_text] Playback error: {e}") 