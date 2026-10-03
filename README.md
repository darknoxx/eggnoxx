# 🥚 EggNoxx

Eine minimalistische Eieruhr in Schwarz-Weiß mit Retro-Pixel-Look. Keine Farben,
keine Gradienten, keine Schnickschnacks — nur ein Pixel-Ei, das sich füllt, und
eine große Uhr aus einer 8×8-Pixelschrift.

![EggNoxx im Bereitschaftszustand](docs/screenshot-idle.png)

**Linux und macOS** (Apple Silicon und Intel) · Python 3.10+ · PySide6

## Features

- **Presets**: Weich 6:30 · Halbweich 7:00 · Hart 9:00
- **Freier Timer** mit Minuten- und Sekundeneingabe
- **Pixel-Ei**, das sich beim Kochen von unten füllt
- **Volumen-gerechter Füllstand** — das Ei wirkt gefüllt, nicht nur hoch
- **Alarm** aus einem gebündelten Signalton und blinkender Schwarz-Weiß-Invertierung des ganzen Fensters
- **Immer-im-Vordergrund** für den Blick über den Herd
- Läuft auch minimiert weiter, beim Schließen wird nachgefragt
- Läuft auf Linux und auf macOS, beide brauchen nur ein Terminal zum Starten

## Kochzeiten

Alle Presets zählen **ab dem Einlegen ins bereits kochende Wasser** — so ist
es auch in den klassischen Kochzeiten-Tabellen üblich. Das Ei ist ein
Wärmespeicher und muss erst selbst auf Temperatur kommen.

| Preset | Zeit | Dotter |
| --- | --- | --- |
| Weich | 6:30 | noch flüssig |
| Halbweich | 7:00 | dickflüssig, weich |
| Hart | 9:00 | vollständig fest |

**Aus Kaltwasser** braucht dasselbe Ergebnis etwa **3 Minuten mehr** (weich also
rund 9–10 min, hart rund 12–13 min). Die App weist während des Betriebs darauf
hin.

## Bedienung

| Taste | Funktion |
| --- | --- |
| `Leertaste` | Start / Pause |
| `R` | Reset |
| `1` `2` `3` | Preset Weich / Halbweich / Hart |
| `Alt` + `T` | Immer im Vordergrund umschalten |
| `Esc` | Beenden |

## Installation

EggNoxx läuft auf **Linux** und **macOS** (Apple Silicon und Intel). Die App
selbst ist reines Qt und lattet überall; unterschiedlich ist nur die
Installation.

### macOS

```bash
git clone https://github.com/darknoxx/eggnoxx.git ~/Vibecoding/EggNoxx
cd ~/Vibecoding/EggNoxx
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
python -m eggnoxx
```

Voraussetzung ist ein Python 3.10 oder neuer — Apple liefert keines mehr mit,
am einfachsten via Homebrew:

```bash
brew install python
```

`./install.sh` gibt es nur unter Linux. Auf dem Mac startet EggNoxx aus dem
Terminal; ein Doppelklick-Symbol im Finder wäre ein `.app`-Bundle, das es
bewusst nicht gibt.

### Linux

```bash
git clone https://github.com/darknoxx/eggnoxx.git ~/Vibecoding/EggNoxx
cd ~/Vibecoding/EggNoxx
./install.sh
```

Das Skript legt das venv an, installiert PySide6 und das Paket, erzeugt bei
Bedarf Icons und Alarmton und registriert den Desktop-Eintrag. Läuft ohne
`sudo` und fasst nichts außerhalb von `~/.local/share` an. Danach steht
EggNoxx im Anwendungsmenü und lässt sich an die Taskleiste pinnen.

Mit Entwicklungswerkzeugen (pytest, ruff):

```bash
WITH_DEV=1 ./install.sh
```

Wieder entfernen:

```bash
./install.sh --uninstall
```

<details>
<summary>Manuell statt per Skript</summary>

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python -m eggnoxx
```

Nur unter Linux dazu, um den Starter-Eintrag zu setzen:

```bash
python -m eggnoxx.desktop install
```

`eggnoxx.desktop` kennt auch `status` (nur prüfen) und `uninstall`.

</details>

## Starten

```bash
eggnoxx          # oder: python -m eggnoxx
```

## Klang

Der Alarm ist ein gebündelter Ton: zwei kurze Töne von je 0,12 s, mit weichen
Rändern gegen das Klicken. Er liegt als `eggnoxx/assets/sounds/alarm.wav` im
Paket und wird über `QSoundEffect` abgespielt, also durch den System-Mixer —
auf Linux wie auf macOS gleich.

Fehlt die Datei oder fehlt das Audio-Backend, fällt der Alarm auf den
System-Piepton zurück und läuft nie auf einen Fehler. Neu erzeugen lässt sich
der Ton mit:

```bash
python tools/make_sound.py
```

Sollte auf einem System nichts zu hören sein, liegt es am Ausgabegerät: In
Containern oder auf Dummy-Sinks (PipeWire `auto_null`) akzeptiert Qt kein
PCM. Auf einem normalen Desktop mit echter Soundkarte läuft es.

## Icons

Die Icons liegen als Pixelgrafik in den Größen 16 bis 256px plus einer
SVG-Version in `eggnoxx/assets/icons/`. Neu erzeugen:

```bash
python -m eggnoxx.icon
```

## Entwicklung

```bash
pip install -e ".[dev]"

pytest              # 69 Logik-Tests, ohne GUI
ruff check .
ruff format .

python smoke_test.py           # GUI-Test headless (offscreen) + Screenshots
python smoke_test.py --visible # Fenster wirklich anzeigen
```

### Aufbau

| Datei | Inhalt |
| --- | --- |
| `eggnoxx/core.py` | Timer-Logik ohne Qt — driftfrei über `time.monotonic()` |
| `eggnoxx/window.py` | Hauptfenster, Presets, Tastaturkürzel |
| `eggnoxx/egg.py` | Das Pixel-Ei: Form, Rasterung, Füllstand |
| `eggnoxx/panel.py` | Punktraster und Eckwinkel als Hintergrund |
| `eggnoxx/alarm.py` | Signalton und Blink-Logik |
| `eggnoxx/theme.py` | Farben und die eingebettete Pixelschrift |
| `eggnoxx/icon.py` | Erzeugt das App-Icon in allen Größen |
| `eggnoxx/desktop.py` | Desktop-Eintrag und Icons installieren (nur Linux) |
| `tools/make_sound.py` | Erzeugt `alarm.wav` |
| `install.sh` | venv, Paket, Icons und Starter-Eintrag (nur Linux) |
| `smoke_test.py` | GUI-Test headless, mit Screenshots |

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

Python 3.10 oder neuer und PySide6. Getestet mit Python 3.14 und PySide6 6.11
unter Linux sowie auf einem MacBook mit M-Chip. PySide6 liefert für macOS ein
`universal2`-Wheel, Intel und Apple Silicon laufen also beide.

Auf macOS bringt Apple kein `python3` mehr mit — siehe [Installation](#installation).