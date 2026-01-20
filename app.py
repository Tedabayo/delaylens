import os
import pandas as pd
import streamlit as st
from datetime import datetime
import hopsworks

FG_NAME = "realtime_predictions_fg"
FG_VERSION = 1
MAX_ROWS = 500

st.set_page_config(page_title="DelayLens", layout="wide")
st.title("DelayLens – Real-Time Transit Monitor (with Predictions)")

@st.cache_data(ttl=15)
def load_preds_from_hopsworks():
    api_key = os.environ.get("HOPSWORKS_API_KEY")
    if not api_key:
        raise RuntimeError("HOPSWORKS_API_KEY is not set.")

    project = hopsworks.login(api_key_value=api_key)
    fs = project.get_feature_store()
    fg = fs.get_feature_group(FG_NAME, version=FG_VERSION)

    df = fg.read()
    if "feed_timestamp" in df.columns:
        df = df.sort_values("feed_timestamp", ascending=False)

    return df.head(MAX_ROWS)

st.caption(f"Last refresh: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

df = load_preds_from_hopsworks()

st.subheader("Latest predictions (sample)")
show_cols = [
    "iso_time_utc",
    "route_id",
    "trip_id",
    "stop_id",
    "prediction_num_updates",
]

if "actual_num_updates" in df.columns:
    show_cols.append("actual_num_updates")

show_cols = [c for c in show_cols if c in df.columns]
st.dataframe(df[show_cols], use_container_width=True)

st.markdown(
    """
**What you are seeing**
- Predictions come from **Hopsworks Feature Group**
- Feature Group: `realtime_predictions_fg`
"""
)

