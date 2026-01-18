# BlueAnt Portfolio Analyzer

KI-gestützter Portfolio Analyzer für BlueAnt Projektdaten.

---

## Installation

### Option 1: Docker (Empfohlen)

Die einfachste Methode - keine lokale Installation von Python oder Dependencies nötig.

**Voraussetzungen:** [Docker Desktop](https://www.docker.com/products/docker-desktop/) installiert

**1. `docker-compose.yml` Datei erstellen:**

```yaml
version: '3.8'

services:
  backend:
    image: maxbudde/blueant-backend:latest
    container_name: blueant-backend
    restart: unless-stopped
    expose:
      - "8000"
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    networks:
      - blueant-network

  frontend:
    image: maxbudde/blueant-frontend:latest
    container_name: blueant-frontend
    restart: unless-stopped
    ports:
      - "80:80"
    depends_on:
      backend:
        condition: service_healthy
    networks:
      - blueant-network

networks:
  blueant-network:
    driver: bridge
```

**2. Anwendung starten:**

```bash
docker-compose up -d
```

**3. Im Browser öffnen:**

```
http://localhost
```

**4. Anwendung stoppen:**

```bash
docker-compose down
```

**5. Updates holen:**

```bash
docker-compose pull
docker-compose up -d
```

---

### Option 2: Lokale Installation

#### macOS / Linux

1. Terminal öffnen und ausführen:
```bash
./start.sh
```

#### Windows

1. Doppelklick auf `start.bat`

**Das war's!** Die Anwendung startet automatisch und öffnet das Frontend im Browser.

---

### Option 3: Manuelles Setup (für Entwickler)

1. Python Virtual Environment erstellen:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. Backend starten:
```bash
python run.py
```

3. Frontend: `frontend/index.html` im Browser öffnen

---

## Konfiguration

**Keine `.env`-Datei erforderlich!**

Alle API-Keys werden direkt im Frontend eingegeben:
- BlueAnt URL
- BlueAnt API-Key
- Gemini API-Key

Die eingegebenen Keys werden nur für die aktuelle Session verwendet und nicht gespeichert.

---

## Fehlerbehebung

| Problem | Lösung |
|---------|--------|
| Docker: Container startet nicht | `docker-compose logs` prüfen |
| Docker: Port 80 belegt | In `docker-compose.yml` Port ändern: `"8080:80"` |
| Python nicht gefunden | Python 3.9+ installieren: https://python.org |
| Backend startet nicht | Prüfen ob Port 8000 frei ist |
| Frontend zeigt Fehler | Backend muss laufen (http://localhost:8000) |

---

## Docker Images

Die Docker Images sind öffentlich verfügbar:

- Backend: `maxbudde/blueant-backend:latest`
- Frontend: `maxbudde/blueant-frontend:latest`

Docker Hub: https://hub.docker.com/u/maxbudde
