import os
import time
import numpy as np
import pandas as pd
import hopsworks

PREDICTIONS_CSV = "data/processed/predictions.csv"

FG_NAME = "realtime_predictions_fg"
FG_VERSION = 1
FG_DESCRIPTION = "Batch predictions from DelayLens inference pipeline (num_updates_at_stop)."

PRIMARY_KEYS = ["feed_timestamp", "trip_id", "stop_id"]
EVENT_TIME_COL = "feed_timestamp"

MAX_RETRIES = 3
SLEEP_SEC = 8


def clean_string_columns(df: pd.DataFrame) -> pd.DataFrame:
    obj_cols = df.select_dtypes(include=["object"]).columns.tolist()
    for c in obj_cols:
        df[c] = df[c].replace({np.nan: None, "nan": None, "NaN": None, "": None})
        df[c] = df[c].astype(object)
    return df


def main():
    api_key = os.environ.get("HOPSWORKS_API_KEY")
    if not api_key:
        raise RuntimeError("HOPSWORKS_API_KEY is not set")

    if not os.path.exists(PREDICTIONS_CSV):
        raise FileNotFoundError(f"Missing {PREDICTIONS_CSV}. Run inference first.")

    df = pd.read_csv(PREDICTIONS_CSV, keep_default_na=True, na_values=["nan", "NaN", ""])

    required = PRIMARY_KEYS + [EVENT_TIME_COL, "prediction_num_updates"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"predictions.csv missing columns: {missing}\nCols: {list(df.columns)}")

    df = df.dropna(subset=PRIMARY_KEYS).copy()
    df["feed_timestamp"] = pd.to_numeric(df["feed_timestamp"], errors="raise").astype("int64")

    df = clean_string_columns(df)

    df["trip_id"] = df["trip_id"].astype(str)
    df["stop_id"] = df["stop_id"].astype(str)

    df["prediction_num_updates"] = pd.to_numeric(df["prediction_num_updates"], errors="coerce")

    if "actual_num_updates" in df.columns:
        df["actual_num_updates"] = pd.to_numeric(df["actual_num_updates"], errors="coerce")

    print(f"Loaded predictions: {df.shape[0]} rows, {df.shape[1]} cols")
    print(df.head(3))

    project = hopsworks.login(api_key_value=api_key)
    fs = project.get_feature_store()

    fg = fs.get_or_create_feature_group(
        name=FG_NAME,
        version=FG_VERSION,
        primary_key=PRIMARY_KEYS,
        event_time=EVENT_TIME_COL,
        description=FG_DESCRIPTION,
        online_enabled=False,
    )

    last_err = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            fg.insert(df, write_options={"wait_for_job": False})
            print(f"[OK] Insert request sent to Feature Group: {FG_NAME}_v{FG_VERSION}")
            return
        except Exception as e:
            last_err = e
            print(f"[WARN] Insert attempt {attempt}/{MAX_RETRIES} failed: {type(e).__name__}: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(SLEEP_SEC)

    raise RuntimeError(f"[ERROR] Failed to insert after retries. Last error: {last_err}")


if __name__ == "__main__":
    main()

