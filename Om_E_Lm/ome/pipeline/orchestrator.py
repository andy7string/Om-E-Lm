"""
Om_E_Lm/ome/pipeline/orchestrator.py

Pipeline orchestrator for the OM‑E voice assistant.

Main Purpose:
- Connects audio capture, filtering, VAD, and STT into a single, maintainable pipeline.
- Provides a foundation for adding RAG, LLM, and TTS modules.

Key Features:
- Continuously captures and filters audio frames from the microphone.
- Uses VAD to detect speech and smart pauses.
- Streams speech frames to Vosk STT for real-time transcription.
- Commits and prints the transcript after a smart pause.
- CLI entry point for live testing and demonstration.

How to Use (Command Line):
    python -m Om_E_Lm.ome.pipeline.orchestrator --run
    # Runs the full audio → VAD → STT pipeline, prints transcripts on smart pause.

When to Use:
- As the main entry point for the OM‑E speech-to-speech pipeline.
- For validating and extending the end-to-end flow.
"""
import time
import numpy as np
from Om_E_Lm.ome.handlers.audio_handler import apply_filters, AUDIO_SAMPLE_RATE, AUDIO_DEVICE
from Om_E_Lm.ome.utils.vad_manager import detect_speech, smart_pause_detector
from Om_E_Lm.ome.utils.stt_manager import STTManager
import sounddevice as sd

SAMPLE_RATE = AUDIO_SAMPLE_RATE
FRAME_DURATION_MS = 30
FRAME_SIZE = int(SAMPLE_RATE * FRAME_DURATION_MS / 1000)
SMART_PAUSE_THRESHOLD = 5.0

class PipelineOrchestrator:
    """
    Orchestrates audio capture, filtering, VAD, and STT in a streaming loop.
    """
    def __init__(self, sample_rate=SAMPLE_RATE, device=AUDIO_DEVICE, pause_threshold=SMART_PAUSE_THRESHOLD):
        self.sample_rate = sample_rate
        self.device = device
        self.pause_threshold = pause_threshold
        self.stt = STTManager()
        self.last_speech_time = time.time()
        self.transcript = ""

    def run(self):
        """
        Runs the main pipeline loop: audio → filter → VAD → STT → commit on smart pause.
        """
        print("[Orchestrator] Starting pipeline. Speak into the mic. Ctrl+C to stop.")
        with sd.InputStream(samplerate=self.sample_rate, channels=1, dtype='float32', device=self.device) as stream:
            buffer = []
            def on_partial(res):
                import json
                partial = json.loads(res).get('partial', '')
                if partial:
                    print(f"Partial: {partial}", end='\r')
            def on_final(res):
                import json
                text = json.loads(res).get('text', '')
                if text:
                    print(f"\n[Transcript] {text}")
                    self.transcript = text
            while True:
                audio_chunk, _ = stream.read(FRAME_SIZE)
                audio_chunk = audio_chunk.flatten()
                filtered = apply_filters(audio_chunk, self.sample_rate)
                if detect_speech(filtered, self.sample_rate):
                    buffer.append(filtered)
                    self.last_speech_time = time.time()
                else:
                    buffer.append(np.zeros_like(filtered))
                if smart_pause_detector(self.last_speech_time, threshold=self.pause_threshold):
                    if buffer:
                        print(f"\n[Orchestrator] Smart pause detected. Committing transcript...")
                        def frame_gen():
                            for frame in buffer:
                                yield frame
                        self.stt.start_vosk_stream(frame_gen(), on_partial, on_final)
                        buffer = []
                    print("[Orchestrator] Waiting for speech...")
                    # Wait for speech to resume
                    while smart_pause_detector(self.last_speech_time, threshold=self.pause_threshold):
                        audio_chunk, _ = stream.read(FRAME_SIZE)
                        audio_chunk = audio_chunk.flatten()
                        filtered = apply_filters(audio_chunk, self.sample_rate)
                        if detect_speech(filtered, self.sample_rate):
                            self.last_speech_time = time.time()
                            buffer.append(filtered)
                            break
                        else:
                            buffer.append(np.zeros_like(filtered))

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run the OM‑E audio → VAD → STT pipeline.")
    parser.add_argument('--run', action='store_true', help='Run the pipeline orchestrator')
    args = parser.parse_args()
    if args.run:
        orchestrator = PipelineOrchestrator()
        try:
            orchestrator.run()
        except KeyboardInterrupt:
            print("\n[Orchestrator] Stopped.")
    else:
        parser.print_help() 