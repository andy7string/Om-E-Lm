import webrtcvad
import numpy as np
import time

# VAD aggressiveness: 0 (least), 3 (most)
vad = webrtcvad.Vad(2)

FRAME_DURATION_MS = 30  # 30ms frames
SAMPLE_RATE = 16000
FRAME_SIZE = int(SAMPLE_RATE * FRAME_DURATION_MS / 1000)


def detect_speech(audio_chunk, sample_rate=SAMPLE_RATE):
    """
    Returns True if speech is detected in the given audio chunk.
    audio_chunk: np.ndarray (mono, float32 or int16)
    """
    # Convert to 16-bit PCM
    if audio_chunk.dtype != np.int16:
        audio_chunk = (audio_chunk * 32767).astype(np.int16)
    pcm_bytes = audio_chunk.tobytes()
    return vad.is_speech(pcm_bytes, sample_rate)


def smart_pause_detector(last_speech_time, threshold=5.0):
    """
    Returns True if the time since last speech exceeds the threshold (smart pause).
    """
    return (time.time() - last_speech_time) > threshold 