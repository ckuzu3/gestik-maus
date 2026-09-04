"""Gestik-Maus - Schritt 3:

- Zeigefinger = Cursor
- Pinch (Daumen + Mittelfinger) = Linksklick
- Klatschen (beide Hände kurz zusammenschlagen) = Steuerung an/aus
- Hand wie einen Regler drehen (Handgelenk drehen) = Lautstärke lauter/leiser

Die Steuerung startet INAKTIV - erst nach einem Klatschen bewegt sich der
Cursor. Nochmal klatschen pausiert wieder. Das verhindert, dass der Cursor
gleich beim Programmstart oder aus Versehen loslegt.

Noch keine Drag-/Scroll-Gesten - siehe CLAUDE.md fuer die naechsten Schritte.
Debug-Fenster mit 'q' oder ESC schliessen.

Fuer Rechner ohne Webcam bzw. ohne Bildschirm (Container, CI) gibt es
--source <videodatei> und --no-window; im Normalfall reicht `python main.py`.
"""

import argparse
import time

import cv2

from capture import Camera
from gestures import (
    ClapDetector,
    ClickGesture,
    RotationVolumeControl,
    hands_centroid_distance,
    pinch_ratio,
)
from mouse_control import MouseController
from smoothing import EMAFilter
from tracker import INDEX_FINGER_TIP, HandTracker
from volume_control import VolumeController


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Gestik-Maus")
    parser.add_argument(
        "--source", default="0",
        help="Kamera-Index (Standard: 0) oder Pfad zu einer Videodatei. "
             "Eine Videodatei ersetzt die Webcam - gedacht zum Testen auf "
             "Rechnern ohne Kamera.",
    )
    parser.add_argument(
        "--no-window", action="store_true",
        help="Debug-Fenster nicht anzeigen (noetig ohne Grafik-Ausgabe).",
    )
    parser.add_argument(
        "--start-active", action="store_true",
        help="Steuerung sofort aktiv statt erst nach dem ersten Klatschen. "
             "Nur zum Testen - im Normalbetrieb absichtlich aus, damit der "
             "Cursor nicht gleich beim Start losgeht.",
    )
    args = parser.parse_args(argv)
    args.source = int(args.source) if args.source.isdigit() else args.source
    return args


def main(argv=None):
    args = parse_args(argv)
    camera = Camera(args.source)
    tracker = HandTracker(max_hands=2)
    mouse = MouseController()
    volume = VolumeController()
    smoother = EMAFilter(alpha=0.4)
    click_gesture = ClickGesture()
    rotation = RotationVolumeControl()
    clap_detector = ClapDetector()

    active = args.start_active
    prev_time = time.time()

    try:
        for frame in camera.frames():
            hands = tracker.process(frame)
            now = time.time()

            # Klatschen wird IMMER geprueft (auch wenn gerade inaktiv), sonst
            # koennte man die Steuerung nie wieder aufwecken.
            if clap_detector.update(hands, now):
                active = not active
                smoother.reset()
                click_gesture.reset()
                rotation.reset()

            # Alle erkannten Haende zur Kontrolle einzeichnen.
            for h in hands:
                tracker.draw(frame, h)

            # Live-Diagnose fuer die Klatsch-Erkennung: Anzahl erkannter
            # Haende und (falls 2) der tatsaechliche Zentren-Abstand im
            # Vergleich zu den beiden Schwellenwerten. Damit sich
            # APART_THRESHOLD/TOUCH_THRESHOLD in gestures.py anhand echter
            # Werte justieren lassen, statt zu raten.
            clap_dist = hands_centroid_distance(hands)
            clap_info = f"Haende: {len(hands)}"
            if clap_dist is not None:
                clap_info += (
                    f" | Klatsch-Abstand: {clap_dist:.2f} "
                    f"(auseinander>{ClapDetector.APART_THRESHOLD:.2f}, "
                    f"beieinander<{ClapDetector.TOUCH_THRESHOLD:.2f}, "
                    f"war_auseinander={clap_detector._was_apart})"
                )
            cv2.putText(
                frame, clap_info, (10, 140),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2,
            )

            primary = hands[0] if hands else None

            if active and primary is not None:
                tip = primary[INDEX_FINGER_TIP]
                sx, sy = smoother.update(tip.x, tip.y)
                mouse.move_to_normalized(sx, sy)

                ratio = pinch_ratio(primary)
                pinching = ratio < click_gesture.threshold
                if click_gesture.update(primary):
                    mouse.click()

                step = rotation.update(primary)
                if step > 0:
                    volume.step_up()
                elif step < 0:
                    volume.step_down()

                dot_color = (0, 0, 255) if pinching else (0, 255, 0)
                cv2.circle(
                    frame,
                    (int(tip.x * frame.shape[1]), int(tip.y * frame.shape[0])),
                    10, dot_color, -1,
                )
                cv2.putText(
                    frame, f"Pinch-Wert: {ratio:.2f} (Schwelle: {click_gesture.threshold:.2f})",
                    (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.8, dot_color, 2,
                )
                if pinching:
                    cv2.putText(
                        frame, "PINCH", (10, 105),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2,
                    )
            else:
                smoother.reset()
                click_gesture.reset()
                rotation.reset()

            now2 = time.time()
            fps = 1.0 / max(now2 - prev_time, 1e-6)
            prev_time = now2
            cv2.putText(
                frame, f"FPS: {fps:.1f}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2,
            )

            status_text = "AKTIV" if active else "INAKTIV (klatschen zum Aktivieren)"
            status_color = (0, 255, 0) if active else (0, 0, 255)
            cv2.putText(
                frame, status_text, (10, frame.shape[0] - 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, status_color, 2,
            )

            if args.no_window:
                continue
            cv2.imshow("Gestik-Maus - Debug (q zum Beenden)", frame)
            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), 27):  # 27 = ESC
                break
    finally:
        camera.release()
        tracker.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
