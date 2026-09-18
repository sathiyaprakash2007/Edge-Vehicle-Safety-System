"""
config.py
---------
Central configuration for the Edge Vehicle Analytics prototype.
All tunable values live here so the rest of the codebase stays clean.
These are DEFAULTS — most are overridden live from the Streamlit sidebar.
"""

import os

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")
DATA_DIR = os.path.join(BASE_DIR, "data")
SAMPLE_VIDEOS_DIR = os.path.join(DATA_DIR, "sample_videos")
DB_PATH = os.path.join(BASE_DIR, "database", "safety_events.db")

# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------
# Lightweight pretrained model — good speed/accuracy tradeoff for a laptop demo.
# Ultralytics will auto-download this the first time it's used.
YOLO_MODEL_NAME = "yolov8n.pt"
YOLO_MODEL_PATH = os.path.join(MODELS_DIR, YOLO_MODEL_NAME)

# COCO class ids we care about for this prototype
# (standard COCO indices used by yolov8n.pt)
TARGET_CLASSES = {
    0: "person",
    1: "bicycle",
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck",
}

VEHICLE_CLASS_NAMES = {"car", "bus", "truck", "motorcycle"}
PEDESTRIAN_CLASS_NAMES = {"person", "bicycle"}

# ---------------------------------------------------------------------------
# Detection / tracking defaults
# ---------------------------------------------------------------------------
DEFAULT_CONFIDENCE_THRESHOLD = 0.35
DEFAULT_IMAGE_SIZE = 640          # inference resolution, smaller = faster
TRACKER_CONFIG = "bytetrack.yaml"  # built into ultralytics

# How many past center-points to keep per tracked object for trajectory lines
TRAJECTORY_HISTORY_LENGTH = 20

# ---------------------------------------------------------------------------
# Risk engine defaults
# ---------------------------------------------------------------------------
DEFAULT_RISK_THRESHOLDS = {
    "safe_max": 39,       # 0-39   -> SAFE
    "caution_max": 69,    # 40-69  -> CAUTION
    # 70-100 -> HIGH RISK
}

# Pixel-distance bands used by the proximity scorer.
# These are RELATIVE (frame-resolution dependent), not real-world meters.
DEFAULT_PROXIMITY_BANDS = {
    "very_close_px": 80,
    "close_px": 160,
    "moderate_px": 280,
}

# Weights used to combine proximity + closing-speed + trajectory alignment
# into the final 0-100 risk score. Must sum to 1.0.
RISK_WEIGHTS = {
    "proximity": 0.55,
    "closing_speed": 0.25,
    "trajectory_alignment": 0.20,
}

# Minimum seconds between two consecutive HIGH RISK alerts for the SAME pair,
# so we don't spam the log / sound every single frame.
ALERT_COOLDOWN_SECONDS = 5.0

# ---------------------------------------------------------------------------
# Traffic level thresholds (based on simultaneous vehicle count)
# ---------------------------------------------------------------------------
TRAFFIC_LEVEL_THRESHOLDS = {
    "low_max": 3,     # 0-3 vehicles   -> LOW
    "medium_max": 8,  # 4-8 vehicles   -> MEDIUM
    # 9+ vehicles -> HIGH
}

# ---------------------------------------------------------------------------
# UI / misc
# ---------------------------------------------------------------------------
APP_TITLE = "Real-Time Edge Vehicle Analytics for Local Traffic & Pedestrian Safety"
WARNING_SOUND_PATH = os.path.join(BASE_DIR, "alerts", "warning.wav")
