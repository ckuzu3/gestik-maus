# Gestik-Maus

Systemweiter Mausersatz unter Windows per Webcam-Handtracking – bewegt den
Cursor, klickt, schaltet sich per Klatschen an/aus und steuert die
Lautstärke durch eine Dreh-Geste, ganz ohne physische Maus.

## Funktionen

- **Cursor bewegen** – der Zeigefinger steuert die Mausposition
- **Klicken** – Daumen und Mittelfinger zusammenführen (Pinch)
- **An/Aus** – beide Hände kurz zusammenklatschen schaltet die Steuerung
  komplett an oder aus (startet inaktiv, damit nichts aus Versehen passiert)
- **Lautstärke** – die Hand wie einen Regler drehen (im Uhrzeigersinn lauter,
  gegen den Uhrzeigersinn leiser)

Ein Debug-Fenster zeigt live die erkannten Hand-Landmarks, FPS, den
Pinch-Wert und den Aktiv/Inaktiv-Status.

## Voraussetzungen

- Windows
- Python 3.10–3.12
- Eine Webcam

## Installation

```
git clone https://github.com/<dein-user>/gestik-maus.git
cd gestik-maus
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Das benötigte MediaPipe-Handmodell (`hand_landmarker.task`) wird beim ersten
Start automatisch heruntergeladen.

## Verwendung

```
python main.py
```

Das Debug-Fenster mit `q` oder `ESC` schließen. Cursor in eine
Bildschirmecke bewegen (mit der physischen Maus) stoppt sofort jede
automatische Bewegung – das dient als Not-Aus.

## Bekannte Einschränkungen

- Die Dreh-Geste für Lautstärke läuft auf derselben Hand wie Cursor/Klick;
  normale Handbewegung kann in seltenen Fällen versehentlich einen
  Lautstärke-Schritt auslösen.
- Die Schwellenwerte für Klatsch- und Pinch-Erkennung (`gestures.py`) sind
  Startwerte und je nach Kamera/Abstand ggf. anzupassen.
- Noch keine Rechtsklick-, Scroll- oder Drag-Geste (siehe `CLAUDE.md` für
  die Roadmap).

## Mitentwickeln

Details zu Architektur, aktuellem Stand und nächsten Schritten stehen in
[`CLAUDE.md`](./CLAUDE.md).

## Lizenz

[MIT](./LICENSE)
