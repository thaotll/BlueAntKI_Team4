# Feature-Plan: Word-Report-Generierung

## Executive Summary

**Ziel**: Implementierung der Word-Dokument-Generierung als zusätzliches Ausgabeformat für Portfolio-Analysen.

**Hauptkomponenten**:
1. **Models** (`app/models/docx.py`): Datenmodelle für Word-Dokumente
2. **Builder** (`app/services/docx_builder.py`): Konvertiert PortfolioAnalysis → DocxDocumentModel
3. **Renderer** (`app/services/docx_renderer.py`): Konvertiert DocxDocumentModel → .docx Bytes
4. **API-Endpoint** (`POST /api/reports/docx`): HTTP-Interface für Report-Generierung

**Technologie**: `python-docx` Library (analog zu `python-pptx`)

**Architektur**: Folgt dem bewährten Model-Builder-Renderer-Pattern der PPTX-Implementierung

**Implementierungs-Phasen**: 5 Phasen von MVP bis Polishing (siehe Details unten)

**Geschätzter Aufwand**: ~15-20 Personenstunden (abhängig von Phase 5)

## Übersicht

Dieses Dokument beschreibt die Planung für die Implementierung der Word-Dokument-Generierung als zusätzliches Ausgabeformat für die Portfolio-Analyse. Das Feature ermöglicht es, die Analyseergebnisse als bearbeitbares Word-Dokument (.docx) zu exportieren.

## Anforderungen aus Pflichtenheft

### Funktionale Anforderungen
- **Bearbeitbares Format**: Word-Dokument muss vollständig bearbeitbar sein (Kapitel 4.4.3)
- **Bewertungen**: Enthält Bewertungen (Ampeln oder Punktesystem) (Kapitel 4.4.1)
- **Textliche Begründungen**: Kurze Begründungen für jede Bewertung (Kapitel 4.4.1)
- **Vergleichbarkeit**: Fokus auf Vergleichbarkeit der Projekte (Kapitel 4.4.1)
- **Prägnante Texte**: Kurze, prägnante und verständliche Texte (Kapitel 4.4.1)

### Nichtfunktionale Anforderungen
- **Sprache**: Alle Ausgaben in deutscher Sprache (Kapitel 5.5.1, 7.7)
- **Konsistenz**: Konsistente und reproduzierbare Ergebnisse (Kapitel 5.4.3, 7.4)
- **Praxisnutzen**: Praktischer Mehrwert im Geschäftsbetrieb (Kapitel 5.4.1)

## Architektur-Entscheidungen

### Technologie-Stack
- **Bibliothek**: `python-docx` (analog zu `python-pptx` für PowerPoint)
- **Pattern**: Model-Builder-Renderer-Pattern (konsistent mit PPTX-Implementierung)
- **Format**: Office Open XML (.docx) - Standard Word-Format

### Architektur-Pattern

Die Implementierung folgt dem bewährten Pattern der PPTX-Generierung:

```
PortfolioAnalysis
    ↓
DocxBuilder (Business Logic)
    ↓
DocxDocumentModel (Data Model)
    ↓
DocxRenderer (Rendering Logic)
    ↓
.docx bytes
```

### Detaillierter Datenfluss

```
┌─────────────────────────────────────────────────────────────┐
│                    PortfolioAnalysis                         │
│  - portfolio_name, portfolio_id                             │
│  - project_scores[] (mit U/I/C/R/DQ Scores)                  │
│  - executive_summary                                         │
│  - critical_projects[]                                       │
│  - recommendations[]                                         │
│  - statistics (avg_urgency, avg_importance, etc.)           │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    DocxBuilder                               │
│  - build() → DocxDocumentModel                              │
│  - _build_title_page()                                       │
│  - _build_executive_summary()                                │
│  - _build_portfolio_overview()                               │
│  - _build_project_details()                                  │
│  - _build_critical_projects()                               │
│  - _build_recommendations()                                  │
│  - DesignTokens (Farben, Typografie)                        │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              DocxDocumentModel                                │
│  - title, author, created_date                              │
│  - sections[]:                                               │
│    ├─ DocxSectionModel                                      │
│    │   ├─ heading (H1/H2/H3)                                │
│    │   ├─ paragraphs[] (DocxParagraphModel)                  │
│    │   ├─ tables[] (DocxTableModel)                         │
│    │   └─ lists[] (DocxListModel)                           │
│    └─ ...                                                    │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    DocxRenderer                              │
│  - render(model) → bytes                                     │
│  - _render_section()                                        │
│  - _render_paragraph()                                       │
│  - _render_table()                                           │
│  - _render_list()                                            │
│  - _apply_style()                                            │
│  - python-docx API Calls                                     │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
                    .docx file bytes
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              API Endpoint: POST /api/reports/docx           │
│  - GenerateReportRequest (analysis + options)                │
│  - Response: application/vnd.openxmlformats-...              │
│  - Content-Disposition: attachment; filename="..."           │
└─────────────────────────────────────────────────────────────┘
```

