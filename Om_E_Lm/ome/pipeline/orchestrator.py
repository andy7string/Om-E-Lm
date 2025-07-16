"""
Om_E_Lm/ome/pipeline/orchestrator.py

Pipeline orchestrator for the OM‑E voice assistant (refactored: STTManager-centric).

Main Purpose:
- Starts STTManager, which handles mic input, VAD, and streaming STT internally.
- Receives partial/final transcripts via callbacks.
- (Stub) Passes final transcript to next pipeline stage (RAG/LLM/TTS).

Key Features:
- Minimal, maintainable pipeline code.
- CLI entry point for live testing and demonstration.

How to Use (Command Line):
    python -m Om_E_Lm.ome.pipeline.orchestrator --run
    # Runs the full speech pipeline, prints transcripts on-the-fly.

When to Use:
- As the main entry point for the OM‑E speech-to-speech pipeline.
- For validating and extending the end-to-end flow.
"""
from Om_E_Lm.ome.utils.stt_manager import STTManager
from Om_E_Lm.ome.handlers.audio_handler import AUDIO_DEVICE
import argparse
from env import OME_SMART_PAUSE_THRESHOLD, OME_VAULT_VOICE_PATH
import json
import os
import time

class TranscriptCollector:
    def __init__(self):
        self.buffer = []
        self.last_speech_time = time.time()

    def on_partial(self, text):
        if text:
            self.last_speech_time = time.time()

    def on_final(self, text):
        if text:
            self.buffer.append(text)
            self.last_speech_time = time.time()

    def check_silence(self):
        if (time.time() - self.last_speech_time) > OME_SMART_PAUSE_THRESHOLD and self.buffer:
            full_text = " ".join(self.buffer)
            entry = {
                "id": f"user_query_{time.strftime('%Y%m%d_%H%M%S')}",
                "type": "user_query",
                "text": full_text,
                "timestamp": time.strftime('%Y-%m-%dT%H:%M:%S')
            }
            log_voice_entry(entry)
            print(f"[DEBUG] Committed transcript: {entry}")
            self.buffer = []

def log_voice_entry(entry):
    # Ensure the directory exists
    os.makedirs(os.path.dirname(OME_VAULT_VOICE_PATH), exist_ok=True)
    with open(OME_VAULT_VOICE_PATH, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')

class PipelineOrchestrator:
    """
    Orchestrates the OM‑E pipeline by starting STTManager and handling transcript events.
    """
    def __init__(self, device=AUDIO_DEVICE):
        self.device = device
        self.stt = STTManager()
        self.last_transcript = ""
        self.collector = TranscriptCollector()

    def on_partial(self, res):
        import json
        partial = json.loads(res).get('partial', '')
        if partial:
            print(f"Partial: {partial}", end='\r')
        self.collector.on_partial(partial)
        self.collector.check_silence()

    def on_final(self, res):
        import json
        text = json.loads(res).get('text', '')
        if text:
            print(f"\n[Transcript] {text}")
            self.last_transcript = text
        self.collector.on_final(text)
        self.collector.check_silence()

    def run(self):
        print("[Orchestrator] Starting OM‑E pipeline. Speak into the mic. Ctrl+C to stop.")
        try:
            # STTManager handles mic, VAD, and streaming STT internally
            self.stt.run_with_mic(
                callback_on_partial=self.on_partial,
                callback_on_final=self.on_final
            )
        except KeyboardInterrupt:
            print("\n[Orchestrator] Stopped.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the OM‑E speech pipeline (STTManager-centric).")
    parser.add_argument('--run', action='store_true', help='Run the pipeline orchestrator')
    args = parser.parse_args()
    if args.run:
        orchestrator = PipelineOrchestrator()
        orchestrator.run()
    else:
        parser.print_help() 