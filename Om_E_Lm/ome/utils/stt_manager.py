"""
Om_E_Lm/ome/utils/stt_manager.py

Handles streaming Speech-to-Text (STT) using Vosk for the OM‑E voice assistant.

Main Purpose:
- Initialize and manage a Vosk recognizer for offline, streaming STT.
- Accept audio frames, provide partial and final transcripts in real time.
- (Stub) Hotword detection (e.g., "Om‑E").

Key Features:
- Uses Vosk for fast, accurate, fully offline speech recognition.
- Streaming: Accepts audio frames and yields partial/final results.
- CLI Test: Can be run as a script to stream audio, use VAD to gate input, and print transcripts.

How to Use (Command Line):
    python -m Om_E_Lm.ome.utils.stt_manager --test
    # Streams audio, prints partial/final transcripts, and detects hotword.

When to Use:
- As a foundational module for all speech-to-text in the OM‑E pipeline.
- For validating model setup and tuning STT performance.
"""
import os
import queue
import threading
from vosk import Model, KaldiRecognizer
import numpy as np

# Corrected path to go up two directories to the Om_E_Lm project folder, then into its data directory.
MODEL_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data/vosk_model/vosk-model-small-en-us-0.15'))
SAMPLE_RATE = 16000

class STTManager:
    """
    Streaming Speech-to-Text manager using Vosk.
    Args:
        model_path (str): Path to Vosk model directory
        sample_rate (int): Audio sample rate in Hz
    """
    def __init__(self, model_path=MODEL_PATH, sample_rate=SAMPLE_RATE):
        print(f"Attempting to load Vosk model from: {model_path}") # Debug print
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Vosk model path does not exist: {model_path}")
        
        self.model = Model(model_path)
        self.sample_rate = sample_rate
        self.rec = KaldiRecognizer(self.model, self.sample_rate)
        self.rec.SetWords(True)
        self.audio_queue = queue.Queue()
        self.running = False
        self.transcript = ""

    def start_vosk_stream(self, audio_frame_generator, callback_on_partial, callback_on_final):
        """
        Streams audio frames to Vosk recognizer and calls callbacks with partial/final results.
        Args:
            audio_frame_generator (generator): Yields np.ndarray audio frames (mono, float32)
            callback_on_partial (function): Called with partial transcript (JSON string)
            callback_on_final (function): Called with final transcript (JSON string)
        """
        self.running = True
        self.transcript = ""
        for frame in audio_frame_generator:
            if not self.running:
                break
            # Convert to 16-bit PCM
            if frame.dtype != np.int16:
                frame = (frame * 32767).astype(np.int16)
            if self.rec.AcceptWaveform(frame.tobytes()):
                res = self.rec.Result()
                callback_on_final(res)
            else:
                res = self.rec.PartialResult()
                callback_on_partial(res)

    def stop(self):
        """Stops the streaming recognizer."""
        self.running = False

    def commit_transcript(self, full_text):
        """Stores the final transcript (can be extended to log or save)."""
        self.transcript = full_text
        # Could write to file, log, etc.

    def detect_hotword(self, text, hotword="om-e"):
        """Returns True if the hotword is detected in the text (case-insensitive)."""
        # Simple stub: check if hotword in text (case-insensitive)
        return hotword.lower() in text.lower() 

    def run_with_mic(self, callback_on_partial, callback_on_final, hotword=None):
        """
        Starts the full mic → VAD → STT pipeline using internal logic.
        Args:
            callback_on_partial (function): Called with partial transcript (JSON string)
            callback_on_final (function): Called with final transcript (JSON string)
            hotword (str, optional): Hotword to detect (for future use)
        """
        import sounddevice as sd
        from Om_E_Lm.ome.utils.vad_manager import detect_speech
        from Om_E_Lm.ome.handlers.audio_handler import AUDIO_DEVICE
        SAMPLE_RATE = self.sample_rate
        FRAME_DURATION_MS = 30
        FRAME_SIZE = int(SAMPLE_RATE * FRAME_DURATION_MS / 1000)
        def audio_frame_generator():
            with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype='float32', device=AUDIO_DEVICE) as stream:
                while True:
                    audio_chunk, _ = stream.read(FRAME_SIZE)
                    audio_chunk = audio_chunk.flatten()
                    if detect_speech(audio_chunk, SAMPLE_RATE):
                        yield audio_chunk
                    else:
                        yield np.zeros_like(audio_chunk)
        self.start_vosk_stream(audio_frame_generator(), callback_on_partial, callback_on_final)

if __name__ == "__main__":
    import argparse
    import sounddevice as sd
    from Om_E_Lm.ome.utils.vad_manager import detect_speech
    from Om_E_Lm.ome.handlers.audio_handler import AUDIO_DEVICE
    import time
    parser = argparse.ArgumentParser(description="Test streaming Vosk STT with VAD gating.")
    parser.add_argument('--test', action='store_true', help='Run a test: stream audio, print transcripts, detect hotword')
    parser.add_argument('--hotword', type=str, default='om-e', help='Hotword to detect (default: om-e)')
    args = parser.parse_args()
    if args.test:
        print(f"Speak into the mic (device {AUDIO_DEVICE}). Ctrl+C to stop.")
        stt = STTManager()
        SAMPLE_RATE = 16000
        FRAME_DURATION_MS = 30
        FRAME_SIZE = int(SAMPLE_RATE * FRAME_DURATION_MS / 1000)
        def audio_frame_generator():
            with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype='float32', device=AUDIO_DEVICE) as stream:
                while True:
                    audio_chunk, _ = stream.read(FRAME_SIZE)
                    audio_chunk = audio_chunk.flatten()
                    if detect_speech(audio_chunk, SAMPLE_RATE):
                        yield audio_chunk
                    else:
                        yield np.zeros_like(audio_chunk)
        def on_partial(res):
            import json
            partial = json.loads(res).get('partial', '')
            if partial:
                print(f"Partial: {partial}", end='\r')
        def on_final(res):
            import json
            text = json.loads(res).get('text', '')
            if text:
                print(f"\nFinal: {text}")
                if stt.detect_hotword(text, hotword=args.hotword):
                    print(f"Hotword '{args.hotword}' detected!")
        try:
            stt.start_vosk_stream(audio_frame_generator(), on_partial, on_final)
        except KeyboardInterrupt:
            print("\nTest stopped.")
    else:
        parser.print_help() 