#!/usr/bin/env bash
#
# EggNoxx installieren: venv anlegen, Abhängigkeiten holen, Icons erzeugen,
# Desktop-Eintrag registrieren.
#
#   ./install.sh              # installieren
#   ./install.sh --uninstall  # wieder entfernen (Desktop-Eintrag und Icons)
#
# Läuft ohne sudo und fasst nichts außerhalb von ~/.local/share an.

set -euo pipefail

PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_DIR/.venv"
PYTHON="${PYTHON:-python3}"
MIN_PYTHON="3.10"

bold() { printf '\033[1m%s\033[0m\n' "$1"; }
info() { printf '  %s\n' "$1"; }
fail() { printf '\033[1mFehler: %s\033[0m\n' "$1" >&2; exit 1; }

check_python() {
    command -v "$PYTHON" >/dev/null 2>&1 || fail "$PYTHON nicht gefunden."
    "$PYTHON" -c "import sys; sys.exit(0 if sys.version_info >= tuple(map(int, '$MIN_PYTHON'.split('.'))) else 1)" \
        || fail "Python $MIN_PYTHON oder neuer noetig (gefunden: $("$PYTHON" -V 2>&1))."
}

create_venv() {
    [ -d "$VENV_DIR" ] || {
        info "venv wird angelegt ..."
        "$PYTHON" -m venv "$VENV_DIR"
    }
    "$VENV_DIR/bin/python" -m pip install --quiet --upgrade pip
}

install_project() {
    info "Abhaengigkeiten werden installiert (PySide6, das dauert einen Moment) ..."
    # Optionale Gruppe mit pytest/ruff: nur sinnvoll, wenn wirklich entwickelt
    # wird, deshalb nicht Teil der Standardinstallation.
    if [ "${WITH_DEV:-0}" = "1" ]; then
        "$VENV_DIR/bin/pip" install --quiet -e "$PROJECT_DIR[dev]"
    else
        "$VENV_DIR/bin/pip" install --quiet -e "$PROJECT_DIR"
    fi
}

generate_assets() {
    # Icons und Ton liegen im Repo; nur neu erzeugen, wenn sie fehlen.
    if [ ! -f "$PROJECT_DIR/eggnoxx/assets/icons/128x128.png" ]; then
        info "Icons werden erzeugt ..."
        QT_QPA_PLATFORM=offscreen "$VENV_DIR/bin/python" -m eggnoxx.icon >/dev/null
    fi
    if [ ! -f "$PROJECT_DIR/eggnoxx/assets/sounds/alarm.wav" ]; then
        info "Alarmton wird erzeugt ..."
        "$VENV_DIR/bin/python" "$PROJECT_DIR/tools/make_sound.py" >/dev/null
    fi
}

install_desktop() {
    info "Desktop-Eintrag wird registriert ..."
    "$VENV_DIR/bin/python" -m eggnoxx.desktop install
}

uninstall() {
    if [ -x "$VENV_DIR/bin/python" ]; then
        "$VENV_DIR/bin/python" -m eggnoxx.desktop uninstall || true
    else
        bold "Kein venv gefunden - Desktop-Eintrag bitte von Hand entfernen:"
        info "~/.local/share/applications/eggnoxx.desktop"
        info "~/.local/share/icons/hicolor/*/apps/eggnoxx.png"
    fi
    [ -d "$VENV_DIR" ] && bold "venv bleibt erhalten ($VENV_DIR) - fuer ein vollstaendiges"
    [ -d "$VENV_DIR" ] && info "Entfernen: rm -rf $VENV_DIR"
    return 0
}

usage() {
    cat <<EOF
EggNoxx Installation

  ./install.sh              venv anlegen, Paket installieren, Starter-Eintrag setzen
  ./install.sh --uninstall  Desktop-Eintrag und Icons wieder entfernen

Umgebungsvariablen:
  PYTHON    Python fuer das venv (Vorgabe: python3)
  WITH_DEV  1 installiert zusaetzlich pytest und ruff

Beispiele:
  WITH_DEV=1 ./install.sh    # inklusive Test- und Lint-Werkzeugen
EOF
}

main() {
    case "${1:-}" in
        --uninstall)
            uninstall
            return 0
            ;;
        -h | --help)
            usage
            return 0
            ;;
        "")
            ;;
        *)
            fail "Unbekanntes Argument: $1 (siehe ./install.sh --help)"
            ;;
    esac

    bold "EggNoxx wird installiert"
    check_python
    create_venv
    install_project
    generate_assets
    install_desktop

    echo
    bold "Fertig."
    info "Starten:        $VENV_DIR/bin/eggnoxx"
    info "Im Starter:    nach 'EggNoxx' suchen"
    info "Neu installieren: $VENV_DIR/bin/pip install -e ."
    echo
    info "Taucht EggNoxx nicht sofort im Starter auf, einmal ab- und anmelden -"
    info "das ist der Icon-Cache der Desktop-Umgebung."
}

main "$@"