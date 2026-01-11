import time
import subprocess
from datetime import datetime

INTERVAL_SECONDS = 60

def main():
    print("Starting collector. Press Ctrl+C to stop.")
    while True:
        start = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n[{start}] Fetching GTFS-RT trip updates...")
        subprocess.run(["python", "scripts/fetch_realtime.py"], check=False)

        print(f"Sleeping {INTERVAL_SECONDS} seconds...")
        time.sleep(INTERVAL_SECONDS)

if __name__ == "__main__":
    main()
