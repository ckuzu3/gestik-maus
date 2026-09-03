"""Webcam-Capture: liefert gespiegelte BGR-Frames als Generator."""

import cv2


class Camera:
    def __init__(self, index: int = 0, width: int = 1280, height: int = 720):
        self.cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        if not self.cap.isOpened():
            raise RuntimeError(
                f"Konnte Webcam mit Index {index} nicht öffnen. "
                "Ist eine andere App gerade auf die Kamera zu?"
            )

    def frames(self):
        """Generator: liefert horizontal gespiegelte BGR-Frames (Spiegel-Effekt,
        fühlt sich vor der Kamera natürlicher an als unmodifiziert).

        Ein einzelner fehlgeschlagener Frame-Read (kommt bei manchen
        Webcam-Treibern gelegentlich vor) wird übersprungen statt das ganze
        Programm abstürzen zu lassen. Erst nach vielen Fehlversuchen am
        Stück gilt die Kamera als wirklich getrennt."""
        consecutive_failures = 0
        while True:
            ok, frame = self.cap.read()
            if not ok:
                consecutive_failures += 1
                if consecutive_failures > 30:
                    raise RuntimeError(
                        "Konnte dauerhaft kein Frame von der Webcam lesen "
                        "(30 Fehlversuche in Folge). Ist die Kamera getrennt "
                        "worden oder von einer anderen App blockiert?"
                    )
                continue
            consecutive_failures = 0
            yield cv2.flip(frame, 1)

    def release(self):
        self.cap.release()
