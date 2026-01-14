#!/bin/bash

# ============================================
# BlueAnt Portfolio Analyzer - Startskript
# Für macOS / Linux
# ============================================

# Farben für bessere Lesbarkeit
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Aktuelles Verzeichnis des Skripts ermitteln
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

echo ""
echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}   BlueAnt Portfolio Analyzer${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Prüfen ob Python installiert ist
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Fehler: Python3 ist nicht installiert!${NC}"
    echo "Bitte installiere Python 3.13 von https://www.python.org/downloads/"
    echo ""
    read -p "Drücke Enter zum Beenden..."
    exit 1
fi

# Python-Version prüfen (mindestens 3.13)
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || { [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 13 ]; }; then
    echo -e "${RED}❌ Fehler: Python 3.13 oder höher wird benötigt!${NC}"
    echo "Installierte Version: $PYTHON_VERSION"
    echo "Bitte installiere Python 3.13 von https://www.python.org/downloads/"
    echo ""
    read -p "Drücke Enter zum Beenden..."
    exit 1
fi

echo -e "${GREEN}✓ Python $PYTHON_VERSION gefunden${NC}"

# Ins Backend-Verzeichnis wechseln
cd "$BACKEND_DIR" || {
    echo -e "${RED}❌ Fehler: Backend-Verzeichnis nicht gefunden!${NC}"
    read -p "Drücke Enter zum Beenden..."
    exit 1
}

# Prüfen ob Virtual Environment existiert
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚙ Virtual Environment wird erstellt...${NC}"
    python3 -m venv venv
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Fehler beim Erstellen des Virtual Environment!${NC}"
        read -p "Drücke Enter zum Beenden..."
        exit 1
    fi
    echo -e "${GREEN}✓ Virtual Environment erstellt${NC}"
fi

# Virtual Environment aktivieren
echo -e "${YELLOW}⚙ Virtual Environment wird aktiviert...${NC}"
source venv/bin/activate

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Fehler beim Aktivieren des Virtual Environment!${NC}"
    read -p "Drücke Enter zum Beenden..."
    exit 1
fi
echo -e "${GREEN}✓ Virtual Environment aktiviert${NC}"

# Abhängigkeiten installieren (falls nötig)
echo -e "${YELLOW}⚙ Abhängigkeiten werden geprüft...${NC}"
pip install -r requirements.txt -q

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Fehler beim Installieren der Abhängigkeiten!${NC}"
    read -p "Drücke Enter zum Beenden..."
    exit 1
fi
echo -e "${GREEN}✓ Abhängigkeiten installiert${NC}"

# Prüfen ob .env existiert
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠ Hinweis: Keine .env Datei gefunden.${NC}"
    echo -e "${YELLOW}  Bitte erstelle eine .env Datei basierend auf .env.example${NC}"
    echo ""
fi

# Backend im Hintergrund starten
echo ""
echo -e "${YELLOW}⚙ Backend wird gestartet...${NC}"
python run.py &
BACKEND_PID=$!

# Kurz warten, damit der Server hochfahren kann
sleep 3

# Prüfen ob Backend läuft
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo -e "${RED}❌ Fehler: Backend konnte nicht gestartet werden!${NC}"
    echo "Prüfe die Konsole auf Fehlermeldungen."
    read -p "Drücke Enter zum Beenden..."
    exit 1
fi

echo -e "${GREEN}✓ Backend läuft (PID: $BACKEND_PID)${NC}"

# Frontend-Server starten
echo ""
echo -e "${YELLOW}⚙ Frontend-Server wird gestartet...${NC}"
cd "$FRONTEND_DIR" || {
    echo -e "${RED}❌ Fehler: Frontend-Verzeichnis nicht gefunden!${NC}"
    kill $BACKEND_PID 2>/dev/null
    read -p "Drücke Enter zum Beenden..."
    exit 1
}

# Python HTTP-Server für Frontend starten (Port 3000)
python3 -m http.server 3000 --bind 127.0.0.1 &
FRONTEND_PID=$!

# Kurz warten, damit der Frontend-Server hochfahren kann
sleep 2

# Prüfen ob Frontend-Server läuft
if ! kill -0 $FRONTEND_PID 2>/dev/null; then
    echo -e "${RED}❌ Fehler: Frontend-Server konnte nicht gestartet werden!${NC}"
    kill $BACKEND_PID 2>/dev/null
    read -p "Drücke Enter zum Beenden..."
    exit 1
fi

echo -e "${GREEN}✓ Frontend-Server läuft (PID: $FRONTEND_PID)${NC}"

# Browser öffnen mit URL
echo ""
echo -e "${YELLOW}⚙ Browser wird geöffnet...${NC}"
sleep 1

FRONTEND_URL="http://localhost:3000"

# Browser öffnen (macOS)
if command -v open &> /dev/null; then
    open "$FRONTEND_URL"
# Linux
elif command -v xdg-open &> /dev/null; then
    xdg-open "$FRONTEND_URL"
else
    echo -e "${YELLOW}⚠ Browser konnte nicht automatisch geöffnet werden.${NC}"
    echo "Bitte öffne manuell: $FRONTEND_URL"
fi

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}   ✓ Anwendung erfolgreich gestartet!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo -e "Backend läuft auf:  ${BLUE}http://localhost:8000${NC}"
echo -e "Frontend läuft auf: ${BLUE}http://localhost:3000${NC}"
echo ""
echo -e "${YELLOW}Zum Beenden: Drücke Ctrl+C${NC}"
echo ""

# Auf Benutzer-Interrupt warten und dann beide Server beenden
cleanup() {
    echo ""
    echo -e "${YELLOW}⚙ Anwendung wird beendet...${NC}"
    kill $FRONTEND_PID 2>/dev/null
    echo -e "${GREEN}✓ Frontend-Server gestoppt${NC}"
    kill $BACKEND_PID 2>/dev/null
    echo -e "${GREEN}✓ Backend gestoppt${NC}"
    echo ""
    exit 0
}

trap cleanup SIGINT SIGTERM

# Warten bis einer der Prozesse beendet wird
wait $BACKEND_PID $FRONTEND_PID

