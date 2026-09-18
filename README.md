# Real-Time Edge Vehicle Analytics for Local Traffic and Pedestrian Safety

**Hackathon prototype — 24-hour build**

A real-time computer vision app that watches a webcam or traffic video,
detects and tracks vehicles and pedestrians, estimates how close they are
getting to each other, and raises an immediate on-screen (and optional
audio) warning when a situation looks dangerous.

> ⚠️ **This is a hackathon prototype, not a certified safety product.**
> See [Limitations](#limitations) before drawing any real-world conclusions
> from its output.

---

## Table of Contents

- [Problem Statement](#problem-statement)
- [Proposed Solution](#proposed-solution)
- [Why Edge AI?](#why-edge-ai)
- [System Architecture](#system-architecture)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Installation](#installation)
- [How to Run](#how-to-run)
- [Demo Instructions](#demo-instructions)
- [Screenshots](#screenshots)
- [Future Improvements](#future-improvements)
- [Limitations](#limitations)
- [Team Contributions](#team-contributions)

---

## Problem Statement

Pedestrian injuries and fatalities from vehicle collisions remain a major
urban safety issue, especially at unsignalized crossings, in parking lots,
and near school zones. Most existing collision-warning systems are either
built into new vehicles (expensive, not retrofittable) or rely on cloud
processing (adds latency, needs connectivity, raises privacy concerns for
constant video upload).

## Proposed Solution

A lightweight, **camera-only** system that runs entirely on a local
laptop ("the edge device"):

1. Detects vehicles and pedestrians in the live video feed.
2. Tracks each one individually across frames.
3. Estimates how close vehicle/pedestrian pairs are getting, and whether
   they're moving toward each other.
4. Scores the situation 0-100 and classifies it SAFE / CAUTION / HIGH RISK.
5. Immediately shows a warning banner (and optional sound) when risk is
   high, and logs the event locally for later review.

No cloud dependency for the core safety loop — it works offline, which
also means no raw video ever has to leave the device.

## Why Edge AI?

- **Latency**: a collision-risk warning that arrives 2 seconds late over
  a network round-trip is much less useful than one computed instantly
  on-device.
- **Privacy**: video frames never have to leave the laptop for the core
  detection/alert loop.
- **Reliability**: works even with no or unstable internet — important
  for street-level or outdoor deployments.
- **Cost**: no cloud GPU bill; a modern laptop CPU is enough for a
  lightweight YOLO model at a usable frame rate.

## System Architecture

```
        Camera (webcam or video file)
                    │
                    ▼
          Local Edge Device (laptop)
                    │
                    ▼
             YOLO Detection
       (person, bicycle, car, motorcycle,
              bus, truck)
                    │
                    ▼
           ByteTrack Tracking
     (stable ID per object across frames)
                    │
                    ▼
             Risk Analysis
   (relative proximity + trajectory + closing speed
              → 0-100 risk score)
                    │
                    ▼
              Local Alert
   (on-screen banner, optional sound, SQLite log)
```

Everything above the "Local Alert" box runs **on the laptop** — the
laptop *is* the edge device in this prototype. There is no server
component.

## Features

- Live webcam **or** uploaded MP4 video as input, with Start/Stop controls
- YOLO-based detection of `person`, `bicycle`, `motorcycle`, `car`, `bus`, `truck`
- ByteTrack-based multi-object tracking with a persistent ID per object
  (`Car #12`, `Person #7`, ...)
- Live counts: vehicles detected, pedestrians detected, traffic level
  (LOW / MEDIUM / HIGH)
- Relative proximity analysis between every vehicle/pedestrian pair
  (explicitly labeled as pixel-based, **not** meters)
- Trajectory trails + a simple "are they closing in on each other?" estimate
- Transparent, configurable, rule-based 0-100 risk score → SAFE / CAUTION / HIGH RISK
- Large on-screen "PEDESTRIAN COLLISION RISK — SLOW DOWN" warning with a
  cooldown so it doesn't spam every frame
- Optional alert sound
- SQLite event log (timestamp, vehicle ID, pedestrian ID, risk score,
  proximity, status) with a live "Recent Safety Events" table in the UI
- Demo Mode using a prerecorded sample video, so the whole thing still
  works if the venue wifi/webcam is unreliable
- Friendly error handling for missing webcam, bad video files, missing
  model weights, and database errors

## Technology Stack

| Layer         | Choice                                   |
|---------------|-------------------------------------------|
| Language      | Python 3.10+                              |
| Detection     | Ultralytics YOLOv8 (`yolov8n.pt`, pretrained on COCO) |
| Tracking      | ByteTrack (built into Ultralytics' `.track()` API) |
| Video I/O     | OpenCV                                    |
| Dashboard     | Streamlit                                 |
| Storage       | SQLite (stdlib `sqlite3`)                 |
| Math/arrays   | NumPy                                     |
| Alert sound   | `playsound` (optional, fails gracefully)  |

## Installation

```bash
# 1. Clone / unzip the project, then cd into it
cd edge_vehicle_safety

# 2. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

See [`models/README.md`](models/README.md) for model download details —
short version: nothing manual is required, Ultralytics auto-downloads
`yolov8n.pt` the first time you run the app.

## How to Run

```bash
streamlit run app.py
```

Streamlit will open the dashboard in your browser (usually
`http://localhost:8501`). In the sidebar:

1. Choose an input source: **Laptop webcam**, **Upload MP4 video**, or
   **Demo mode (sample video)**.
2. Adjust confidence / risk thresholds if you like (defaults work fine).
3. Press **▶ Start**. Press **■ Stop** any time.

## Demo Instructions

**Fastest, most reliable path for judges:**

1. Drop a short traffic/crosswalk clip into `data/sample_videos/`
   (see that folder's README for tips on where to find one).
2. Run `streamlit run app.py`.
3. Select **Demo mode (sample video)** → pick your file → **Start**.
4. Point out, live, as a vehicle and pedestrian get close: watch the
   connecting line turn amber (CAUTION) then red (HIGH RISK), the risk
   score climb, and the warning banner + log entry appear.
5. Open the **Recent Safety Events** table to show the SQLite log is real
   and persistent.

**If the webcam works reliably at your venue**, "Laptop webcam" is more
impressive — just make sure someone can safely walk in front of a "car"
(even just another person miming holding a car-sized box, or a remote
control car) to trigger a HIGH RISK moment.

## Screenshots

_(Add screenshots/GIFs of the running dashboard here before submission —
e.g. `docs/screenshot_dashboard.png`, `docs/screenshot_high_risk.png`.)_

## Future Improvements

- Camera calibration (known camera height/tilt/focal length) to convert
  pixel distance into an actual real-world distance estimate
- Kalman-filter or learned trajectory prediction instead of simple
  frame-to-frame deltas
- Multi-camera fusion for wider intersection coverage
- On-device model quantization (e.g. ONNX/TensorRT) for higher FPS on
  lower-power edge hardware (Jetson, Raspberry Pi + accelerator)
- Configurable per-zone risk rules (e.g. stricter thresholds right at a
  marked crosswalk)
- Historical analytics dashboard (risk hot-spots over time, by hour/day)

## Limitations

- **Pixel distance is a relative proximity estimate only** — without
  camera calibration it cannot be converted to meters/feet. Two objects
  that look "close" in a wide-angle or far-zoomed shot may be much
  farther apart in reality than the pixel distance suggests.
- **This is a prototype risk score, not a certified collision-warning
  system.** It must not be used for safety-critical decisions, vehicle
  control, or as a substitute for driver attention.
- Detection quality depends heavily on camera angle, lighting, occlusion,
  motion blur, and the limits of the pretrained COCO model (e.g. it was
  not fine-tuned on this specific deployment's camera).
- Tracking IDs can occasionally switch during heavy occlusion (e.g. one
  pedestrian walking behind another), which can briefly distort
  trajectory/closing-speed estimates.
- Frame rate and accuracy trade off against each other on CPU-only
  laptops; lower `imgsz` / resolution improves speed at some accuracy cost.

## Team Contributions

_(Fill in for your team before submission, e.g.:)_

| Name | Contribution |
|------|--------------|
| —    | Detection & tracking pipeline |
| —    | Risk engine & analytics |
| —    | Streamlit dashboard & UX |
| —    | Database, alerts, and testing |
