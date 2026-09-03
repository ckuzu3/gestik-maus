"""Mapping Kamera-Koordinaten -> Bildschirmkoordinaten + Cursor bewegen."""

import pyautogui

# Failsafe bewusst an: Maus in eine Bildschirmecke bewegen (mit der
# physischen Maus) bricht jede automatische Bewegung sofort ab. Das ist
# der Not-Aus, solange es noch keine eigene Abbruch-Geste gibt.
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0  # keine künstliche Verzögerung nach jedem Aufruf

# Aktive Zone im Kamerabild (normiert), die auf den vollen Bildschirm
# gemappt wird. Verhindert, dass man bis an den Rand des Kamerabilds
# greifen muss, um die Bildschirmränder zu erreichen.
ACTIVE_ZONE = (0.15, 0.15, 0.85, 0.85)  # (x_min, y_min, x_max, y_max)

# Abstand (px), den der automatisch gesetzte Cursor mindestens von den
# Bildschirmecken haelt. Ohne das wuerde die Handbewegung selbst irgendwann
# exakt (0,0) treffen und pyautoguis FAILSAFE ausloesen (siehe unten) - der
# Not-Aus wuerde sich also versehentlich selbst ausloesen, statt nur auf die
# physische Maus zu reagieren.
_CORNER_MARGIN = 3


def _remap(value: float, in_min: float, in_max: float) -> float:
    value = max(in_min, min(in_max, value))
    return (value - in_min) / (in_max - in_min)


class MouseController:
    def __init__(self):
        self.screen_w, self.screen_h = pyautogui.size()

    def move_to_normalized(self, x: float, y: float):
        """x, y: normierte Koordinaten (0..1) aus dem Kamerabild."""
        x_min, y_min, x_max, y_max = ACTIVE_ZONE
        nx = _remap(x, x_min, x_max)
        ny = _remap(y, y_min, y_max)
        screen_x = nx * self.screen_w
        screen_y = ny * self.screen_h
        screen_x = min(max(screen_x, _CORNER_MARGIN), self.screen_w - 1 - _CORNER_MARGIN)
        screen_y = min(max(screen_y, _CORNER_MARGIN), self.screen_h - 1 - _CORNER_MARGIN)
        pyautogui.moveTo(screen_x, screen_y, _pause=False)

    def click(self):
        pyautogui.click(_pause=False)