## Komponenten-Übersicht

### 1. Models (`app/models/docx.py`)

#### `DocxDocumentModel`
- Hauptmodell für das gesamte Word-Dokument
- Enthält Metadaten (Titel, Autor, Erstellungsdatum)
- Liste von Sektionen/Abschnitten

#### `DocxSectionModel`
- Repräsentiert einen logischen Abschnitt im Dokument
- Enthält Überschrift, Absätze, Tabellen, Listen

#### `DocxParagraphModel`
- Einzelner Absatz mit Formatierung
- Unterstützt verschiedene Stile (Überschrift, Body, Caption)
- Text-Runs mit individueller Formatierung

#### `DocxTableModel`
- Tabellen für strukturierte Daten (z.B. Projektvergleiche)
- Unterstützt Header-Rows, Formatierung, Zell-Styling

#### `DocxListModel`
- Nummerierte oder Aufzählungslisten
- Für Empfehlungen, Risikocluster, etc.

#### Gemeinsame Modelle (Wiederverwendung)
- `RgbColor` (aus `pptx.py` wiederverwenden)
- `TextStyle` (erweitern für Word-spezifische Features)
- `TextRun`, `TextParagraph` (anpassen für Word)

### 2. Builder (`app/services/docx_builder.py`)

#### `DocxBuilder`
- Konvertiert `PortfolioAnalysis` in `DocxDocumentModel`
- Verantwortlich für Content-Entscheidungen und Struktur
- Nutzt `DesignTokens` für konsistentes Styling

#### Hauptmethoden:
- `build()`: Hauptmethode, erstellt vollständiges Dokument
- `_build_title_page()`: Titelseite mit Portfolio-Name, Datum
- `_build_executive_summary()`: Executive Summary Abschnitt
- `_build_portfolio_overview()`: Portfolio-Übersicht mit Statistiken
- `_build_project_details()`: Detaillierte Projektbewertungen
- `_build_critical_projects()`: Fokus auf kritische Projekte
- `_build_recommendations()`: Handlungsempfehlungen
- `_build_appendix()`: Anhang mit technischen Details (optional)

#### DesignTokens (wiederverwendet/erweitert)
- Farben: BlueAnt Primary/Accent (konsistent mit PPTX)
- Typografie: Calibri, konsistente Schriftgrößen
- Abstände: Margins, Paragraph-Spacing

### 3. Renderer (`app/services/docx_renderer.py`)

#### `DocxRenderer`
- Konvertiert `DocxDocumentModel` in tatsächliche .docx Bytes
- Nutzt `python-docx` Library
- Reine Rendering-Logik, keine Business-Entscheidungen

#### Hauptmethoden:
- `render(model)`: Hauptmethode, erstellt .docx Bytes
- `_render_section()`: Rendert einen Abschnitt
- `_render_paragraph()`: Rendert einen Absatz mit Formatierung
- `_render_table()`: Rendert Tabellen
- `_render_list()`: Rendert Listen
- `_apply_style()`: Wendet Text-Styles an

### 4. API-Endpoint (`app/api/reports.py`)

#### Neuer Endpoint: `POST /api/reports/docx`
- Analoge Struktur zu `/api/reports/pptx`
- Nutzt `GenerateReportRequest` (wiederverwendet)
- Gibt Word-Dokument als Download zurück
- Content-Type: `application/vnd.openxmlformats-officedocument.wordprocessingml.document`

## Dokument-Struktur

### 1. Titelseite
- Portfolio-Name (große Überschrift)
- Untertitel: "KI-gestützte Portfolioanalyse (U/I/C/R/DQ)"
- Erstellungsdatum und -zeit
- Optional: Logo/Header

### 2. Executive Summary
- Kurze Management-Zusammenfassung (aus `PortfolioAnalysis.executive_summary`)
- Key Metrics Box (Durchschnittswerte U/I/C/R)
- Kritische Projekte: Anzahl und Liste

### 3. Portfolio-Übersicht
- Statistik-Tabelle:
  - Durchschnittswerte pro Dimension (U/I/C/R/DQ)
  - Anzahl Projekte gesamt
  - Anzahl kritischer Projekte
  - Durchschnittlicher Fortschritt
- Portfolio-Status-Ampel (visuell: grün/gelb/rot)

