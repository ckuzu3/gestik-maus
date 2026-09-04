"""Prueft die Gesten-Logik aus gestures.py mit synthetischen Landmarks.

Laeuft ohne Webcam und ohne Bildschirm - das ist der einzige Teil des
Projekts, der sich automatisiert testen laesst. Alles was mit Kamera,
Cursor oder Debug-Fenster zu tun hat, muss weiterhin von Hand vor der
Kamera geprueft werden.

    python test_gestures.py
"""
import math
from types import SimpleNamespace as P

from gestures import ClapDetector, ClickGesture, RotationVolumeControl, pinch_ratio

def hand(cx=0.5, cy=0.5, angle_deg=90.0, pinch=0.5, span=0.2):
    """21 Landmarks: Handgelenk in (cx,cy), Mittelfinger-Basis um `angle_deg`
    gedreht im Abstand `span`, Daumen-/Mittelfinger-Spitze `pinch*span` weit
    auseinander."""
    a = math.radians(angle_deg)
    lms = [P(x=cx, y=cy, z=0.0) for _ in range(21)]
    lms[0] = P(x=cx, y=cy, z=0.0)                                    # WRIST
    lms[9] = P(x=cx + span*math.cos(a), y=cy + span*math.sin(a), z=0.0)  # MIDDLE_MCP
    lms[4] = P(x=cx, y=cy - span, z=0.0)                             # THUMB_TIP
    lms[12] = P(x=cx + pinch*span, y=cy - span, z=0.0)               # MIDDLE_TIP
    return lms

ok = True
def check(name, cond):
    global ok
    ok = ok and cond
    print(("PASS  " if cond else "FAIL  ") + name)

# --- Pinch / Klick ---
check("pinch_ratio offen  > Schwelle", pinch_ratio(hand(pinch=0.8)) > 0.35)
check("pinch_ratio zu     < Schwelle", pinch_ratio(hand(pinch=0.1)) < 0.35)

cg = ClickGesture()
clicks = [cg.update(hand(pinch=p)) for p in (0.8, 0.1, 0.1, 0.1, 0.8, 0.1)]
check("genau 1 Klick pro Pinch (kein Dauerfeuer)", clicks == [False, True, False, False, False, True])

# --- Klatschen ---
cd = ClapDetector()
seq = [(0.9, 100.0), (0.05, 100.1), (0.05, 100.2), (0.9, 100.3), (0.05, 100.35), (0.9, 101.5), (0.05, 101.6)]
claps = [cd.update([hand(cx=0.5-d/2), hand(cx=0.5+d/2)], t) for d, t in seq]
check("Klatschen erkannt, Cooldown greift", claps == [False, True, False, False, False, False, True])
check("eine Hand allein loest nichts aus", cd.update([hand()], 5.0) is False)

# --- Lautstaerke-Drehung ---
rv = RotationVolumeControl()
rv.update(hand(angle_deg=90))
steps_up = [rv.update(hand(angle_deg=90 + d)) for d in (5, 10, 16, 20, 32)]
check("Drehung im Uhrzeigersinn -> +1-Schritte", sum(s for s in steps_up if s > 0) == 2 and all(s >= 0 for s in steps_up))
rv2 = RotationVolumeControl()
rv2.update(hand(angle_deg=90))
steps_dn = [rv2.update(hand(angle_deg=90 - d)) for d in (5, 10, 16, 20, 32)]
check("Drehung gegen den Uhrzeigersinn -> -1-Schritte", sum(1 for s in steps_dn if s < 0) == 2)
rv3 = RotationVolumeControl()
rv3.update(hand(angle_deg=90))
check("Zittern (<15 Grad) loest keinen Schritt aus", all(rv3.update(hand(angle_deg=90 + d)) == 0 for d in (2, -3, 4, -1)))

print("\nALLES OK" if ok else "\nES GAB FEHLER")
raise SystemExit(0 if ok else 1)
