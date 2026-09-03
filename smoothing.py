"""Einfacher Exponential-Moving-Average-Filter gegen Tracking-Jitter."""


class EMAFilter:
    def __init__(self, alpha: float = 0.4):
        """alpha nahe 1.0 = kaum Glättung (reagiert schnell, mehr Zittern).
        alpha nahe 0.0 = starke Glättung (ruhiger, aber spürbare Verzögerung).
        0.3-0.5 ist ein guter Startwert für Cursor-Bewegung."""
        self.alpha = alpha
        self._value = None

    def update(self, x: float, y: float) -> tuple[float, float]:
        if self._value is None:
            self._value = (x, y)
        else:
            px, py = self._value
            self._value = (
                self.alpha * x + (1 - self.alpha) * px,
                self.alpha * y + (1 - self.alpha) * py,
            )
        return self._value

    def reset(self):
        self._value = None
