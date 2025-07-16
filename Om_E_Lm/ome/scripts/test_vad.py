import sounddevice as sd
import numpy as np
import time
import sys
import os
from Om_E_Lm.ome.utils.vad_manager import detect_speech, smart_pause_detector

SAMPLE_RATE = 16000
FRAME_DURATION_MS = 30
FRAME_SIZE = int(SAMPLE_RATE * FRAME_DURATION_MS / 1000)

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
            if smart_pause_detector(last_speech_time, threshold=5.0):
                print("\nSmart pause detected! Waiting for speech...")
                while smart_pause_detector(last_speech_time, threshold=5.0):
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