"""
app.py
------
Streamlit dashboard for the Edge Vehicle Analytics prototype.

Run with:
    streamlit run app.py

This file is intentionally "just wiring": it reads sidebar controls, pulls
frames from a webcam or uploaded video, and calls out to the detection /
analytics / alerts / database modules for everything else.
"""

import os
import tempfile
import time
import logging

import cv2
import streamlit as st

from config import (
    APP_TITLE,
    DEFAULT_CONFIDENCE_THRESHOLD,
    DEFAULT_IMAGE_SIZE,
    DEFAULT_RISK_THRESHOLDS,
    DEFAULT_PROXIMITY_BANDS,
    SAMPLE_VIDEOS_DIR,
    DB_PATH,
)
from detection.detector import VehicleDetector, ModelLoadError
from detection.tracker import TrackManager
from analytics.proximity import find_proximity_pairs
from analytics.trajectory import TrajectoryStore
from analytics.risk_engine import evaluate_pair
from alerts.alert_manager import AlertManager
from database.db import init_db, log_event, get_recent_events, make_event, DatabaseError
from utils.helpers import (
    traffic_level,
    draw_detection_box,
    draw_trajectory,
    draw_risk_pair,
    draw_high_risk_banner,
    count_by_category,
    bgr_to_rgb,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="Edge Vehicle Safety", layout="wide")

