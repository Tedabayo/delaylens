import os
import pandas as pd
import gradio as gr
import hopsworks

FG_NAME = "realtime_predictions_fg"
FG_VERSION = 1

DEFAULT_LIMIT = 50


def read_predictions_from_hopsworks() -> pd.DataFrame:
    api_key = os.environ.get("HOPSWORKS_API_KEY")
    if not api_key:
        raise RuntimeError("HOPSWORKS_API_KEY is not set")

    project = hopsworks.login(api_key_value=api_key)
    fs = project.get_feature_store()

    fg = fs.get_feature_group(FG_NAME, version=FG_VERSION)
    df = fg.read()

    if "feed_timestamp" in df.columns:
        df = df.sort_values("feed_timestamp", ascending=False)

    return df


def build_choices(df: pd.DataFrame, col: str):
    if col not in df.columns:
        return ["ALL"]
    vals = sorted(df[col].dropna().astype(str).unique().tolist())
    return ["ALL"] + vals


def fetch_table(route_id: str, stop_id: str, limit: int):
    df = read_predictions_from_hopsworks()

    if route_id != "ALL" and "route_id" in df.columns:
        df = df[df["route_id"].astype(str) == str(route_id)]

    if stop_id != "ALL" and "stop_id" in df.columns:
        df = df[df["stop_id"].astype(str) == str(stop_id)]

    if "feed_timestamp" in df.columns and len(df) > 0:
        latest_ts = df["feed_timestamp"].max()
        last_updated = f"Last updated (feed_timestamp): {int(latest_ts)}"
    else:
        last_updated = "Last updated: unknown"

    show_cols = []
    for c in [
        "iso_time_utc",
        "feed_timestamp",
        "route_id",
        "stop_id",
        "trip_id",
        "stop_sequence",
        "prediction_num_updates",
        "actual_num_updates",
    ]:
        if c in df.columns:
            show_cols.append(c)

    df_out = df[show_cols].head(int(limit)).copy() if show_cols else df.head(int(limit)).copy()
    return last_updated, df_out


def main():
    df0 = read_predictions_from_hopsworks()
    route_choices = build_choices(df0, "route_id")
    stop_choices = build_choices(df0, "stop_id")

    with gr.Blocks(title="DelayLens – Predictions") as demo:
        gr.Markdown("# DelayLens – Live Predictions (Hopsworks Feature Store)")
        gr.Markdown(f"Reading from Feature Group: **{FG_NAME}_v{FG_VERSION}**")

        with gr.Row():
            route_dd = gr.Dropdown(choices=route_choices, value="ALL", label="route_id")
            stop_dd = gr.Dropdown(choices=stop_choices, value="ALL", label="stop_id")
            limit = gr.Slider(10, 200, value=DEFAULT_LIMIT, step=10, label="Rows to show")

        refresh_btn = gr.Button("Refresh")

        last_updated = gr.Textbox(label="Status", interactive=False)
        table = gr.Dataframe(label="Predictions", interactive=False)

        refresh_btn.click(fetch_table, inputs=[route_dd, stop_dd, limit], outputs=[last_updated, table])

        timer = gr.Timer(20)
        timer.tick(fetch_table, inputs=[route_dd, stop_dd, limit], outputs=[last_updated, table])

        demo.load(fetch_table, inputs=[route_dd, stop_dd, limit], outputs=[last_updated, table])

    demo.launch(server_name="0.0.0.0", server_port=7860)


if __name__ == "__main__":
    main()
