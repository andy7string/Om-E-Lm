import os
import subprocess
import time
import requests

OLLAMA_ENV = {
    "OLLAMA_FLASH_ATTENTION": "1",
    "OLLAMA_KV_CACHE_QUANT": "Q4",
    "OLLAMA_MAX_CONTEXT": "32768",
    "OLLAMA_KEEP_ALIVE": "60m",
    "OLLAMA_MAX_LOADED_MODELS": "1",
    "OLLAMA_NUM_PARALLEL": "4",  # Adjust to your number of performance cores
    # Assign up to 80% of RAM for GPU tasks (Apple Silicon)
    "OLLAMA_GPU_PERCENT": "80"
    # "OLLAMA_GPU_OVERHEAD": "0.1"  # Removed, not supported in your Ollama version
}

OLLAMA_SERVER_URL = "http://127.0.0.1:11434"
MODEL_NAME = "deepseek-r1:1.5b"


def is_ollama_running():
    try:
        r = requests.get(f"{OLLAMA_SERVER_URL}/api/tags", timeout=2)
        return r.status_code == 200
    except Exception:
        return False

def start_ollama_server():
    print("🚀 Starting Ollama with max performance settings...")
    env = os.environ.copy()
    env.update(OLLAMA_ENV)
    # Start ollama serve in the background
    subprocess.Popen(["ollama", "serve"], env=env)
    # Wait for server to be ready
    for _ in range(20):
        if is_ollama_running():
            print("✅ Ollama server is running!")
            return True
        time.sleep(1)
    print("❌ Ollama server did not start in time.")
    return False

def preload_model(model_name=MODEL_NAME):
    print(f"🔥 Preloading {model_name} into RAM...")
    url = f"{OLLAMA_SERVER_URL}/api/generate"
    payload = {"model": model_name, "prompt": "Hello", "stream": False}
    try:
        response = requests.post(url, json=payload, timeout=30)
        if response.status_code == 200:
            print(f"✅ {model_name} is now loaded and warm.")
        else:
            print(f"❌ Failed to preload: {response.text}")
    except Exception as e:
        print(f"❌ Exception during preload: {e}")

def main():
    # Kill any running Ollama server (optional, comment out if you want to keep running sessions)
    # subprocess.run(["pkill", "ollama"])
    if not is_ollama_running():
        started = start_ollama_server()
        if not started:
            return
    else:
        print("ℹ️  Ollama server already running.")
    preload_model()

if __name__ == "__main__":
    main() 