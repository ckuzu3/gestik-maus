# Gestik-Maus

Systemweiter Mausersatz unter Windows per Webcam-Handtracking (MediaPipe).
Ziel: Cursor bewegen, klicken, scrollen und ziehen ausschließlich per
Handgeste vor der Webcam.

## Tech-Stack

- Python 3.10–3.12
- OpenCV (`opencv-python`) – Webcam-Capture
- MediaPipe (`mediapipe`, Tasks API `HandLandmarker`) – Hand-Landmark-Erkennung.
  Wichtig: die alte `mp.solutions.hands`-API existiert in aktuellen
  mediapipe-Versionen nicht mehr (weder als Attribut noch als
  `mediapipe.python.solutions`-Submodul) – nur die neue Tasks API
  funktioniert noch. Braucht eine Modell-Datei `hand_landmarker.task`,
  die `tracker.py` beim ersten Start automatisch herunterlädt.
- `pyautogui` – systemweite Cursor-/Klick-Steuerung und Lautstärke
  (Medientasten) unter Windows

## Projektstruktur

- `capture.py` – Webcam öffnen, Frames liefern (gespiegelt für natürliches Gefühl)
- `tracker.py` – MediaPipe-Wrapper: Frame → Liste erkannter Hände (je 21
  Landmarks, normiert 0–1)
- `smoothing.py` – Exponentieller gleitender Durchschnitt gegen Jitter
- `gestures.py` – Gesten-Klassifikation auf Basis von Landmark-Listen:
  - `ClickGesture`/`pinch_ratio` – Pinch Daumen+Mittelfinger = Klick
  - `ClapDetector` – zwei Hände schnell zusammen = Klatschen
  - `RotationVolumeControl` – Handgelenk drehen = Lautstärke-Schritte
- `mouse_control.py` – Mapping Kamera-Koordinaten → Bildschirmkoordinaten,
  Cursor bewegen/klicken
- `volume_control.py` – Systemlautstärke über Medientasten
- `main.py` – Haupt-Loop, verbindet alles, zeigt Debug-Overlay

## Aktueller Stand (Schritt 3)

- Cursor-Bewegung per Zeigefingerspitze (fertig)
- Linksklick per Pinch-Geste (Daumen + Mittelfinger — bewusst nicht der
  Zeigefinger, da der sonst gleichzeitig den Cursor bewegen würde).
  `ClickGesture` löst genau einen Klick pro Pinch aus (kein Dauerfeuer beim
  Halten), Schwelle auf Handspanne normiert (kameraabstands-unabhängig).
- Klatschen (beide Hände im Bild schnell zusammenschlagen) schaltet die
  gesamte Steuerung an/aus (`ClapDetector`, braucht beide Hände gleichzeitig
  im Kamerabild). Programm startet bewusst INAKTIV, damit der Cursor nicht
  gleich beim Start oder aus Versehen loslegt.
- Hand wie einen Regler drehen (Handgelenkwinkel) ändert die Lautstärke in
  festen Schritten (`RotationVolumeControl`, alle 15° ein Schritt). Läuft auf
  derselben Hand wie Cursor/Klick — Achtung, siehe bekannte Einschränkung
  unten.
- Debug-Fenster zeigt: FPS, Pinch-Status, Aktiv/Inaktiv-Status (unten links),
  Skelett aller erkannten Hände.
- Noch **keine** Rechtsklick-/Scroll-/Drag-Gesten.

## Bekannte Einschränkungen / offene Fragen

- Die Dreh-Geste für Lautstärke nutzt denselben Winkel (Handgelenk →
  Mittelfinger-Basis) unabhängig von reiner Handbewegung. Normales
  Verschieben der Hand beim Zeigen kann die Handausrichtung leicht mit
  verändern und theoretisch ungewollt einen Lautstärke-Schritt auslösen.
  Falls das beim Testen stört: Schwelle (`DEGREES_PER_STEP` in
  `gestures.py`) erhöhen, oder Dreh-Geste an eine eigene Handpose koppeln
  (z. B. nur wenn die Hand zur Faust geschlossen ist).
- `ClapDetector`-Schwellen (`APART_THRESHOLD`/`TOUCH_THRESHOLD` in
  `gestures.py`) sind ungetestete Startwerte und müssen wahrscheinlich an
  Kamera-Auflösung/-Abstand angepasst werden.
- Welche der zwei Hände beim Klatschen `hands[0]` wird (und damit die
  Cursor-Hand ist), ist nicht deterministisch, wenn zwischenzeitlich beide
  Hände im Bild sind.

## Ausführen

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Debug-Fenster mit `q` oder `ESC` schließen. Cursor in eine Bildschirmecke
bewegen (physische Maus) löst `pyautogui`s Failsafe aus und stoppt sofort
jede automatische Bewegung – das ist der Not-Aus. Einmal klatschen (beide
Hände kurz zusammenschlagen) aktiviert/pausiert die Steuerung.

## Nächste Schritte (nicht Teil dieses Commits)

1. Klatsch- und Dreh-Schwellen anhand von echtem Testfeedback justieren
2. Zweite Pinch-Variante (Daumen + Zeigefinger, während Zeigefinger kurz
   nicht als Cursor zählt) oder eigene Handpose → Rechtsklick
3. Faust halten → Drag (Mouse-Down bis Faust gelöst wird)
4. Zwei-Finger-Bewegung vertikal → Scrollen
5. Tray-Icon (`pystray`) + Autostart + PyInstaller-Packaging

Bitte jeweils **eine** Erweiterung pro Änderung umsetzen und danach manuell
vor der Kamera testen lassen (automatisiertes Testen ist hier nicht möglich)
statt mehrere Gesten auf einmal einzubauen.
