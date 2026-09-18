"""
tests_smoke.py
---------------
Lightweight smoke tests that exercise the analytics/alerts/database logic
WITHOUT needing a webcam, a video file, or the ultralytics package to be
fully functional. Good for a quick "did I break anything" check before a
demo, and for judges who want to see the risk logic is real and testable.

Run with:
    python tests_smoke.py
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_proximity_and_risk():
    from detection.detector import Detection
    from analytics.proximity import find_proximity_pairs
    from analytics.trajectory import TrajectoryStore
    from analytics.risk_engine import evaluate_pair

    vehicle = Detection(track_id=1, class_name="car", confidence=0.9, bbox=[90, 90, 150, 150])
    pedestrian = Detection(track_id=2, class_name="person", confidence=0.85, bbox=[160, 90, 190, 150])

    pairs = find_proximity_pairs([vehicle, pedestrian])
    assert len(pairs) == 1, "Expected exactly one vehicle/pedestrian pair"

    store = TrajectoryStore()
    for x in [300, 280, 260, 240]:
        store.update(1, [x, 200])

    result = evaluate_pair(pairs[0], store)
    assert 0 <= result.risk_score <= 100
    assert result.status in ("SAFE", "CAUTION", "HIGH RISK")
    print("[PASS] proximity + risk engine")


def test_alert_cooldown():
    from alerts.alert_manager import AlertManager

    manager = AlertManager(cooldown_seconds=100)
    assert manager.should_alert(1, 2) is True
    assert manager.should_alert(1, 2) is False, "Cooldown should block immediate repeat alert"
    print("[PASS] alert cooldown")


def test_database_roundtrip():
    from database.db import init_db, log_event, get_recent_events, make_event

    tmp_db = os.path.join(tempfile.gettempdir(), "smoke_test_safety.db")
    if os.path.exists(tmp_db):
        os.remove(tmp_db)

    init_db(tmp_db)
    event = make_event(
        vehicle_id=1, pedestrian_id=2, risk_score=88.5,
        proximity_px=42.0, status="HIGH RISK",
    )
    row_id = log_event(event, tmp_db)
    assert row_id is not None

    events = get_recent_events(limit=5, db_path=tmp_db)
    assert len(events) == 1
    assert events[0].status == "HIGH RISK"
    print("[PASS] database roundtrip")


def test_traffic_level():
    from utils.helpers import traffic_level

    assert traffic_level(0) == "LOW"
    assert traffic_level(5) == "MEDIUM"
    assert traffic_level(20) == "HIGH"
    print("[PASS] traffic level bucketing")


if __name__ == "__main__":
    test_proximity_and_risk()
    test_alert_cooldown()
    test_database_roundtrip()
    test_traffic_level()
    print("\nAll smoke tests passed.")
