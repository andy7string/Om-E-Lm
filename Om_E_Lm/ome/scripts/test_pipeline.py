import sys
import os
from Om_E_Lm.ome.handlers.audio_handler import stream_audio
import soundfile as sf
import sounddevice as sd

AUDIO_OUT_PATH = 'Om_E_Lm/data/audio/temp_mic.wav'

# List available audio devices
print("\nAvailable audio devices:")
for idx, dev in enumerate(sd.query_devices()):
    print(f"{idx}: {dev['name']} (inputs: {dev['max_input_channels']}, outputs: {dev['max_output_channels']})")
print("\nSet the AUDIO_DEVICE index in audio_handler.py to a device with inputs >= 1.")


def save_and_play(audio, sample_rate):
    print(f"Saving filtered audio to {AUDIO_OUT_PATH}")
    sf.write(AUDIO_OUT_PATH, audio, sample_rate)
    print("Playing back filtered audio...")
    sd.play(audio, sample_rate)
    sd.wait()

if __name__ == "__main__":
    stream_audio(save_and_play, duration=3)
    print("Test complete.") 