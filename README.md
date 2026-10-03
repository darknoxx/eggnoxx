# 🥚 EggNoxx

Eine minimalistische Eieruhr in Schwarz-Weiß mit Retro-Pixel-Look. Keine Farben,
keine Gradienten, keine Schnickschnacks — nur ein Pixel-Ei, das sich füllt, und
eine große Uhr aus einer 8×8-Pixelschrift.

![EggNoxx im Bereitschaftszustand](docs/screenshot-idle.png)

## Features

- **Presets**: Weich 6:30 · Wachtel 7:00 · Hart 9:00
- **Freier Timer** mit Minuten- und Sekundeneingabe
- **Pixel-Ei**, das sich beim Kochen von unten füllt
- **Volumen-gerechter Füllstand** — das Ei wirkt gefüllt, nicht nur hoch
- **Alarm** aus Signalton und blinkender Schwarz-Weiß-Invertierung des ganzen Fensters
- **Immer-im-Vordergrund** für den Blick über den Herd
- Läuft auch minimiert weiter, beim Schließen wird nachgefragt

## Bedienung

| Taste | Funktion |
| --- | --- |
| `Leertaste` | Start / Pause |
| `R` | Reset |
| `1` `2` `3` | Preset Weich / Wachtel / Hart |
| `Alt` + `T` | Immer im Vordergrund umschalten |
| `Esc` | Beenden |

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install pyside6
```

## Starten

```bash
python -m eggnoxx
```

Alternativ nach `pip install -e .` als `eggnoxx`.

## Entwicklung

```bash
pip install -e ".[dev]"

pytest              # 33 Logik-Tests, ohne GUI
ruff check .
ruff format .

python smoke_test.py           # GUI-Test headless (offscreen) + Screenshots
python smoke_test.py --visible # Fenster wirklich anzeigen
```

### Aufbau

| Datei | Inhalt |
| --- | --- |
| `eggnoxx/core.py` | Timer-Logik ohne Qt — driftfrei über `time.monotonic()` |
| `eggnoxx/theme.py` | Farben und die eingebettete Pixelschrift |
| `eggnoxx/egg.py` | Das Pixel-Ei: Form, Rasterung, Füllstand |
| `eggnoxx/panel.py` | PunktRaster und Eckwinkel als Hintergrund |
| `eggnoxx/alarm.py` | Signalton und Blink-Logik |
| `eggnoxx/window.py` | Hauptfenster, Presets, Tastaturkürzel |

Die Logik in `core.py` kommt bewusst ohne Qt aus, damit sie direkt testbar ist:
ein `Countdown` rechnet immer gegen eine Deadline, nie gegen aufsummierte
Ticks — so kann die Uhr nicht driften.

### Zwei Details, die den Unterschied machen

**Das Ei ist echte Pixelgrafik.** Die Form wird in ein kleines Raster
geschrieben und mit Nearest-Neighbour-Skaling vergrößert, statt als Vektor
gezeichnet zu werden. Deshalb sitzt die Zelle auf einer ganzen Pixelzahl und
flimmert beim Skalieren nicht.

**Der Füllstand folgt der Fläche, nicht der Höhe.** Die Zeit läuft linear, das
Auge liest das Ei aber als Gefäß: Eine lineare Höhenrampe ließe es nach oben
rennen und dann zäh kriechen. `fill_height()` bildet deshalb über die
kumulative Querschnittsfläche ab, damit die Steigung gleichmäßig wirkt.

## Schrift

**Silkscreen** von Jason Kottke, SIL Open Font License 1.1. Die OFL liegt bei
`eggnoxx/assets/fonts/OFL.txt`. Fehlen die Dateien, fällt die App automatisch auf
die System-Monospace-Schrift zurück.

## Anforderungen

Python 3.10+ und PySide6 (getestet mit Python 3.14 und PySide6 6.11).