### 4. Projektbewertungen (Detailliert)
Für jedes Projekt:
- **Projekt-Header**: Name, ID, Owner
- **Bewertungs-Tabelle**:
  | Dimension | Score (1-5) | Begründung |
  |-----------|-------------|------------|
  | U (Dringlichkeit) | ⭐⭐⭐ | ... |
  | I (Wichtigkeit) | ⭐⭐⭐⭐ | ... |
  | C (Komplexität) | ⭐⭐ | ... |
  | R (Risiko) | ⭐⭐⭐⭐ | ... |
  | DQ (Datenqualität) | ⭐⭐⭐ | ... |
- **Projekt-Summary**: Kurze Gesamtbewertung
- **Status-Indikatoren**:
  - Fortschritt: XX%
  - Meilensteine: X/Y abgeschlossen, Z verzögert
  - Aufwand: Plan vs. Ist
  - Status-Ampel (grün/gelb/rot/grau)

### 5. Kritische Projekte
- Fokus-Abschnitt für kritische Projekte
- Detaillierte Analyse der kritischsten 3-5 Projekte
- Risiko-Highlights
- Handlungsbedarf

### 6. Priorisierte Projektliste
- Rangliste aller Projekte nach Priorität
- Tabelle: Rang | Projekt | Prioritäts-Score | Hauptrisiko

### 7. Empfehlungen
- Nummerierte Liste der Handlungsempfehlungen
- Aus `PortfolioAnalysis.recommendations`
- Optional: Priorisierung der Empfehlungen

### 8. Anhang (Optional)
- Technische Details
- Datenqualitäts-Hinweise
- Methodik-Kurzbeschreibung

## Design-Spezifikation

