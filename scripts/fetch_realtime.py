import csv
import os
from datetime import datetime, timezone

import requests
from google.transit import gtfs_realtime_pb2

GTFS_RT_TRIP_UPDATES_URL = "https://open-data.rtd-denver.com/files/gtfs-rt/rtd/TripUpdate.pb"
OUT_CSV = "data/raw/trip_updates.csv"

def extract_delay_seconds(trip_update) -> int | None:
    if not trip_update.stop_time_update:
        return None
    stu0 = trip_update.stop_time_update[0]

    if stu0.HasField("arrival") and stu0.arrival.HasField("delay"):
        return stu0.arrival.delay
    if stu0.HasField("departure") and stu0.departure.HasField("delay"):
        return stu0.departure.delay
    return None
def main() -> None:
    # 1) Fetch feed
    feed = gtfs_realtime_pb2.FeedMessage()
    resp = requests.get(GTFS_RT_TRIP_UPDATES_URL, timeout=30)
    resp.raise_for_status()
    feed.ParseFromString(resp.content)

    feed_ts = int(feed.header.timestamp)
    iso_time = datetime.fromtimestamp(feed_ts, tz=timezone.utc).isoformat()

    # --- NEW: skip if timestamp unchanged ---
    last_ts_path = "data/raw/last_timestamp.txt"
    os.makedirs(os.path.dirname(last_ts_path), exist_ok=True)

    if os.path.exists(last_ts_path):
        with open(last_ts_path, "r") as f:
            last_ts = f.read().strip()
        if last_ts.isdigit() and int(last_ts) == feed_ts:
            print(f"Feed timestamp unchanged ({feed_ts}). Skipping write.")
            return

    with open(last_ts_path, "w") as f:
        f.write(str(feed_ts))
    # --- END NEW ---

    # 2) Ensure output folder exists
    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)

    # 3) Append rows
    file_exists = os.path.exists(OUT_CSV)
    with open(OUT_CSV, "a", newline="") as f:
        writer = csv.DictWriter(
    f,
    fieldnames=["feed_timestamp", "iso_time_utc", "route_id", "trip_id", "stop_id", "delay_seconds"],
)

        if not file_exists:
            writer.writeheader()

        written = 0
        for entity in feed.entity:
            if not entity.HasField("trip_update"):
                continue

            tu = entity.trip_update
            trip = tu.trip

            stop_id = None
            if tu.stop_time_update:
                stop_id = tu.stop_time_update[0].stop_id

            writer.writerow(
                {
                    "feed_timestamp": feed_ts,
                    "iso_time_utc": iso_time,
                    "route_id": trip.route_id,
                    "trip_id": trip.trip_id,
                    "stop_id": stop_id,
                    "delay_seconds": extract_delay_seconds(tu),
                }
            )
            written += 1

    print(f"Feed timestamp: {feed_ts} ({iso_time})")
    print(f"Wrote {written} rows to {OUT_CSV}")

if __name__ == "__main__":
    main()
