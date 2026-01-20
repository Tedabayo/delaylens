import csv
import os
from datetime import datetime, timezone

import requests
from google.transit import gtfs_realtime_pb2

GTFS_RT_TRIP_UPDATES_URL = "https://open-data.rtd-denver.com/files/gtfs-rt/rtd/TripUpdate.pb"
OUT_CSV = "data/raw/trip_updates.csv"


def get_first_stop_times(trip_update):
    """
    Return (stop_id, stop_sequence, arrival_time, departure_time) from the first stop_time_update.
    arrival_time / departure_time are epoch seconds (int) or None.
    """
    if not trip_update.stop_time_update:
        return None, None, None, None

    stu0 = trip_update.stop_time_update[0]

    stop_id = stu0.stop_id if stu0.stop_id != "" else None
    stop_seq = int(stu0.stop_sequence) if stu0.stop_sequence is not None else None

    arr_time = None
    dep_time = None

    if stu0.HasField("arrival") and stu0.arrival.HasField("time"):
        arr_time = int(stu0.arrival.time)

    if stu0.HasField("departure") and stu0.departure.HasField("time"):
        dep_time = int(stu0.departure.time)

    return stop_id, stop_seq, arr_time, dep_time


def main() -> None:
    # 1) Fetch feed
    feed = gtfs_realtime_pb2.FeedMessage()
    resp = requests.get(GTFS_RT_TRIP_UPDATES_URL, timeout=30)
    resp.raise_for_status()
    feed.ParseFromString(resp.content)

    feed_ts = int(feed.header.timestamp)
    iso_time = datetime.fromtimestamp(feed_ts, tz=timezone.utc).isoformat()

    # --- Skip if timestamp unchanged (prevents duplicates) ---
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
    # --- End skip logic ---

    # 2) Ensure output folder exists
    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)

    # 3) Append rows
    file_exists = os.path.exists(OUT_CSV)
    with open(OUT_CSV, "a", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "feed_timestamp",
                "iso_time_utc",
                "route_id",
                "trip_id",
                "stop_id",
                "stop_sequence",
                "arrival_time",
                "departure_time",
            ],
        )

        if not file_exists:
            writer.writeheader()

        written = 0
        skipped_no_time = 0

        for entity in feed.entity:
            if not entity.HasField("trip_update"):
                continue

            tu = entity.trip_update
            trip = tu.trip

            stop_id, stop_seq, arr_time, dep_time = get_first_stop_times(tu)

            # Keep only rows where at least one of arrival/departure time exists
            if arr_time is None and dep_time is None:
                skipped_no_time += 1
                continue

            writer.writerow(
                {
                    "feed_timestamp": feed_ts,
                    "iso_time_utc": iso_time,
                    "route_id": trip.route_id,
                    "trip_id": trip.trip_id,
                    "stop_id": stop_id,
                    "stop_sequence": stop_seq,
                    "arrival_time": arr_time,
                    "departure_time": dep_time,
                }
            )
            written += 1

    print(f"Feed timestamp: {feed_ts} ({iso_time})")
    print(f"Wrote {written} rows to {OUT_CSV} (skipped {skipped_no_time} rows with no time fields)")


if __name__ == "__main__":
    main()
