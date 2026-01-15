# Feedback-Umsetzungsplan
## Priorisiert nach Dringlichkeit und Wichtigkeit

---

## 🔴 PRIORITÄT 0 (KRITISCH) - Bugs die Funktionalität beeinträchtigen

### 1. TTS Stop-Button Bug
**Problem:** Der Stop-Knopf bei Vorlesen geht nicht aus  
**Datei:** `frontend/js/ui.js`  
**Lösung:** `stopSpeech()` Funktion prüfen, Button-State korrekt zurücksetzen  
**Aufwand:** ~30 Min

### 2. Kritikalitäts-Erkennung fehlerhaft
**Problem:** Projekte mit 0% Fortschritt und 0 Meilensteinen werden nicht als kritisch erkannt
- "IT-Sicherheitsinitiative Zero-Trust" → sollte kritisch sein
- "Werk2-Maschinenverlagerung" → sollte kritisch sein  
**Datei:** `backend/app/services/normalizer.py`, `backend/app/services/sanity_validator.py`  
**Lösung:** Logik erweitern: Wenn `progress_percent == 0` UND `milestones_completed == 0` UND nicht abgeschlossen → als kritisch markieren  
**Aufwand:** ~1-2h

### 3. Identische Inhalte bei DATEN-FEHLER Projekten
**Problem:** 
- "IT-Sicherheitsinitiative Zero-Trust [DATEN-FEHLER]" und "Werk2-Maschinenverlagerung [DATEN-FEHLER]" haben identische Inhalte
- "CRM-System Migration [DATEN-FEHLER]" und "Digitale Dokumentenverwaltung [DATEN-FEHLER]" haben identische Inhalte  
**Datei:** `backend/app/ai/prompts.py`, `backend/app/ai/gemini.py`  
**Lösung:** Prüfen ob LLM für DATEN-FEHLER Projekte Fallback-Text verwendet. Sicherstellen dass projektspezifische Daten verwendet werden  
**Aufwand:** ~2-3h

### 4. Text abgeschnitten in Executive Summary (PPTX)
**Problem:** Executive Summary Text ist in PPTX abgeschnitten  
**Datei:** `backend/app/services/pptx_builder.py`  
**Lösung:** Text-Länge prüfen, Textumbruch/Scrollbox implementieren  
**Aufwand:** ~1h

### 5. "[ABGESCHLOSSEN]en" Textfehler
**Problem:** Falsche Grammatik bei abgeschlossenen Projekten  
**Datei:** `backend/app/services/pptx_builder.py` (Zeile 804)  
**Lösung:** "[ABGESCHLOSSEN]" statt "[ABGESCHLOSSEN]en"  
**Aufwand:** ~5 Min

---

## 🟠 PRIORITÄT 1 (HOCH) - Wichtige UX/UI Verbesserungen

### 6. [KRITISCH] als Tag statt Text
**Problem:** "[KRITISCH]" sollte als visueller Tag/Badge dargestellt werden, nicht als Text  
**Datei:** `frontend/js/ui.js` (Zeile 379), `frontend/styles/components.css`  
**Lösung:** CSS-Badge-Komponente erstellen, ähnlich wie `project-status`  
**Aufwand:** ~1h

### 7. [DATEN-FEHLER] als Tag mit Erklärung
**Problem:** "[DATEN-FEHLER]" sollte als Tag dargestellt werden mit Tooltip/Erklärung  
**Datei:** `frontend/js/ui.js`, `backend/app/services/pptx_builder.py`  
**Lösung:** 
- Frontend: Tag-Komponente mit Tooltip "Daten-Inkonsistenz erkannt: Projekt als abgeschlossen markiert, aber keine Meilensteine erreicht"
- PPTX: Tag-ähnliche Darstellung  
**Aufwand:** ~1-2h

### 8. Sortierung nach Kritikalität statt alphabetisch
**Problem:** Zusammenfassung ist alphabetisch sortiert → sollte nach kritisch → wenig kritisch sortiert werden  
**Datei:** `frontend/js/ui.js` (Zeile 291)  
**Lösung:** `project_scores` sortieren nach: `is_critical` → `priority_score` (descending)  
**Aufwand:** ~30 Min