### Farben
- **Primary**: BlueAnt Blau (#016bd5) - für Überschriften, Akzente
- **Accent**: Hellblau (#008dca) - für Hervorhebungen
- **Text**: Dunkelgrau (#333333) - Haupttext
- **Ampeln**:
  - Grün: #00AA44
  - Gelb: #FFAA00
  - Rot: #CC0000
  - Grau: #808080

### Typografie
- **Schriftart**: Calibri (konsistent mit PPTX)
- **Überschriften**:
  - H1 (Titel): 24pt, Bold, Primary Color
  - H2 (Sektion): 18pt, Bold, Text Dark
  - H3 (Unterabschnitt): 14pt, Bold, Text Dark
- **Body**: 11pt, Regular, Text Dark
- **Caption**: 9pt, Regular, Text Light

### Layout
- **Seitenränder**: 2.5cm (Standard Word)
- **Zeilenabstand**: 1.15 (leicht erhöht für Lesbarkeit)
- **Absatzabstand**: 6pt nach Überschriften, 3pt zwischen Absätzen

### Tabellen
- **Header-Row**: Primary Color Background, Weiße Schrift, Bold
- **Zebra-Striping**: Alternierende Zeilen (Hellgrau/Weiß)
- **Borders**: Dünne Linien (0.5pt), Grau
- **Zell-Padding**: 0.2cm

## Implementierungs-Phasen

### Phase 1: Grundstruktur (MVP)
- [ ] `python-docx` zu `requirements.txt` hinzufügen
- [ ] Basis-Models erstellen (`docx.py`)
- [ ] Basis-Renderer erstellen (`docx_renderer.py`)
- [ ] API-Endpoint hinzufügen (`/api/reports/docx`)
- [ ] Titelseite implementieren
- [ ] Executive Summary implementieren

**Akzeptanzkriterien**:
- Endpoint liefert gültiges .docx-Dokument
- Dokument enthält Titelseite und Executive Summary
- Dokument ist in Word öffnen- und bearbeitbar

### Phase 2: Projektbewertungen
- [ ] Projektbewertungs-Tabelle implementieren
- [ ] Score-Visualisierung (Sterne/Symbole)
- [ ] Projekt-Details-Abschnitt
- [ ] Status-Indikatoren (Ampeln, Fortschritt)

**Akzeptanzkriterien**:
- Alle Projekte werden mit vollständigen Bewertungen dargestellt
- Tabellen sind gut lesbar und formatiert
- Status-Indikatoren sind visuell klar

### Phase 3: Portfolio-Übersicht & Statistiken
- [ ] Portfolio-Statistik-Tabelle
- [ ] Durchschnittswerte-Visualisierung
- [ ] Portfolio-Status-Ampel

**Akzeptanzkriterien**:
- Alle Statistiken werden korrekt dargestellt
- Visualisierungen sind verständlich

### Phase 4: Kritische Projekte & Empfehlungen
- [ ] Kritische-Projekte-Abschnitt
- [ ] Priorisierte Projektliste
- [ ] Empfehlungen-Liste
- [ ] Formatierung und Styling verfeinern

**Akzeptanzkriterien**:
- Kritische Projekte werden hervorgehoben
- Empfehlungen sind klar strukturiert
- Dokument ist vollständig und professionell

### Phase 5: Polishing & Testing
- [ ] Design-Tokens konsolidieren (gemeinsam mit PPTX)
- [ ] Fehlerbehandlung verbessern
- [ ] Logging erweitern
- [ ] Edge Cases testen (leere Listen, fehlende Daten)
- [ ] Performance-Optimierung (bei Bedarf)

**Akzeptanzkriterien**:
- Dokument entspricht allen Anforderungen aus Pflichtenheft
- Code ist wartbar und dokumentiert
- Keine Fehler bei normalen und Edge-Case-Eingaben

## Abhängigkeiten

### Externe Bibliotheken
- `python-docx`: Muss zu `requirements.txt` hinzugefügt werden
  - Version: `1.1.0` (stabil, gut dokumentiert)
  - Alternative: `docx` (älter, weniger aktiv)

### Interne Abhängigkeiten
- `app.models.scoring.PortfolioAnalysis`: Datenquelle
- `app.models.pptx.RgbColor`: Wiederverwendung für Farben
- Gemeinsame Design-Tokens (können in separatem Modul extrahiert werden)

### Refactoring-Empfehlung: Gemeinsame Design-Tokens

**Aktueller Zustand**: `DesignTokens` ist nur in `PptxBuilder` definiert.

**Empfehlung**: Design-Tokens in gemeinsames Modul extrahieren:
- Neues Modul: `app/design/tokens.py`
- Enthält: Farben, Typografie, Layout-Konstanten
- Wird von beiden Buildern (`PptxBuilder`, `DocxBuilder`) genutzt
- Vorteile:
  - Konsistenz zwischen PPTX und DOCX
  - Einfache Wartung (Single Source of Truth)
  - Einfache Erweiterung für zukünftige Formate

**Umsetzung**: Optional, kann parallel zur Word-Implementierung erfolgen oder danach refactored werden.

## Testing-Strategie

### Unit Tests
- `DocxBuilder`: Testen der Model-Erstellung
- `DocxRenderer`: Testen der Rendering-Logik
- Edge Cases: Leere Analysen, fehlende Daten, Sonderzeichen

### Integration Tests
- API-Endpoint: Testen des vollständigen Flows
- Datei-Validierung: Generiertes .docx ist gültig und öffnenbar

### Manuelle Tests
- Dokument in Word öffnen und bearbeiten
- Formatierung prüfen
- Druckvorschau prüfen
- Verschiedene Word-Versionen testen (2016, 2019, 365)

## Risiken & Mitigation

### Risiko 1: Inkompatibilität mit Word-Versionen
- **Mitigation**: `python-docx` nutzt Standard Office Open XML, sollte kompatibel sein
- **Test**: Verschiedene Word-Versionen testen

### Risiko 2: Komplexe Formatierung schwer umsetzbar
- **Mitigation**: Fokus auf Standard-Formatierungen, komplexe Layouts vermeiden
- **Fallback**: Einfacheres Layout, wenn komplexe Formatierung nicht funktioniert

### Risiko 3: Performance bei vielen Projekten
- **Mitigation**: Lazy Rendering, Streaming bei sehr großen Dokumenten
- **Monitoring**: Logging der Generierungszeit

### Risiko 4: Unterschiedliche Darstellung in verschiedenen Word-Versionen
- **Mitigation**: Standard-Stile verwenden, keine proprietären Features
- **Test**: In verschiedenen Versionen validieren

## Offene Fragen

1. **Seitenzahlen**: Sollen Seitenzahlen hinzugefügt werden? (Empfehlung: Ja, ab Seite 2)
2. **Inhaltsverzeichnis**: Soll automatisch ein Inhaltsverzeichnis generiert werden? (Empfehlung: Ja, bei >5 Seiten)
3. **Header/Footer**: Sollen Header/Footer mit Logo/Informationen hinzugefügt werden? (Empfehlung: Optional)
4. **Tabellen-Größe**: Wie viele Projekte maximal? Soll Paginierung bei Tabellen erfolgen? (Empfehlung: Automatische Word-Paginierung nutzen)
5. **Grafiken**: Sollen Charts/Grafiken eingebettet werden? (Empfehlung: Phase 2, optional)

## Nächste Schritte

1. **Review dieser Planung** mit dem Team
2. **Entscheidung über offene Fragen**
3. **Start mit Phase 1** (Grundstruktur)
4. **Iterative Entwicklung** mit Feedback-Loops

## Referenzen

- Pflichtenheft Team4.txt (Kapitel 4.4, 5.5, 7.7)
- Bestehende PPTX-Implementierung (`app/services/pptx_builder.py`, `app/services/pptx_renderer.py`)
- `python-docx` Dokumentation: https://python-docx.readthedocs.io/
- Office Open XML Spezifikation: ECMA-376

