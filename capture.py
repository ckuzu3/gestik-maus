"""Webcam-Capture: liefert gespiegelte BGR-Frames als Generator.

Als Quelle geht neben einem Kamera-Index (Normalfall) auch der Pfad zu einer
Videodatei. Das ist der einzige Weg, den kompletten main.py-Loop auf einem
Rechner ohne Webcam durchlaufen zu lassen (z. B. in einer CI-/Container-
Umgebung) - fuer die eigentliche Nutzung bleibt der Kamera-Index gemeint.
"""

import sys

import cv2


def _backend_for(source):
    """DirectShow gibt es nur unter Windows; auf Linux/macOS scheitert
    VideoCapture mit CAP_DSHOW sofort. Fuer Videodateien ist DirectShow
    ohnehin der falsche Backend."""
    if sys.platform == "win32" and isinstance(source, int):
        return cv2.CAP_DSHOW
    return cv2.CAP_ANY


class Camera:
    def __init__(self, source=0, width: int = 1280, height: int = 720):
        """source: Kamera-Index (int) oder Pfad zu einer Videodatei (str)."""
        self.source = source
        self.is_live = isinstance(source, int)
        self.cap = cv2.VideoCapture(source, _backend_for(source))
        if self.is_live:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        if not self.cap.isOpened():
            if self.is_live:
                raise RuntimeError(
                    f"Konnte Webcam mit Index {source} nicht öffnen. "
                    "Ist eine andere App gerade auf die Kamera zu?"
                )
            raise RuntimeError(f"Konnte Videodatei nicht öffnen: {source}")

    def frames(self):
        """Generator: liefert horizontal gespiegelte BGR-Frames (Spiegel-Effekt,
        fühlt sich vor der Kamera natürlicher an als unmodifiziert).

        Ein einzelner fehlgeschlagener Frame-Read (kommt bei manchen
        Webcam-Treibern gelegentlich vor) wird übersprungen statt das ganze
        Programm abstürzen zu lassen. Erst nach vielen Fehlversuchen am
        Stück gilt die Kamera als wirklich getrennt. Bei einer Videodatei
        bedeutet ein fehlgeschlagener Read dagegen schlicht 'Video zu Ende',
        der Generator endet dann normal."""
        consecutive_failures = 0
        while True:
            ok, frame = self.cap.read()
            if not ok:
                if not self.is_live:
                    return
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
