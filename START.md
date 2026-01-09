# 🚀 Projekt Start-Anleitung

## Schnellstart

### 1. Backend starten

```bash
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate
python run.py
```

Das Backend läuft dann auf: **http://localhost:8000**

### 2. Frontend starten

In einem **neuen Terminal**:

```bash
cd frontend
python3 -m http.server 3000
```

Das Frontend läuft dann auf: **http://localhost:3000**

## 📋 Vollständiges Setup (nur beim ersten Mal)

### Schritt 1: Virtual Environment erstellen

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### Schritt 2: Dependencies installieren

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Schritt 3: .env Datei konfigurieren

Die `.env` Datei sollte im Projekt-Root existieren. Falls nicht, kopiere `.env.example` zu `.env` und trage deine API-Keys ein:

```bash
# Im Projekt-Root
cp .env.example .env
# Dann .env bearbeiten und API-Keys eintragen
```

Erforderliche Variablen:
- `BLUEANT_API_KEY` - Dein BlueAnt API Key
- `GEMINI_API_KEY` - Dein Google Gemini API Key

## 🎯 URLs nach dem Start

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Dokumentation (Swagger)**: http://localhost:8000/docs
- **API Dokumentation (ReDoc)**: http://localhost:8000/redoc

## 🛑 Server stoppen

Drücke `Ctrl+C` in den Terminal-Fenstern, in denen die Server laufen.

Oder per Kommando:
```bash
# Backend stoppen (Port 8000)
lsof -ti:8000 | xargs kill

# Frontend stoppen (Port 3000)
lsof -ti:3000 | xargs kill
```

## ✅ Prüfen ob alles läuft

### Backend Health Check:
```bash
curl http://localhost:8000/health
```

### Frontend öffnen:
Öffne im Browser: http://localhost:3000

## 🔧 Troubleshooting

### Problem: "ModuleNotFoundError"
→ Virtual Environment nicht aktiviert
```bash
cd backend
source venv/bin/activate
```

### Problem: Port bereits belegt
→ Anderen Port verwenden oder bestehenden Prozess beenden
```bash
# Prozess finden
lsof -i :8000
# Prozess beenden
kill <PID>
```

### Problem: ".env file not found"
→ .env Datei im Projekt-Root erstellen (siehe Schritt 3)

## 📝 Hinweise

- Backend und Frontend müssen **gleichzeitig** laufen
- Backend läuft auf Port **8000**
- Frontend läuft auf Port **3000**
- Das Frontend kommuniziert mit dem Backend über `http://localhost:8000`

