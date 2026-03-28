import subprocess
import time
import sys

def main():
    print("=== Starting Uvicorn Server ===")
    server_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8000"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
    # Wait for the server to spin up
    time.sleep(3)

    try:
        print("\n=== Running Baseline Evaluation ===")
        # flush output immediately
        subprocess.check_call([sys.executable, "-u", "baseline.py"])
    except subprocess.CalledProcessError as e:
        print(f"\nBaseline execution failed with exit code {e.returncode}")
    finally:
        print("\n=== Shutting down server ===")
        server_proc.terminate()
        server_proc.wait()

if __name__ == "__main__":
    main()
