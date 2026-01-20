# DelayLens – Real-Time Transit ML (GTFS-Realtime)

DelayLens is a scalable machine learning project that ingests **GTFS-Realtime Trip Updates**, engineers features from streaming data, stores them in the **Hopsworks Feature Store**, trains a model using a **Feature View**, runs batch inference, and visualizes predictions in a **Streamlit UI**.

This project follows the architecture and requirements of **ID2223 Lab 1 & Lab 2**.

---

## 1. Dynamic Data Source

- **Source:** GTFS-Realtime Trip Updates feed  
- **Type:** Streaming / continuously updated data  
- **Ingestion:**  
  The realtime feed is fetched repeatedly and parsed into tabular form.

Each feed snapshot is timestamped using:
- `feed_timestamp` (event time)
- `iso_time_utc`

A guard is used to **skip ingestion when the feed timestamp is unchanged**, ensuring true streaming behavior.

---

## 2. Prediction Target

We explicitly define the prediction target as:

### **num_updates_at_stop**

> The number of GTFS-Realtime updates observed for a given  
> **(route_id, stop_id)** within a short time window.

This target:
- Is derived directly from the realtime stream
- Does not rely on static schedules
- Acts as a proxy for transit instability / congestion

---

## 3. Feature Engineering

Realtime GTFS data is transformed into features including:

- `route_id`
- `trip_id`
- `stop_id`
- `stop_sequence`
- `arrival_time`
- `departure_time`
- `feed_timestamp`
- `iso_time_utc`

The target column `num_updates_at_stop` is computed from the streaming data.

---

## 4. Feature Store (Hopsworks)

Features are stored in **Hopsworks Feature Store**.

### Feature Groups
- **realtime_features_target_fg (v1)**
  - Primary keys: `feed_timestamp`, `trip_id`, `stop_id`
  - Event time: `feed_timestamp`
  - Contains engineered features + target

Feature group materialization runs asynchronously in Hopsworks.

---

## 5. Feature Pipeline

**Script:**  
```bash
python scripts/feature_pipeline.py


Live Demo

The real-time DelayLens UI is deployed on Hugging Face Spaces:
https://huggingface.co/spaces/teeda-ml/delaylens