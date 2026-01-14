@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: ============================================
:: BlueAnt Portfolio Analyzer - Startskript
:: Für Windows
:: ============================================

title BlueAnt Portfolio Analyzer

echo.
echo ============================================
echo    BlueAnt Portfolio Analyzer
echo ============================================
echo.

:: Aktuelles Verzeichnis des Skripts ermitteln
set "SCRIPT_DIR=%~dp0"
set "BACKEND_DIR=%SCRIPT_DIR%backend"
set "FRONTEND_DIR=%SCRIPT_DIR%frontend"

:: Prüfen ob Python installiert ist
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [FEHLER] Python ist nicht installiert!
    echo Bitte installiere Python von https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo [OK] Python gefunden

:: Ins Backend-Verzeichnis wechseln
cd /d "%BACKEND_DIR%"
if %errorlevel% neq 0 (
    echo [FEHLER] Backend-Verzeichnis nicht gefunden!
    pause
    exit /b 1
)

:: Prüfen ob Virtual Environment existiert
if not exist "venv" (
    echo [INFO] Virtual Environment wird erstellt...
    python -m venv venv
    
    if %errorlevel% neq 0 (
        echo [FEHLER] Virtual Environment konnte nicht erstellt werden!
        pause
        exit /b 1
    )
    echo [OK] Virtual Environment erstellt
)

:: Virtual Environment aktivieren
echo [INFO] Virtual Environment wird aktiviert...
call venv\Scripts\activate.bat

if %errorlevel% neq 0 (
    echo [FEHLER] Virtual Environment konnte nicht aktiviert werden!
    pause
    exit /b 1
)
echo [OK] Virtual Environment aktiviert

:: Abhängigkeiten installieren
echo [INFO] Abhängigkeiten werden geprueft...
pip install -r requirements.txt -q

if %errorlevel% neq 0 (
    echo [FEHLER] Abhängigkeiten konnten nicht installiert werden!
    pause
    exit /b 1
)
echo [OK] Abhängigkeiten installiert

:: Prüfen ob .env existiert
if not exist ".env" (
    echo.
    echo [WARNUNG] Keine .env Datei gefunden.
    echo           Bitte erstelle eine .env Datei basierend auf .env.example
    echo.
)

:: Frontend-Server im Hintergrund starten
echo.
echo [INFO] Frontend-Server wird gestartet...
start "BlueAnt Frontend Server" cmd /c "cd /d "%FRONTEND_DIR%" && python -m http.server 3000"

:: Kurz warten damit Frontend-Server starten kann
timeout /t 2 /nobreak >nul

:: Browser öffnen
echo [INFO] Browser wird geoeffnet...
start "" "http://localhost:3000"

:: Backend starten
echo.
echo [INFO] Backend wird gestartet...
echo.
echo ============================================
echo    Anwendung erfolgreich gestartet!
echo ============================================
echo.
echo Backend laeuft auf: http://localhost:8000
echo Frontend laeuft auf: http://localhost:3000
echo.
echo Zum Beenden: Schliesse dieses Fenster oder druecke Ctrl+C
echo              (Frontend-Server muss separat geschlossen werden)
echo.
echo ============================================
echo    Backend Log:
echo ============================================
echo.

:: Backend starten (blockiert bis Benutzer beendet)
python run.py

:: Falls Backend beendet wird
echo.
echo [INFO] Backend wurde beendet.
pause

