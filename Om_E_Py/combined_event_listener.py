"""
combined_event_listener.py

Runs both app_quit_listener.py and clean_event_listener_classified.py as subprocesses.
This allows you to monitor app quit/launch events and window events/classification with a single script.

- Each script runs in its own process (no threading issues with AppKit/NSRunLoop).
- Graceful shutdown on Ctrl+C (terminates both subprocesses).

Usage:
    python combined_event_listener.py [bundle_id_or_app_name]
    # Optional argument is passed to clean_event_listener_classified.py

"""
import subprocess
import sys
import signal
import time

if __name__ == "__main__":
    args = sys.argv[1:]

    # Start app_quit_listener.py as a subprocess
    p1 = subprocess.Popen([sys.executable, "app_quit_listener.py"])

    # Start clean_event_listener_classified.py as a subprocess, passing any CLI args
    p2_cmd = [sys.executable, "clean_event_listener_classified.py"] + args
    p2 = subprocess.Popen(p2_cmd)

    processes = [p1, p2]

    def shutdown(signum, frame):
        print("\n[Combined] Exiting... (signal received)")
        for p in processes:
            if p.poll() is None:
                p.terminate()
        # Give them a moment to exit gracefully
        time.sleep(1)
        for p in processes:
            if p.poll() is None:
                p.kill()
        print("[Combined] Both subprocesses stopped.")
        sys.exit(0)

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    try:
        # Wait for both subprocesses to finish
        while all(p.poll() is None for p in processes):
            time.sleep(0.5)
    except KeyboardInterrupt:
        shutdown(None, None)
    shutdown(None, None) 