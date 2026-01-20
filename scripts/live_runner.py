import time
import subprocess
from datetime import datetime

# Run every N seconds
INTERVAL_SEC = 30

# The pipeline steps you already have
PIPELINE = [
    ["python", "scripts/fetch_realtime.py"],
    ["python", "scripts/join_realtime_with_stops.py"],
    ["python", "scripts/join_with_routes.py"],
    ["python", "scripts/upload_delaylens_data.py"],  # uploads training_data.csv now
]

def run_step(cmd):
    print(f"\n--- Running: {' '.join(cmd)} ---")
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"[WARN] Step failed but loop will continue: {e}")


def main():
    print("Starting DelayLens LIVE runner loop...")
    print(f"Interval: {INTERVAL_SEC}s")
    while True:
        start = datetime.now()
        print(f"\n==============================")
        print(f"Tick @ {start.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"==============================")

        for cmd in PIPELINE:
            run_step(cmd)

        
        with open("data/processed/last_updated.txt", "w") as f:
            f.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        

        end = datetime.now()
        dt = (end - start).total_seconds()
        sleep_for = max(0, INTERVAL_SEC - dt)
        print(f"\nCycle finished in {dt:.1f}s. Sleeping {sleep_for:.1f}s...")
        time.sleep(sleep_for)
if __name__ == "__main__":
    main()