# DelayLens – Real-Time Public Transit Delay Prediction

**Course:** ID2223 – Scalable Machine Learning  
**Institution:** KTH Royal Institute of Technology  

## 0. Project Name and Group Members
**Project Name:** DelayLens – Real-Time Public Transit Delay Prediction  

**Group Members:**  
- Tida Bayo  

---

## 1. Dynamic Data Sources
This project uses **dynamic, real-time data sources** and does not rely on static Kaggle datasets.

- **GTFS-Realtime Trip Updates**  
  Live streaming data providing real-time information about vehicle movements and delays.
- **Static GTFS Schedules**  
  Route, stop, and trip metadata used to contextualize live updates.

The real-time data is continuously fetched and processed to reflect the current state of public transit.

---

## 2. Prediction Problem
The goal of this project is to **predict and monitor public transit delays in real time**.

By combining GTFS-Realtime trip updates with static GTFS schedule data, the system produces enriched features that:
- Capture current delays at stop and route level
- Can be used to train machine learning models for delay prediction
- Support real-time monitoring and downstream decision-making

---

## 3. User Interface
The project provides a **web-based dashboard built with Streamlit**.

The UI allows users to:
- View live public transit trip updates
- Inspect delay information at stop and route level
- Understand how real-time data is processed and updated continuously

To run the UI locally:
```bash
streamlit run ui/app.py


Technologies Used

Python

GTFS-Realtime

Pandas

Streamlit

REST APIs

Git and GitHub