### 9. Farbcodierung (gray/green/yellow) passt nicht zu Sicherheitsstufe
**Problem:** "gray, green, yellow" passt nicht zur Farbcodierung/Sicherheitsstufe. Beispiel: CRM-Blue Ant [KRITISCH] aber als Gray eingestuft  
**Datei:** `backend/app/services/normalizer.py`, `frontend/js/ui.js`  
**Lösung:** Mapping zwischen `status_color` und kritikalität prüfen. Gelbe Stufe zwischen kritisch und gut einführen  
**Aufwand:** ~1-2h

### 10. Gelbe/Warn-Stufe fehlt
**Problem:** Gibt es eine gelbe Stufe zwischen kritisch und gutem Zustand?  
**Datei:** `backend/app/models/domain.py` (StatusColor), `backend/app/services/normalizer.py`  
**Lösung:** Gelbe Stufe für "Risikobehaftet" oder "Zeitkritisch" Projekte einführen  
**Aufwand:** ~1h

### 11. "Innovatives Projekt für Industrie 4.0 #262" sollte kritisch sein
**Problem:** Projekt mit hoher Bewertung wird nicht als kritisch eingeordnet  
**Datei:** `backend/app/services/normalizer.py`, `backend/app/ai/prompts.py`  
**Lösung:** Kritikalitäts-Logik prüfen, ggf. erweitern  
**Aufwand:** ~1h

### 12. Anführungszeichen '' → ""
**Problem:** Einfache Anführungszeichen sollten durch doppelte ersetzt werden  
**Datei:** Alle Dateien mit Text-Generierung (`backend/app/ai/prompts.py`, `backend/app/services/docx_builder.py`, `backend/app/services/pptx_builder.py`)  
**Lösung:** String-Ersetzung in Prompts und Templates  
**Aufwand:** ~30 Min

### 13. Großbuchstaben → Fettdruck
**Problem:** Statt Großbuchstaben lieber fettgedruckt verwenden  
**Datei:** `backend/app/services/docx_builder.py`, `backend/app/services/pptx_builder.py`  
**Lösung:** `bold=True` statt `.upper()` verwenden  
**Aufwand:** ~30 Min

### 14. "Benötigte Entscheidungen" rot fliegt rum (PPTX)
**Problem:** Roter Text in Enterprise-Cloud-Migration [KRITISCH] Folie  
**Datei:** `backend/app/services/pptx_builder.py`  
**Lösung:** Text-Positionierung und Formatierung prüfen  
**Aufwand:** ~30 Min

---

## 🟡 PRIORITÄT 2 (MITTEL) - Fehlende Features aus Pflichtenheft

### 15. Technische Dokumentation fehlt (7.3 Dokumentationsanforderungen)
**Problem:** Technische Beschreibung der KI-Abfragen (Prompts, Variablen) fehlt  
**Datei:** Neu erstellen  
**Lösung:** Dokument erstellen mit:
- Beschreibung aller verwendeten Prompts
- Verwendete Variablen/Datenpunkte
- Aufbau/Struktur der KI-Analyselogik  
**Aufwand:** ~3-4h

### 16. Tabellarische Gegenüberstellung der Aufwandsstunden fehlt
**Problem:** Im Pflichtenheft wurde tabellarische Gegenüberstellung der reinen Aufwandsstunden gefordert  
**Datei:** `backend/app/services/docx_builder.py`, `backend/app/services/pptx_builder.py`  
**Lösung:** Tabelle erstellen mit: Projekt | Geplant | Ist | Forecast | Abweichung  
**Aufwand:** ~2-3h

### 17. Visuelle Elemente in Word-Bericht (Soll-Kriterium)
**Problem:** Word-Bericht ist textlastig, fehlt farbliche Kennzeichnung (Rot/Gelb/Grün) für Status  
**Datei:** `backend/app/services/docx_builder.py`, `backend/app/models/docx.py`  
**Lösung:** Farbige Status-Indikatoren für kritische Projekte hinzufügen  
**Aufwand:** ~2h

### 18. Vergleichbarkeit der Projekte fehlt
**Problem:** "Sie soll einen Fokus auf die Vergleichbarkeit der Projekte legen (z. B. 2 Projekte haben ähnliche Themen)"  
**Datei:** `backend/app/ai/prompts.py`, `backend/app/services/docx_builder.py`  
**Lösung:** LLM-Prompt erweitern um Projekt-Vergleich, ähnliche Projekte identifizieren  
**Aufwand:** ~2-3h

