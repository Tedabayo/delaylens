import os
import joblib
import pandas as pd
import hopsworks

FV_NAME = "realtime_features_target_fv"
FV_VERSION = 1
TRAINING_DATASET_VERSION = 1

MODEL_PATH = "models/num_updates_model.joblib"
OUT_CSV = "data/processed/predictions.csv"


def main():
    # 1) Load trained model
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(
            f"Model not found at {MODEL_PATH}. Run training_pipeline.py first."
        )

    model = joblib.load(MODEL_PATH)
    print("[OK] Loaded trained model")

    # 2) Connect to Hopsworks
    api_key = os.environ.get("HOPSWORKS_API_KEY")
    if not api_key:
        raise RuntimeError("HOPSWORKS_API_KEY is not set")

    project = hopsworks.login(api_key_value=api_key)
    fs = project.get_feature_store()

    # 3) Load latest feature data (same way as training)
    fv = fs.get_feature_view(FV_NAME, version=FV_VERSION)

    X, y = fv.get_training_data(
        training_dataset_version=TRAINING_DATASET_VERSION
    )

    print(f"[OK] Loaded features for inference: {X.shape}")

    # 4) Make predictions
    preds = model.predict(X)

    # 5) Build output dataframe
    out = X.copy()
    out["prediction_num_updates"] = preds

    # Keep target if available (for inspection)
    if y is not None:
        out["actual_num_updates"] = y.iloc[:, 0].values

    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    out.to_csv(OUT_CSV, index=False)

    print(f"[OK] Predictions written to {OUT_CSV}")
    print(out[["prediction_num_updates"]].head(10))


if __name__ == "__main__":
    main()
