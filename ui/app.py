import pandas as pd
import streamlit as st

DATA_PATH = "data/processed/realtime_enriched_with_routes.csv"

st.set_page_config(page_title="DelayLens", layout="wide")

st.title("🚍 DelayLens – Real-Time Transit Monitor")

@st.cache_data
def load_data():
    return pd.read_csv(DATA_PATH)

df = load_data()

st.subheader("Latest realtime data (sample)")
st.write(df.head(20))

st.markdown(
    """
**What you are seeing**
- This table is built from **live GTFS-Realtime data**
- Data is joined with **static GTFS schedules**
- The pipeline updates automatically as new data arrives
"""
)
