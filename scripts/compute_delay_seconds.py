import os
import numpy as np
import pandas as pd
from datetime import datetime, timezone

try:
    # Python 3.9+
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None


# Inputs
REALTIME_CSV = "data/raw/trip_updates.csv"
STOP_TIMES_TXT = "data/static/google_transit/stop_times.txt"

# Output (this becomes your supervised dataset with a target)
OUT_CSV = "data/processed/realtime_with_delay.csv"

# Transit agency timezone (RTD Denver). If you switch city later, change this.
AGENCY_TZ = "America/Denver"


def _hhmmss_to_seconds(hhmmss: str) -> int | None:
    """
    GTFS stop_times uses HH:MM:SS and can be > 24:00:00.
    Returns seconds since "service day midnight", possibly > 86400.
    """
    if not isinstance(hhmmss, str) or not hhmmss.strip():
        return None
    parts = hhmmss.strip().split(":")
    if len(parts) != 3:
        return None
    h, m, s = parts
    if not (h.isdigit() and m.isdigit() and s.isdigit()):
        return None
    return int(h) * 3600 + int(m) * 60 + int(s)


def _midnight_epoch_for_event(event_epoch: int) -> int:
    """
    Convert the event epoch -> agency-local date -> local midnight epoch.
    """
    if ZoneInfo is None:
        # fallback (won't be perfect, but prevents crashing)
        dt_utc = datetime.fromtimestamp(event_epoch, tz=timezone.utc)
        midnight_utc = datetime(dt_utc.year, dt_utc.month, dt_utc.day, tzinfo=timezone.utc)
        return int(midnight_utc.timestamp())

    tz = ZoneInfo(AGENCY_TZ)
    dt_local = datetime.fromtimestamp(event_epoch, tz=timezone.utc).astimezone(tz)
    midnight_local = datetime(dt_local.year, dt_local.month, dt_local.day, 0, 0, 0, tzinfo=tz)
    return int(midnight_local.timestamp())


def main():
    if not os.path.exists(REALTIME_CSV):
        raise FileNotFoundError(f"Missing {REALTIME_CSV}. Run fetch_realtime.py first.")

    if not os.path.exists(STOP_TIMES_TXT):
        raise FileNotFoundError(f"Missing {STOP_TIMES_TXT}.")

    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)

    # 1) Load realtime
    rt = pd.read_csv(REALTIME_CSV)

    required_rt = ["trip_id", "stop_sequence", "arrival_time", "departure_time", "feed_timestamp"]
    missing_rt = [c for c in required_rt if c not in rt.columns]
    if missing_rt:
        raise ValueError(f"Realtime CSV missing columns: {missing_rt}. Found: {list(rt.columns)}")

    # Clean/join keys
    rt["trip_id"] = rt["trip_id"].astype(str)
    rt["stop_sequence"] = pd.to_numeric(rt["stop_sequence"], errors="coerce").astype("Int64")

    # event_time_epoch: prefer departure_time; if missing use arrival_time; else fallback feed_timestamp
    rt["departure_time"] = pd.to_numeric(rt["departure_time"], errors="coerce")
    rt["arrival_time"] = pd.to_numeric(rt["arrival_time"], errors="coerce")
    rt["feed_timestamp"] = pd.to_numeric(rt["feed_timestamp"], errors="coerce")

    rt["event_time_epoch"] = rt["departure_time"]
    rt.loc[rt["event_time_epoch"].isna(), "event_time_epoch"] = rt["arrival_time"]
    rt.loc[rt["event_time_epoch"].isna(), "event_time_epoch"] = rt["feed_timestamp"]

    # Drop rows where we still have no event time
    rt = rt.dropna(subset=["event_time_epoch"]).copy()
    rt["event_time_epoch"] = rt["event_time_epoch"].astype("int64")

    # 2) Load stop_times
    st = pd.read_csv(STOP_TIMES_TXT)

    required_st = ["trip_id", "stop_sequence", "arrival_time", "departure_time"]
    missing_st = [c for c in required_st if c not in st.columns]
    if missing_st:
        raise ValueError(f"stop_times.txt missing columns: {missing_st}. Found: {list(st.columns)}")

    st["trip_id"] = st["trip_id"].astype(str)
    st["stop_sequence"] = pd.to_numeric(st["stop_sequence"], errors="coerce").astype("Int64")

    # Convert GTFS HH:MM:SS -> seconds since midnight (can be > 86400)
    st["sched_arr_sec"] = st["arrival_time"].map(_hhmmss_to_seconds)
    st["sched_dep_sec"] = st["departure_time"].map(_hhmmss_to_seconds)

    # Keep only join columns + schedule seconds
    st_small = st[["trip_id", "stop_sequence", "sched_arr_sec", "sched_dep_sec"]].copy()

    # 3) Join realtime rows to scheduled rows using (trip_id, stop_sequence)
    df = rt.merge(st_small, on=["trip_id", "stop_sequence"], how="left")

    # 4) Build scheduled epoch timestamps and compute delay
    # scheduled seconds can be > 86400 -> add extra days beyond midnight
    midnight_epochs = df["event_time_epoch"].map(_midnight_epoch_for_event).astype("int64")

    # pick scheduled departure if available else arrival
    sched_sec = df["sched_dep_sec"].copy()
    sched_sec = sched_sec.where(pd.notna(sched_sec), df["sched_arr_sec"])

    # compute scheduled_epoch = midnight + sched_sec (+ extra days already inside sched_sec)
    df["scheduled_epoch"] = midnight_epochs + pd.to_numeric(sched_sec, errors="coerce").fillna(np.nan)

    # delay_seconds = realtime_event_time - scheduled_epoch
    df["delay_seconds"] = df["event_time_epoch"] - df["scheduled_epoch"]

    # If we couldn't map to schedule, delay becomes NaN — that’s OK.
    # Optional: remove crazy outliers (e.g., > 6 hours) to avoid junk labels
    df.loc[df["delay_seconds"].abs() > 6 * 3600, "delay_seconds"] = np.nan

    # 5) Save
    keep_cols = [
        "feed_timestamp",
        "iso_time_utc",
        "route_id",
        "trip_id",
        "stop_id",
        "stop_sequence",
        "arrival_time",
        "departure_time",
        "delay_seconds",
    ]
    # keep whatever exists from realtime
    keep_cols = [c for c in keep_cols if c in df.columns]
    out = df[keep_cols].copy()

    out.to_csv(OUT_CSV, index=False)

    non_null = int(out["delay_seconds"].notna().sum()) if "delay_seconds" in out.columns else 0
    print(f"[OK] Wrote {len(out)} rows -> {OUT_CSV}")
    print(f"[INFO] delay_seconds non-null: {non_null} / {len(out)}")
    print(out[["trip_id", "stop_sequence", "delay_seconds"]].dropna().head(10))


if __name__ == "__main__":
    main()
