"""Gesten-Klassifikation auf Basis von Landmark-Listen.

Bewusst ohne Kamera-/Tracker-Abhaengigkeit geschrieben (reine Funktionen auf
Landmark-Koordinaten), damit sich das mit Fixture-Daten unit-testen laesst,
ohne dass eine Webcam laufen muss.
"""

import math

THUMB_TIP = 4
MIDDLE_FINGER_TIP = 12
WRIST = 0
MIDDLE_FINGER_MCP = 9

# Pinch-Abstand (Daumen-Mittelfinger), normiert auf die Handspanne
# (Handgelenk -> Mittelfinger-Basis). Normierung macht die Schwelle
# unabhaengig davon, wie nah die Hand an der Kamera ist.
#
# Bewusst Mittelfinger statt Zeigefinger fuer den Klick: der Zeigefinger
# steuert den Cursor, wuerde also beim Klick-Pinch selbst mitwandern und den
# Cursor kurz vor dem Klick verschieben. Mittelfinger+Daumen laesst den
# Zeigefinger/Cursor unbeeinflusst.
PINCH_THRESHOLD = 0.35


def _distance(a, b) -> float:
    return math.hypot(a.x - b.x, a.y - b.y)


def pinch_ratio(landmarks) -> float:
    """Kleiner Wert = Daumen und Mittelfinger sind nah beieinander (Pinch)."""
    hand_span = _distance(landmarks[WRIST], landmarks[MIDDLE_FINGER_MCP])
    if hand_span < 1e-6:
        return 1.0
    pinch_dist = _distance(landmarks[THUMB_TIP], landmarks[MIDDLE_FINGER_TIP])
    return pinch_dist / hand_span


def is_pinching(landmarks, threshold: float = PINCH_THRESHOLD) -> bool:
    return pinch_ratio(landmarks) < threshold


class ClickGesture:
    """Erkennt den Uebergang 'nicht gepincht' -> 'gepincht' und meldet genau
    einen Klick pro Pinch (kein Dauerfeuer, solange man die Finger zusammen
    haelt). Bei verlorener Hand-Erkennung mit reset() zuruecksetzen."""

    def __init__(self, threshold: float = PINCH_THRESHOLD):
        self.threshold = threshold
        self._was_pinching = False

    def update(self, landmarks) -> bool:
        """True genau in dem Frame, in dem ein neuer Pinch beginnt."""
        pinching = is_pinching(landmarks, self.threshold)
        just_started = pinching and not self._was_pinching
        self._was_pinching = pinching
        return just_started

    def reset(self):
        self._was_pinching = False


def _centroid(landmarks):
    xs = [lm.x for lm in landmarks]
    ys = [lm.y for lm in landmarks]
    return (sum(xs) / len(xs), sum(ys) / len(ys))


def hands_centroid_distance(hands_landmarks):
    """Abstand zwischen den Zentren der ersten beiden erkannten Haende, oder
    None, wenn weniger als 2 Haende erkannt wurden. Nur zu Debug-/
    Kalibrierzwecken (ClapDetector.update macht die eigentliche Erkennung)."""
    if len(hands_landmarks) < 2:
        return None
    c1 = _centroid(hands_landmarks[0])
    c2 = _centroid(hands_landmarks[1])
    return math.hypot(c1[0] - c2[0], c1[1] - c2[1])


class ClapDetector:
    """Erkennt eine Klatsch-Geste anhand zweier Hand-Zentren: die Hände
    waren auseinander und kommen sich dann schnell sehr nah. Braucht beide
    Hände im selben Frame, ansonsten passiert nichts (kein Fehler)."""

    APART_THRESHOLD = 0.4   # Zentren gelten als "auseinander" (normierter Abstand)
    TOUCH_THRESHOLD = 0.12  # Zentren gelten als "beieinander" (Klatsch-Moment)
    COOLDOWN_S = 0.8        # Mindestabstand zwischen zwei erkannten Klatschern

    def __init__(self):
        self._was_apart = False
        self._last_clap_time = 0.0

    def update(self, hands_landmarks, now: float) -> bool:
        """hands_landmarks: Liste von Hand-Landmark-Listen (aus
        HandTracker.process). Gibt True zurück genau in dem Frame, in dem
        ein Klatschen erkannt wird."""
        if len(hands_landmarks) < 2:
            return False

        c1 = _centroid(hands_landmarks[0])
        c2 = _centroid(hands_landmarks[1])
        dist = math.hypot(c1[0] - c2[0], c1[1] - c2[1])

        clapped = False
        if dist > self.APART_THRESHOLD:
            self._was_apart = True
        elif dist < self.TOUCH_THRESHOLD and self._was_apart:
            self._was_apart = False
            if now - self._last_clap_time > self.COOLDOWN_S:
                clapped = True
                self._last_clap_time = now
        return clapped


class RotationVolumeControl:
    """Erkennt eine Dreh-Geste (Handgelenk drehen wie an einem Regler) und
    meldet Lautstärke-Schritte. Nutzt den Winkel des Vektors
    Handgelenk -> Mittelfinger-Basis in der Bildebene; die Drehung wird
    aufsummiert und löst alle DEGREES_PER_STEP Grad einen Schritt aus (wie
    bei einem Drehregler mit Rasterung), damit kleines Zittern nicht schon
    Lautstärke-Schritte auslöst."""

    DEGREES_PER_STEP = 15.0

    def __init__(self, degrees_per_step: float = DEGREES_PER_STEP):
        self.degrees_per_step = degrees_per_step
        self._prev_angle = None
        self._accumulated = 0.0

    def update(self, landmarks) -> int:
        """Gibt -1 (leiser), 0 (kein Schritt) oder +1 (lauter) zurück."""
        wrist = landmarks[WRIST]
        mcp = landmarks[MIDDLE_FINGER_MCP]
        angle = math.degrees(math.atan2(mcp.y - wrist.y, mcp.x - wrist.x))

        if self._prev_angle is None:
            self._prev_angle = angle
            return 0

        delta = angle - self._prev_angle
        delta = (delta + 180) % 360 - 180  # kürzeste Richtung, -180..180
        self._prev_angle = angle
        self._accumulated += delta

        if self._accumulated >= self.degrees_per_step:
            self._accumulated -= self.degrees_per_step
            return 1
        if self._accumulated <= -self.degrees_per_step:
            self._accumulated += self.degrees_per_step
            return -1
        return 0

    def reset(self):
        self._prev_angle = None
        self._accumulated = 0.0
