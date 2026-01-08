# BlueAntKI_Team4

Portfolio Analyzer mit KI-Integration.

---

## 🚀 Schnellstart (Empfohlen)

### macOS / Linux
1. `.env` Datei im `backend/` Ordner erstellen (siehe `.env.example`)
2. Terminal öffnen und ausführen:
```bash
./start.sh
```

### Windows
1. `.env` Datei im `backend/` Ordner erstellen (siehe `.env.example`)
2. Doppelklick auf `start.bat`

**Das war's!** Die Anwendung startet automatisch und öffnet das Frontend im Browser.

---

## 🔧 Manuelles Setup (für Entwickler)

1. Python Virtual Environment erstellen:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. `.env` Datei erstellen (siehe `.env.example`)

3. Backend starten:
```bash
python run.py
```

4. Frontend: `frontend/index.html` im Browser öffnen

---

## ❓ Fehlerbehebung

- **Python nicht gefunden**: Installiere Python 3.9+ von https://www.python.org/downloads/
- **Backend startet nicht**: Prüfe ob die `.env` Datei korrekt konfiguriert ist
- **Frontend zeigt Fehler**: Stelle sicher, dass das Backend läuft (http://localhost:8000)
