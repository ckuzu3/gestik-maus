"""MediaPipe-Wrapper (Tasks API): Frame -> Hand-Landmarks (21 Punkte, normiert 0..1).

Nutzt die neue MediaPipe Tasks API (HandLandmarker). Die alte
`mediapipe.solutions` / `mediapipe.python.solutions`-API (aus der ersten
Version dieses Skripts) existiert in aktuell installierten mediapipe-Versionen
nicht mehr, daher dieser Wechsel.

Die Tasks API braucht eine Modell-Datei (hand_landmarker.task). Sie wird
beim ersten Start automatisch neben dieses Skript heruntergeladen, falls sie
fehlt.
"""

import os
import time
import urllib.request

import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_tasks
from mediapipe.tasks.python import vision

# Landmark-Index der Zeigefingerspitze im 21-Punkte-Handmodell.
INDEX_FINGER_TIP = 8

MODEL_PATH = os.path.join(os.path.dirname(__file__), "hand_landmarker.task")
MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
    "hand_landmarker/float16/latest/hand_landmarker.task"
)

# Standard-Verbindungen zwischen den 21 Hand-Landmarks (nur zum Zeichnen im
# Debug-Fenster, ersetzt die frühere mp.solutions.drawing_utils).
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),          # Daumen
    (0, 5), (5, 6), (6, 7), (7, 8),          # Zeigefinger
    (5, 9), (9, 10), (10, 11), (11, 12),     # Mittelfinger
    (9, 13), (13, 14), (14, 15), (15, 16),   # Ringfinger
    (13, 17), (17, 18), (18, 19), (19, 20),  # kleiner Finger
    (0, 17),                                  # Handballen
]


def _ensure_model():
    if os.path.exists(MODEL_PATH):
        return
    print(f"Lade Hand-Landmark-Modell herunter nach {MODEL_PATH} ...")
    try:
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
        print("Download abgeschlossen.")
    except Exception as exc:
        raise RuntimeError(
            "Konnte das Hand-Landmark-Modell nicht automatisch herunterladen "
            f"({exc}).\nBitte manuell laden von:\n{MODEL_URL}\n"
            f"und als Datei speichern unter:\n{MODEL_PATH}"
        ) from exc


class HandTracker:
    def __init__(self, max_hands: int = 1, min_detection_confidence: float = 0.7,
                 min_tracking_confidence: float = 0.6):
        _ensure_model()
        base_options = mp_tasks.BaseOptions(model_asset_path=MODEL_PATH)
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_hands=max_hands,
            min_hand_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )
        self.detector = vision.HandLandmarker.create_from_options(options)
        self._start_time = time.time()

    def process(self, frame_bgr):
        """Gibt eine Liste erkannter Hände zurück (0, 1 oder bis zu max_hands
        Einträge). Jede Hand ist eine Liste von 21 Landmarks mit .x, .y
        (normiert 0..1, 0,0 = oben links) und .z. Leere Liste = keine Hand
        erkannt."""
        rgb = frame_bgr[:, :, ::-1].copy()  # BGR -> RGB, kontiguierlich fuer mp.Image
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        timestamp_ms = int((time.time() - self._start_time) * 1000)
        result = self.detector.detect_for_video(mp_image, timestamp_ms)
        return result.hand_landmarks or []

    def draw(self, frame_bgr, landmarks):
        """Zeichnet die Landmarks zu Debug-Zwecken auf den Frame (in-place)."""
        if landmarks is None:
            return
        h, w = frame_bgr.shape[:2]
        points = [(int(lm.x * w), int(lm.y * h)) for lm in landmarks]
        for a, b in HAND_CONNECTIONS:
            cv2.line(frame_bgr, points[a], points[b], (0, 200, 0), 2)
        for x, y in points:
            cv2.circle(frame_bgr, (x, y), 4, (0, 255, 0), -1)

    def close(self):
        self.detector.close()