### 19. Prognose-Analyse verbessern
**Problem:** Analyse von Prognosen (Kann-Kriterium) ist halbwegs erfüllt, könnte besser sein  
**Datei:** `backend/app/ai/prompts.py`  
**Lösung:** Prompt erweitern um detailliertere Trend-Analysen  
**Aufwand:** ~1-2h

### 20. "Identifizierte Risikomuster" Folie hat wenig Inhalt
**Problem:** Detaillierte PP sollte mehr Inhalt auf Risikomuster-Folie haben  
**Datei:** `backend/app/services/pptx_builder.py`  
**Lösung:** Mehr Details zu Risikomustern generieren, ggf. LLM-Prompt erweitern  
**Aufwand:** ~1-2h

---

## 🟢 PRIORITÄT 3 (NIEDRIG) - Polish und kleine Verbesserungen

### 21. Satzbau-Variation in Word (optional)
**Problem:** Satzanfänge wiederholen sich zu sehr  
**Datei:** `backend/app/ai/prompts.py`  
**Lösung:** Prompt erweitern um Variation der Satzanfänge  
**Aufwand:** ~30 Min

### 22. Windows-Test
**Problem:** Wurde es auf Windows-Rechner getestet?  
**Datei:** N/A  
**Lösung:** Test auf Windows durchführen, `start.bat` prüfen  
**Aufwand:** ~1h

### 23. Abbildung abgeschnitten (Frontend)
**Problem:** Abbildung ist abgeschnitten  
**Datei:** `frontend/styles/components.css`  
**Lösung:** CSS für Bilder/Charts prüfen, `overflow` und `object-fit` anpassen  
**Aufwand:** ~30 Min

---

## 📋 Zusammenfassung nach Aufwand

| Priorität | Anzahl Tasks | Geschätzter Aufwand |
|-----------|-------------|-------------------|
| P0 (Kritisch) | 5 | ~6-8h |
| P1 (Hoch) | 9 | ~8-12h |
| P2 (Mittel) | 6 | ~12-16h |
| P3 (Niedrig) | 3 | ~2-3h |
| **GESAMT** | **23** | **~28-39h** |

---

## 🎯 Empfohlene Reihenfolge

### Sprint 1 (Kritische Bugs - 1-2 Tage)
1. TTS Stop-Button Bug (#1)
2. "[ABGESCHLOSSEN]en" Textfehler (#5)
3. Text abgeschnitten Executive Summary (#4)
4. Kritikalitäts-Erkennung (#2)
5. Identische Inhalte DATEN-FEHLER (#3)

### Sprint 2 (UX Verbesserungen - 2-3 Tage)
6. [KRITISCH] als Tag (#6)
7. [DATEN-FEHLER] als Tag (#7)
8. Sortierung nach Kritikalität (#8)
9. Farbcodierung korrigieren (#9)
10. Gelbe Stufe einführen (#10)
11. Anführungszeichen (#12)
12. Großbuchstaben → Fettdruck (#13)

### Sprint 3 (Pflichtenheft Features - 3-4 Tage)
15. Technische Dokumentation (#15)
16. Tabellarische Aufwandsstunden (#16)
17. Visuelle Elemente Word (#17)
18. Projekt-Vergleichbarkeit (#18)
19. Prognose-Analyse (#19)
20. Risikomuster-Folie (#20)

### Sprint 4 (Polish - 1 Tag)
21. Satzbau-Variation (#21)
22. Windows-Test (#22)
23. Abbildung abgeschnitten (#23)

---

## 📝 Notizen

- **Kritikalitäts-Logik:** Aktuell wird `is_critical` hauptsächlich durch LLM bestimmt. Heuristik in `normalizer.py` sollte erweitert werden für Projekte mit 0% Fortschritt.
- **DATEN-FEHLER:** Diese Projekte sollten trotzdem projektspezifische Analysen erhalten, nicht Fallback-Text.
- **Technische Dokumentation:** Sollte alle Prompts in `backend/app/ai/prompts.py` dokumentieren.
- **Windows-Kompatibilität:** `start.bat` existiert bereits, sollte getestet werden.