# ---------------------------------------------------------------------------
# Session state — everything that must survive across Streamlit re-runs
# ---------------------------------------------------------------------------
def init_session_state():
    defaults = {
        "running": False,
        "detector": None,
        "model_error": None,
        "track_manager": TrackManager(),
        "trajectory_store": TrajectoryStore(),
        "alert_manager": AlertManager(),
        "last_alert_flash_until": 0.0,
        "db_ready": False,
        "db_error": None,
        "current_stats": {
            "vehicles": 0,
            "pedestrians": 0,
            "traffic_level": "LOW",
            "risk_score": 0,
            "status": "SAFE",
        },
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_session_state()

# Initialize DB once per session
if not st.session_state.db_ready and st.session_state.db_error is None:
    try:
        init_db()
        st.session_state.db_ready = True
    except DatabaseError as exc:
        st.session_state.db_error = str(exc)


# ---------------------------------------------------------------------------
# Sidebar controls
# ---------------------------------------------------------------------------
st.sidebar.title("⚙️ Controls")

input_source = st.sidebar.radio(
    "Input source", ["Laptop webcam", "Upload MP4 video", "Demo mode (sample video)"]
)

uploaded_file = None
if input_source == "Upload MP4 video":
    uploaded_file = st.sidebar.file_uploader("Traffic video (.mp4)", type=["mp4", "mov", "avi"])

sample_video_choice = None
if input_source == "Demo mode (sample video)":
    if os.path.isdir(SAMPLE_VIDEOS_DIR):
        sample_files = [f for f in os.listdir(SAMPLE_VIDEOS_DIR) if f.lower().endswith((".mp4", ".mov", ".avi"))]
    else:
        sample_files = []
    if sample_files:
        sample_video_choice = st.sidebar.selectbox("Sample video", sample_files)
    else:
        st.sidebar.warning(
            f"No sample videos found. Place an .mp4 file in:\n`{SAMPLE_VIDEOS_DIR}`"
        )

st.sidebar.markdown("---")
confidence_threshold = st.sidebar.slider(
    "Detection confidence threshold", 0.10, 0.90, DEFAULT_CONFIDENCE_THRESHOLD, 0.05
)
image_size = st.sidebar.select_slider(
    "Inference resolution (px)", options=[320, 480, 640, 960], value=DEFAULT_IMAGE_SIZE
)

st.sidebar.markdown("---")
st.sidebar.subheader("Risk thresholds")
caution_threshold = st.sidebar.slider(
    "CAUTION starts at", 10, 90, DEFAULT_RISK_THRESHOLDS["safe_max"] + 1
)
high_risk_threshold = st.sidebar.slider(
    "HIGH RISK starts at", caution_threshold + 1, 100, DEFAULT_RISK_THRESHOLDS["caution_max"] + 1
)
risk_thresholds = {
    "safe_max": caution_threshold - 1,
    "caution_max": high_risk_threshold - 1,
}

st.sidebar.markdown("---")
alerts_enabled = st.sidebar.checkbox("Enable safety alerts", value=True)
sound_enabled = st.sidebar.checkbox("Enable alert sound", value=True)

st.sidebar.markdown("---")
col_start, col_stop = st.sidebar.columns(2)
start_clicked = col_start.button("▶ Start", use_container_width=True)
stop_clicked = col_stop.button("■ Stop", use_container_width=True)

if start_clicked:
    st.session_state.running = True
if stop_clicked:
    st.session_state.running = False

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title(APP_TITLE)
st.caption(
    "Hackathon prototype — relative pixel-based proximity, not certified "
    "collision-warning hardware. See README for full limitations."
)

if st.session_state.db_error:
    st.warning(f"Database unavailable, events will not be saved this session: {st.session_state.db_error}")

# ---------------------------------------------------------------------------
# Load model (once)
# ---------------------------------------------------------------------------
if st.session_state.detector is None and st.session_state.model_error is None:
    with st.spinner("Loading YOLO model (first run may download weights)..."):
        try:
            st.session_state.detector = VehicleDetector()
        except ModelLoadError as exc:
            st.session_state.model_error = str(exc)

if st.session_state.model_error:
    st.error(st.session_state.model_error)
    st.stop()

# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------
video_col, stats_col = st.columns([2, 1])

with video_col:
    st.subheader("Live Video")
    video_placeholder = st.empty()
    banner_placeholder = st.empty()

with stats_col:
    st.subheader("Detection Statistics")
    vehicles_metric = st.empty()
    pedestrians_metric = st.empty()
    traffic_metric = st.empty()
    risk_metric = st.empty()
    status_metric = st.empty()

st.markdown("---")
st.subheader("Recent Safety Events")
events_placeholder = st.empty()


def render_stats(stats: dict):
    vehicles_metric.metric("Vehicles Detected", stats["vehicles"])
    pedestrians_metric.metric("Pedestrians Detected", stats["pedestrians"])
    traffic_metric.metric("Traffic Level", stats["traffic_level"])
    risk_metric.metric("Current Risk Score", f"{stats['risk_score']:.0f}/100")

    status = stats["status"]
    if status == "HIGH RISK":
        status_metric.error(f"Safety Status: {status}")
    elif status == "CAUTION":
        status_metric.warning(f"Safety Status: {status}")
    else:
        status_metric.success(f"Safety Status: {status}")


def render_events_table():
    events = get_recent_events(limit=15)
    if not events:
        events_placeholder.info("No safety events logged yet.")
        return
    rows = [
        {
            "Time": e.timestamp,
            "Vehicle ID": e.vehicle_id,
            "Pedestrian ID": e.pedestrian_id,
            "Risk": f"{e.risk_score:.0f}",
            "Proximity (px)": f"{e.approx_proximity_px:.0f}",
            "Status": e.status,
        }
        for e in events
    ]
    events_placeholder.table(rows)


# Always render current (possibly stale) stats/events, even when not running
render_stats(st.session_state.current_stats)
render_events_table()


# ---------------------------------------------------------------------------
# Video source resolution
# ---------------------------------------------------------------------------
def resolve_video_source():
    """
    Returns a value suitable for cv2.VideoCapture(), or None + an error
    message if the source can't be resolved.
    """
    if input_source == "Laptop webcam":
        return 0, None

    if input_source == "Upload MP4 video":
        if uploaded_file is None:
            return None, "Please upload an MP4/MOV/AVI file to continue."
        tmp_dir = tempfile.gettempdir()
        tmp_path = os.path.join(tmp_dir, f"uploaded_{int(time.time())}_{uploaded_file.name}")
        with open(tmp_path, "wb") as f:
            f.write(uploaded_file.read())
        return tmp_path, None

    if input_source == "Demo mode (sample video)":
        if sample_video_choice is None:
            return None, (
                f"No sample video selected. Add an .mp4 file to "
                f"`{SAMPLE_VIDEOS_DIR}` and refresh."
            )
        return os.path.join(SAMPLE_VIDEOS_DIR, sample_video_choice), None

    return None, "Unknown input source."


# ---------------------------------------------------------------------------
# Main processing loop
# ---------------------------------------------------------------------------
def process_frame(frame, detector, track_manager, trajectory_store, alert_manager):
    detections = detector.detect_and_track(
        frame, confidence=confidence_threshold, image_size=image_size
    )
    detections = track_manager.update(detections)

    for det in detections:
        if det.track_id is not None:
            trajectory_store.update(det.track_id, det.center)

    track_manager.prune_stale()
    trajectory_store.prune(track_manager.get_active_ids())

    vehicles, pedestrians = count_by_category(detections)
    level = traffic_level(vehicles)

    pairs = find_proximity_pairs(detections, max_pixel_distance=600)
    results = [
        evaluate_pair(pair, trajectory_store, thresholds=risk_thresholds)
        for pair in pairs
    ]

    frame_max_risk = 0.0
    frame_status = "SAFE"
    high_risk_hit = False

    for det in detections:
        draw_detection_box(frame, det)
        if det.track_id is not None:
            draw_trajectory(frame, det.track_id, trajectory_store)

    center_lookup = {d.track_id: d.center for d in detections if d.track_id is not None}

    for result in results:
        v_center = center_lookup.get(result.vehicle_id)
        p_center = center_lookup.get(result.pedestrian_id)
        if v_center and p_center:
            draw_risk_pair(frame, result, v_center, p_center)

        if result.risk_score > frame_max_risk:
            frame_max_risk = result.risk_score
            frame_status = result.status

        if result.status == "HIGH RISK":
            high_risk_hit = True
            if alerts_enabled and alert_manager.should_alert(result.vehicle_id, result.pedestrian_id):
                alert_manager.play_sound(enabled=sound_enabled)
                if st.session_state.db_ready:
                    event = make_event(
                        vehicle_id=result.vehicle_id,
                        pedestrian_id=result.pedestrian_id,
                        risk_score=result.risk_score,
                        proximity_px=result.pixel_distance,
                        status=result.status,
                    )
                    log_event(event)

    stats = {
        "vehicles": vehicles,
        "pedestrians": pedestrians,
        "traffic_level": level,
        "risk_score": frame_max_risk,
        "status": frame_status,
    }
    return frame, stats, high_risk_hit


def run_video_loop():
    source, error = resolve_video_source()
    if error:
        st.error(error)
        st.session_state.running = False
        return

    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        st.error(
            "Could not open the video source. If using the webcam, make sure "
            "it isn't in use by another app and that Streamlit has camera "
            "permission. If using a file, confirm it's a valid, readable video."
        )
        st.session_state.running = False
        return

    detector = st.session_state.detector
    track_manager = st.session_state.track_manager
    trajectory_store = st.session_state.trajectory_store
    alert_manager = st.session_state.alert_manager

    frame_count = 0
    try:
        while st.session_state.running:
            ok, frame = cap.read()
            if not ok or frame is None:
                if input_source != "Laptop webcam":
                    st.info("End of video reached.")
                else:
                    st.error("Lost connection to the webcam.")
                st.session_state.running = False
                break

            frame_count += 1
            # Skip frame resize logic is handled by YOLO's imgsz param;
            # we keep the display frame at native resolution for clarity.
            processed_frame, stats, high_risk_hit = process_frame(
                frame, detector, track_manager, trajectory_store, alert_manager
            )

            if high_risk_hit and alerts_enabled:
                draw_high_risk_banner(processed_frame)
                st.session_state.last_alert_flash_until = time.time() + 1.5

            video_placeholder.image(bgr_to_rgb(processed_frame), channels="RGB", use_container_width=True)

            st.session_state.current_stats = stats
            render_stats(stats)

            if high_risk_hit:
                render_events_table()

            # Small sleep to keep UI responsive; also naturally caps FPS
            # so a fast laptop doesn't spin at 100% CPU for no benefit.
            time.sleep(0.01)
    finally:
        cap.release()


if st.session_state.running:
    run_video_loop()
else:
    st.info("Select an input source and press ▶ Start to begin the live demo.")
