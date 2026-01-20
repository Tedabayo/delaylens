import os
import time
from datetime import datetime

import hopsworks

LOCAL_FILE = "data/processed/training_data.csv"
REMOTE_DIR = "Resources/delaylens"  # folder in Hopsworks

MAX_RETRIES = 5
SLEEP_SEC = 8  # give the server time

def main():
    api_key = os.environ.get("HOPSWORKS_API_KEY")
    if not api_key:
        raise RuntimeError("HOPSWORKS_API_KEY is not set")

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            project = hopsworks.login(api_key_value=api_key)
            dataset_api = project.get_dataset_api()

            ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            remote_path = f"{REMOTE_DIR}/training_data_{ts}.csv"

            dataset_api.upload(LOCAL_FILE, remote_path, overwrite=False)
            print(f"Uploaded to Hopsworks: {remote_path}")
            return

        except Exception as e:
            print(f"[WARN] Upload attempt {attempt}/{MAX_RETRIES} failed: {type(e).__name__}: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(SLEEP_SEC)

    print("[ERROR] Upload failed after retries. Continuing without crashing the pipeline.")

if __name__ == "__main__":
    main()
