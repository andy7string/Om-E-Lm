"""
Om_E_Lm/ome/utils/vad_manager.py

Handles real-time Voice Activity Detection (VAD) and smart pause detection for the OM‑E voice assistant.

Main Purpose:
- Detect speech and silence in real time from audio frames.
- Trigger transcript commit after a configurable smart pause (e.g., 5s of silence).

Key Features:
- Uses webrtcvad for lightweight, accurate VAD.
- Configurable aggressiveness and pause threshold.
- CLI Test: Can be run as a script to stream audio, print 'Speech'/'Silence', and detect smart pause.

How to Use (Command Line):
    python -m Om_E_Lm.ome.utils.vad_manager --test
    # Streams audio, prints 'Speech'/'Silence', and notifies on smart pause.

When to Use:
- As a foundational module for all speech/silence detection in the OM‑E pipeline.
- For tuning VAD and pause thresholds for your environment.
"""
import webrtcvad
import numpy as np
import time

VAD_AGGRESSIVENESS = 2  # 0 (least), 3 (most)
FRAME_DURATION_MS = 30  # 30ms frames
SAMPLE_RATE = 16000
FRAME_SIZE = int(SAMPLE_RATE * FRAME_DURATION_MS / 1000)

vad = webrtcvad.Vad(VAD_AGGRESSIVENESS)


def detect_speech(audio_chunk, sample_rate=SAMPLE_RATE):
    """
    Returns True if speech is detected in the given audio chunk.
    Args:
        audio_chunk (np.ndarray): 1D array of audio samples (float32 or int16)
        sample_rate (int): Sample rate in Hz
    Returns:
        bool: True if speech detected, False otherwise
    """
    # Convert to 16-bit PCM
    if audio_chunk.dtype != np.int16:
        audio_chunk = (audio_chunk * 32767).astype(np.int16)
    pcm_bytes = audio_chunk.tobytes()
    return vad.is_speech(pcm_bytes, sample_rate)


def smart_pause_detector(last_speech_time, threshold=5.0):
    """
    Returns True if the time since last speech exceeds the threshold (smart pause).
    Args:
        last_speech_time (float): Timestamp of last detected speech (time.time())
        threshold (float): Pause threshold in seconds
    Returns:
        bool: True if smart pause detected, False otherwise
    """
    return (time.time() - last_speech_time) > threshold

if __name__ == "__main__":
    import argparse
    import sounddevice as sd
    parser = argparse.ArgumentParser(description="Test real-time VAD and smart pause detection.")
    parser.add_argument('--test', action='store_true', help='Run a test: stream audio, print Speech/Silence, detect smart pause')
    parser.add_argument('--pause', type=float, default=5.0, help='Smart pause threshold in seconds (default: 5.0)')
    args = parser.parse_args()
    if args.test:
        print("Speak into the mic. Ctrl+C to stop.")
        last_speech_time = time.time()
        try:
            with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype='float32') as stream:
                while True:
                    audio_chunk, _ = stream.read(FRAME_SIZE)
                    audio_chunk = audio_chunk.flatten()
                    if detect_speech(audio_chunk, SAMPLE_RATE):
                        print("Speech", end='\r')
                        last_speech_time = time.time()
                    else:
                        print("Silence", end='\r')
                    if smart_pause_detector(last_speech_time, threshold=args.pause):
                        print(f"\nSmart pause detected! (>{args.pause}s of silence) Waiting for speech...")
                        while smart_pause_detector(last_speech_time, threshold=args.pause):
                            audio_chunk, _ = stream.read(FRAME_SIZE)
                            audio_chunk = audio_chunk.flatten()
                            if detect_speech(audio_chunk, SAMPLE_RATE):
                                print("Speech", end='\r')
                                last_speech_time = time.time()
                                break
                            else:
                                print("Silence", end='\r')
        except KeyboardInterrupt:
            print("\nTest stopped.")
    else:
        parser.print_help() 