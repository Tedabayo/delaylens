import os
import hopsworks

FG_NAME = "realtime_features_target_fg"
FG_VERSION = 1

FV_NAME = "realtime_features_target_fv"
FV_VERSION = 1

TARGET_COL = "num_updates_at_stop"


def main():
    api_key = os.environ.get("HOPSWORKS_API_KEY")
    if not api_key:
        raise RuntimeError("HOPSWORKS_API_KEY is not set")

    project = hopsworks.login(api_key_value=api_key)
    fs = project.get_feature_store()

    fg = fs.get_feature_group(FG_NAME, version=FG_VERSION)

    # Create query from feature group
    query = fg.select_all()

    fv = fs.get_or_create_feature_view(
        name=FV_NAME,
        version=FV_VERSION,
        query=query,
        labels=[TARGET_COL],
        description="Feature view for DelayLens delay prediction",
    )

    print(f"[OK] Feature View ready: {FV_NAME}_v{FV_VERSION}")

if __name__ == "__main__":
    main()
