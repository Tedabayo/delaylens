import os
import joblib
import pandas as pd
import hopsworks

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.ensemble import RandomForestRegressor


FV_NAME = "realtime_features_target_fv"
FV_VERSION = 1
TRAINING_DATASET_VERSION = 1

TARGET_COL = "num_updates_at_stop"

MODEL_DIR = "models"
MODEL_FILE = os.path.join(MODEL_DIR, "num_updates_model.joblib")


def main():
    api_key = os.environ.get("HOPSWORKS_API_KEY")
    if not api_key:
        raise RuntimeError("HOPSWORKS_API_KEY is not set")

    # 1) Login + load feature view
    project = hopsworks.login(api_key_value=api_key)
    fs = project.get_feature_store()
    fv = fs.get_feature_view(FV_NAME, version=FV_VERSION)

    # 2) Read training data (THIS is the correct method for your setup)
    X, y = fv.get_training_data(training_dataset_version=TRAINING_DATASET_VERSION)

    print("X shape:", X.shape)
    print("y shape:", y.shape)
    print("Target column:", list(y.columns))

    # y is a DataFrame with one column -> convert to 1D array
    if TARGET_COL not in y.columns:
        raise ValueError(f"Expected target '{TARGET_COL}' in y. Got: {list(y.columns)}")

    y_1d = y[TARGET_COL].astype(float).values

    # 3) Train/test split locally
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_1d, test_size=0.2, random_state=42
    )

    print("X_train:", X_train.shape, "X_test:", X_test.shape)
    print("y_train:", y_train.shape, "y_test:", y_test.shape)

    # 4) Simple preprocessing:
    # - numeric columns: impute median
    # - categorical columns: impute most_frequent + one-hot
    categorical_cols = ["route_id", "trip_id", "stop_id", "iso_time_utc"]
    numeric_cols = [c for c in X.columns if c not in categorical_cols]

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", Pipeline(steps=[
                ("imputer", SimpleImputer(strategy="median")),
            ]), numeric_cols),
            ("cat", Pipeline(steps=[
                ("imputer", SimpleImputer(strategy="most_frequent")),
                ("onehot", OneHotEncoder(handle_unknown="ignore")),
            ]), categorical_cols),
        ],
        remainder="drop"
    )

    model = RandomForestRegressor(
        n_estimators=200,
        random_state=42,
        n_jobs=-1
    )

    clf = Pipeline(steps=[
        ("preprocess", preprocessor),
        ("model", model),
    ])

    # 5) Train
    print("Training model...")
    clf.fit(X_train, y_train)

    # 6) Evaluate
    preds = clf.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    rmse = mean_squared_error(y_test, preds) ** 0.5

    print(f"[OK] MAE:  {mae:.4f}")
    print(f"[OK] RMSE: {rmse:.4f}")

    # 7) Save model locally
    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(clf, MODEL_FILE)
    print(f"[OK] Saved model -> {MODEL_FILE}")


if __name__ == "__main__":
    main()
