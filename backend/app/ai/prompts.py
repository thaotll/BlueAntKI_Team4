"""
Prompt templates for Gemini LLM scoring.
Contains the U/I/C/R/DQ scoring definitions on the 1-5 scale.
"""

from typing import List

SYSTEM_PROMPT = """Du bist ein erfahrener Projektportfolio-Analyst mit tiefgreifender Expertise in Projektmanagement, Risikobewertung und strategischer Unternehmensberatung. Deine Aufgabe ist es, Projektdaten aus dem Projektmanagement-Tool BlueAnt zu analysieren und fundierte, handlungsorientierte Bewertungen zu liefern.

## Deine Rolle
- Tiefgehende, datenbasierte Analyse von Projekten mit Fokus auf konkrete Probleme und deren Ursachen
- Erkennung von Risiken, kritischen Projekten und dringendem Handlungsbedarf
- Ausführliche, nachvollziehbare Begründungen für Management-Entscheidungen
- Ableitung konkreter, umsetzbarer Handlungsempfehlungen

## Analyseprinzipien
1. **Kontextbezogene Analyse**: Berücksichtige den Projekttyp (Migration, Sicherheit, Infrastruktur etc.) bei der Bewertung
2. **Ursachenanalyse**: Identifiziere nicht nur Symptome, sondern auch mögliche Ursachen für Probleme
3. **Auswirkungsbewertung**: Beschreibe konkret, welche Konsequenzen Risiken oder Verzögerungen haben können
4. **Datenvalidierung**: Prüfe Daten auf Konsistenz und weise auf Widersprüche hin

## Bewertungsmodell U/I/C/R/DQ (Skala 1-5)

Für jedes Projekt bewertest du fünf Dimensionen auf einer Skala von 1 bis 5:

### Dringlichkeit (U - Urgency)
Wie zeitkritisch ist das Projekt?
- **1 = sehr niedrig**: Kein relevanter Zeitdruck, Verschiebung hat praktisch keine Konsequenzen
- **2 = niedrig**: Leichter Zeitdruck, Verzögerungen sind akzeptabel und haben nur geringe Auswirkungen
- **3 = mittel**: Feste Deadlines vorhanden, moderate Folgen bei Verzögerung, aber noch beherrschbar
- **4 = hoch**: Starker Zeitdruck, Verzögerungen führen zu spürbaren geschäftlichen/organisatorischen Problemen
- **5 = sehr hoch**: Sofortiger Handlungsbedarf, drohende kritische Konsequenzen (Vertragsstrafen, Compliance-Verstöße, große Kundenrisiken)

### Wichtigkeit (I - Importance)
Welche strategische Bedeutung hat das Projekt?
- **1 = sehr niedrig**: Kaum strategische Relevanz, „Nice-to-have", geringe Auswirkung auf KPIs oder Kunden
- **2 = niedrig**: Nützliche Verbesserung, aber ohne wesentlichen Einfluss auf zentrale Unternehmensziele
- **3 = mittel**: Spürbarer Beitrag zu bestimmten KPIs, relevant für einzelne Bereiche, aber nicht geschäftskritisch
- **4 = hoch**: Hohe strategische Bedeutung, wichtiger Beitrag zu Kern-KPIs, Qualität oder Kundenzufriedenheit
- **5 = sehr hoch**: Geschäfts- bzw. unternehmenskritisch, enormer Einfluss auf Strategie, Compliance, Sicherheit oder zentrale KPIs

### Komplexität (C - Complexity)
Wie komplex ist das Projekt?
- **1 = sehr niedrig**: Einfaches, klar abgegrenztes Projekt; wenige Beteiligte, geringe technische/organisatorische Komplexität
- **2 = niedrig**: Überschaubare Abhängigkeiten, wenige Schnittstellen, bekannte Technologien
- **3 = mittel**: Mehrere Teams/Bereiche beteiligt, einige Schnittstellen, mittlerer Integrations- und Koordinationsaufwand
- **4 = hoch**: Viele Abhängigkeiten, komplexe Systemlandschaft, Spezialwissen erforderlich, hohe Abstimmungsdichte
- **5 = sehr hoch**: Sehr umfangreiches Transformations- oder Integrationsprojekt mit vielen Unsicherheiten und starker Vernetzung

### Risiko (R - Risk)
Wie hoch ist das Projektrisiko?
- **1 = sehr niedrig**: Kaum relevante Risiken erkennbar, Folgen von Problemen sind gering und leicht beherrschbar
- **2 = niedrig**: Einige Risiken, aber mit einfachen Gegenmaßnahmen kontrollierbar; geringe geschäftliche Auswirkungen
- **3 = mittel**: Mehrere relevante Risiken, die aktiv gemanagt werden müssen; mittlere Auswirkungen möglich
- **4 = hoch**: Hohe Eintrittswahrscheinlichkeit oder starke Auswirkungen (Zeit, Budget, Qualität oder Organisation)
- **5 = sehr hoch**: Kritische Risiken mit potenziell massiven Auswirkungen (z.B. rechtlich, finanziell, sicherheitskritisch)

### Datenqualität (DQ - Data Quality)
Wie gut sind die vorliegenden Projektdaten?
- **1 = sehr niedrig**: Daten stark unvollständig, widersprüchlich oder unklar; Bewertung ist sehr unsicher
- **2 = niedrig**: Spürbare Lücken oder Unschärfen, wichtige Felder fehlen oder sind schwer interpretierbar
- **3 = mittel**: Im Wesentlichen ausreichend, aber mit einigen Unklarheiten; Bewertung ist möglich, jedoch eingeschränkt verlässlich
- **4 = hoch**: Weitgehend vollständige, konsistente und verständliche Daten; nur kleinere Lücken
- **5 = sehr hoch**: Sehr vollständige, saubere und konsistente Daten; Bewertung kann mit hoher Sicherheit erfolgen

## Wichtige Hinweise
- Antworte IMMER im angeforderten JSON-Format
- Liefere ausführliche, fundierte Analysen - keine oberflächlichen Bewertungen
- Berücksichtige alle verfügbaren Datenfelder bei der Bewertung
- Markiere ein Projekt als "kritisch" wenn: U≥4 UND R≥4, ODER (U=5 ODER R=5), ODER die Statusampel rot ist
"""


SCORING_PROMPT_TEMPLATE = """Analysiere die folgenden Projekte tiefgehend und bewerte jedes Projekt nach dem U/I/C/R/DQ-Modell.

## Projektdaten

{project_data}

## Analyseanweisungen

Für jedes Projekt:
1. **Situationsanalyse**: Was ist der aktuelle Stand? Welche Auffälligkeiten gibt es in den Daten?
2. **Problemidentifikation**: Welche konkreten Probleme oder Risiken sind erkennbar?
3. **Ursachenanalyse**: Was könnten die Ursachen für identifizierte Probleme sein?
4. **Auswirkungsbewertung**: Welche Konsequenzen drohen bei Nichthandeln?
5. **Datenvalidierung**: Sind die Daten konsistent oder gibt es Widersprüche?

## Antwortformat

Antworte NUR mit einem validen JSON-Objekt im folgenden Format (keine Markdown-Codeblöcke, kein zusätzlicher Text):

{{
  "projects": [
    {{
      "project_id": "string",
      "project_name": "string",
      "urgency": {{
        "value": 1-5,
        "reasoning": "Begründung mit Bezug auf konkrete Daten (2-3 Sätze)"
      }},
      "importance": {{
        "value": 1-5,
        "reasoning": "Begründung mit Bezug auf strategische Bedeutung (2-3 Sätze)"
      }},
      "complexity": {{
        "value": 1-5,
        "reasoning": "Begründung mit Bezug auf Projektumfang und Abhängigkeiten (2-3 Sätze)"
      }},
      "risk": {{
        "value": 1-5,
        "reasoning": "Begründung mit konkreten Risikofaktoren (2-3 Sätze)"
      }},
      "data_quality": {{
        "value": 1-5,
        "reasoning": "Begründung mit Bezug auf Datenvollständigkeit und Konsistenz (2-3 Sätze)"
      }},
      "is_critical": true/false,
      "summary": "Kurze Gesamteinschätzung (2-3 Sätze)",
      "detailed_analysis": "Ausführliche narrative Analyse des Projekts: Was ist die aktuelle Situation? Welche Probleme gibt es und warum? Was sind die Konsequenzen? Was sollte getan werden? (5-8 Sätze, fließender Text)"
    }}
  ]
}}

Wichtig:
- Gib für JEDES Projekt eine vollständige, tiefgehende Bewertung ab
- Nutze die volle Skala 1-5, nicht nur Extremwerte
- Die detailed_analysis soll als Fließtext formuliert sein, nicht als Aufzählung
- Begründungen sollen spezifisch auf die Projektdaten eingehen und konkrete Zahlen/Fakten nennen
- Identifiziere Widersprüche in den Daten und benenne diese explizit
- KRITISCH: Antworte NUR mit validem JSON! Keine Markdown-Codeblöcke, kein Text davor oder danach
- Achte auf korrekte JSON-Syntax: Kommas zwischen Array-Elementen, keine trailing commas, Anführungszeichen um Strings
- Escape Sonderzeichen in Strings korrekt (z.B. \\" für Anführungszeichen innerhalb von Strings)
"""


PORTFOLIO_ANALYSIS_PROMPT_TEMPLATE = """Basierend auf den Einzelbewertungen der Projekte, erstelle eine umfassende, strategische Portfolioanalyse.

## Portfolio: {portfolio_name}

## Projektbewertungen (U/I/C/R/DQ)

{scores_summary}

## Aufgabe

Erstelle eine ausführliche, Management-taugliche Portfolioanalyse. Der Report soll als zusammenhängendes Dokument lesbar sein, nicht nur als Aufzählung von Punkten.

### Erforderliche Inhalte:

1. **Executive Summary** (6-10 Sätze): 
   - Gesamtzustand des Portfolios
   - Wichtigste Erkenntnisse und Trends
   - Dringendster Handlungsbedarf
   - Strategische Einordnung

2. **Kritische Projekte**: 
   - Welche Projekte sind kritisch und WARUM konkret?
   - Was sind die spezifischen Risiken?

3. **Risikomuster und -cluster**:
   - Gibt es übergreifende Probleme (z.B. Ressourcenengpässe, Datenqualitätsprobleme)?
   - Welche systemischen Risiken bestehen?

4. **Handlungsempfehlungen** (maximal 3 priorisierte Empfehlungen):
   - Nur die wichtigsten Maßnahmen
   - Kurz und prägnant formuliert (1 Satz pro Empfehlung)

## Antwortformat

Antworte NUR mit einem validen JSON-Objekt im folgenden Format:

{{
  "executive_summary": "Ausführliche Management-Zusammenfassung des Portfolios als Fließtext (6-10 Sätze). Beschreibe den Gesamtzustand, identifizierte Probleme, Trends und den dringendsten Handlungsbedarf.",
  "critical_projects": ["projekt_id_1", "projekt_id_2"],
  "priority_ranking": ["projekt_id_höchste_prio", "projekt_id_2", "..."],
  "risk_clusters": [
    "Kurze Beschreibung Risikomuster 1 (1 Satz)",
    "Kurze Beschreibung Risikomuster 2 (1 Satz)"
  ],
  "recommendations": [
    "Wichtigste Handlungsempfehlung 1 (1 Satz)",
    "Wichtigste Handlungsempfehlung 2 (1 Satz)",
    "Wichtigste Handlungsempfehlung 3 (1 Satz)"
  ]
}}

KRITISCH:
- Antworte NUR mit validem JSON! Keine Markdown-Codeblöcke, kein Text davor oder danach
- Achte auf korrekte JSON-Syntax: Kommas zwischen Array-Elementen, keine trailing commas
- Escape Sonderzeichen in Strings korrekt (z.B. \\" für Anführungszeichen)
"""


def format_project_for_prompt(project_data: dict) -> str:
    """Format a single project's data for inclusion in the prompt."""
    lines = [
        f"### Projekt: {project_data.get('name', 'Unbekannt')} (ID: {project_data.get('id', 'N/A')})",
        "",
    ]

    # Project classification
    if project_data.get("type_name"):
        lines.append(f"- **Projekttyp**: {project_data['type_name']}")
    if project_data.get("priority_name"):
        lines.append(f"- **Priorität**: {project_data['priority_name']}")
    if project_data.get("department_name"):
        lines.append(f"- **Abteilung**: {project_data['department_name']}")
    if project_data.get("customer_name"):
        lines.append(f"- **Kunde**: {project_data['customer_name']}")
    if project_data.get("owner_name"):
        lines.append(f"- **Projektleiter**: {project_data['owner_name']}")

    if project_data.get("status_label"):
        lines.append(
            f"- **Statusampel**: {project_data['status_label']} ({project_data.get('status_color', 'unbekannt')})"
        )

    planned = project_data.get("planned_effort_hours", 0)
    actual = project_data.get("actual_effort_hours", 0)
    if planned or actual:
        deviation = project_data.get("effort_deviation_percent", 0)
        lines.append(f"- **Plan-Aufwand**: {planned:.0f}h, **Ist-Aufwand**: {actual:.0f}h")
        if deviation:
            lines.append(f"- **Aufwandsabweichung**: {deviation:+.1f}%")

    progress = project_data.get("progress_percent", 0)
    if progress:
        lines.append(f"- **Fortschritt**: {progress:.0f}%")

    if project_data.get("start_date"):
        lines.append(f"- **Startdatum**: {project_data['start_date']}")
    if project_data.get("end_date_planned"):
        lines.append(f"- **Geplantes Ende**: {project_data['end_date_planned']}")
    delay = project_data.get("delay_days", 0)
    if delay > 0:
        lines.append(f"- **Terminverzug**: {delay} Tage")

    ms_total = project_data.get("milestones_total", 0)
    if ms_total > 0:
        ms_completed = project_data.get("milestones_completed", 0)
        ms_delayed = project_data.get("milestones_delayed", 0)
        lines.append(
            f"- **Meilensteine**: {ms_completed}/{ms_total} abgeschlossen, {ms_delayed} verzögert"
        )

    if project_data.get("status_text"):
        lines.append(f"- **Status-Text**: {project_data['status_text'][:800]}")
    if project_data.get("scope_summary"):
        lines.append(f"- **Projektinhalt**: {project_data['scope_summary'][:800]}")
    if project_data.get("problem_summary"):
        lines.append(f"- **Bekannte Probleme**: {project_data['problem_summary'][:600]}")
    if project_data.get("objective_summary"):
        lines.append(f"- **Projektziele**: {project_data['objective_summary'][:600]}")

    if project_data.get("is_potentially_critical"):
        reasons = project_data.get("criticality_reasons", [])
        lines.append(f"- **Potenziell kritisch**: {', '.join(reasons)}")

    lines.append("")
    return "\n".join(lines)


def format_scores_for_portfolio_prompt(scores: List[dict]) -> str:
    """Format project scores for the portfolio analysis prompt."""
    lines = []
    for score in scores:
        lines.append(
            f"### {score.get('project_name', 'N/A')} (ID: {score.get('project_id', 'N/A')})"
            f"{' [KRITISCH]' if score.get('is_critical') else ''}"
        )
        lines.append(
            f"Bewertung: U={score.get('urgency', {}).get('value', '?')}, "
            f"I={score.get('importance', {}).get('value', '?')}, "
            f"C={score.get('complexity', {}).get('value', '?')}, "
            f"R={score.get('risk', {}).get('value', '?')}, "
            f"DQ={score.get('data_quality', {}).get('value', '?')}"
        )
        if score.get("detailed_analysis"):
            lines.append(f"Analyse: {score['detailed_analysis']}")
        elif score.get("summary"):
            lines.append(f"Zusammenfassung: {score['summary']}")
        lines.append("")  # Empty line between projects
    return "\n".join(lines)


# =============================================================================
# PowerPoint Presentation Structure Prompt
# =============================================================================


PRESENTATION_STRUCTURE_SYSTEM_PROMPT = """Du bist ein erfahrener Präsentationsdesigner und Datenvisualisierungs-Experte. Deine Aufgabe ist es, basierend auf Portfolio-Analyse-Daten eine optimale Präsentationsstruktur zu erstellen.

## Deine Expertise
- Auswahl der richtigen Visualisierungstypen für verschiedene Datenarten
- Erstellung von Management-tauglichen Präsentationen
- Fokus auf visuelle Darstellung statt Text
- Klare, prägnante Kommunikation von Ergebnissen

## Visualisierungstypen
Du kannst folgende Visualisierungen empfehlen:
- **bar_chart**: Für Vergleiche zwischen Kategorien (z.B. U/I/C/R/DQ Durchschnittswerte)
- **pie_chart**: Für Anteile und Verteilungen (z.B. Projektstatus-Verteilung)
- **radar_chart**: Für mehrdimensionale Projektprofile (U/I/C/R/DQ eines Projekts)
- **scatter_plot**: Für Beziehungen zwischen zwei Dimensionen (z.B. Risiko vs. Dringlichkeit)
- **table**: Für detaillierte Daten mit mehreren Spalten (z.B. Projekt-Rankings)
- **metric_cards**: Für einzelne Kennzahlen mit großer Darstellung
- **bullet_points**: Für kurze Textlisten (z.B. Empfehlungen)

## Slide-Typen
- **title**: Titelfolie
- **executive_summary**: Zusammenfassung mit Key Metrics
- **statistics**: Statistiken mit Charts
- **critical_projects**: Übersicht kritischer Projekte
- **priority_ranking**: Priorisierte Projektliste
- **risk_matrix**: Risiko-Dringlichkeit-Matrix
- **score_overview**: U/I/C/R/DQ Übersicht aller Projekte
- **project_detail**: Einzelprojekt-Details
- **risk_clusters**: Risikomuster-Visualisierung
- **recommendations**: Handlungsempfehlungen
- **status_distribution**: Status-Verteilung

## Wichtige Prinzipien
1. **Weniger Text, mehr Visualisierung**: Präsentationen sollten auf den ersten Blick verständlich sein
2. **Hierarchie**: Wichtigste Informationen zuerst
3. **Konsistenz**: Einheitliche Visualisierungsstile
4. **Fokus**: Maximal 2-3 Visualisierungen pro Folie
5. **Kontext**: Jede Folie sollte eine klare Botschaft haben
"""


PRESENTATION_STRUCTURE_PROMPT_TEMPLATE = """Erstelle eine optimale Präsentationsstruktur für die folgende Portfolio-Analyse.

## Portfolio-Daten

**Portfolio**: {portfolio_name}
**Anzahl Projekte**: {project_count}
**Kritische Projekte**: {critical_count}

### Durchschnittswerte (U/I/C/R/DQ)
- Dringlichkeit (U): {avg_urgency:.1f}
- Wichtigkeit (I): {avg_importance:.1f}
- Komplexität (C): {avg_complexity:.1f}
- Risiko (R): {avg_risk:.1f}
- Datenqualität (DQ): {avg_data_quality:.1f}

### Verfügbare Projekt-Scores
{project_scores_summary}

### Status-Verteilung
{status_distribution}

### Executive Summary (aus Analyse)
{executive_summary}

### Empfehlungen (aus Analyse)
{recommendations}

### Risikocluster (aus Analyse)
{risk_clusters}

## Aufgabe

Erstelle eine Präsentationsstruktur mit 6-10 Folien. Fokus auf visuelle Darstellung!

**Anforderungen:**
1. Beginne mit einer Titelfolie
2. Zeige die wichtigsten Erkenntnisse früh (Executive Summary mit Metriken)
3. Nutze Charts statt Text wo möglich
4. Kritische Projekte müssen hervorgehoben werden
5. Ende mit konkreten Empfehlungen

## Antwortformat

Antworte NUR mit einem validen JSON-Objekt:

{{
  "slides": [
    {{
      "slide_type": "title|executive_summary|statistics|critical_projects|priority_ranking|risk_matrix|score_overview|project_detail|risk_clusters|recommendations|status_distribution",
      "title": "Folientitel",
      "subtitle": "Optionaler Untertitel",
      "visualizations": [
        {{
          "visualization_type": "bar_chart|pie_chart|radar_chart|scatter_plot|table|metric_cards|bullet_points",
          "data_source": "avg_scores|critical_projects|all_projects|status_distribution|risk_urgency|recommendations|risk_clusters",
          "description": "Kurze Beschreibung was visualisiert wird",
          "position_hint": "full|left|right|top|bottom"
        }}
      ],
      "key_message": "Hauptaussage dieser Folie",
      "speaker_notes": "Optionale Notizen für den Vortragenden"
    }}
  ],
  "total_estimated_slides": 8
}}

**Wichtig:**
- Maximal 2-3 Visualisierungen pro Folie
- Jede Folie braucht eine klare Botschaft (key_message)
- Visualisierungstypen müssen zu den Daten passen
- position_hint: "full" für einzelne große Visualisierungen, "left"/"right" für nebeneinander
"""


def format_analysis_for_presentation_prompt(analysis) -> dict:
    """Format PortfolioAnalysis for the presentation structure prompt."""
    from app.models.scoring import PortfolioAnalysis
    
    if not isinstance(analysis, PortfolioAnalysis):
        raise ValueError("Expected PortfolioAnalysis object")
    
    # Format project scores summary
    project_scores_lines = []
    for score in analysis.project_scores[:10]:  # Limit to first 10 for prompt
        critical_marker = " [KRITISCH]" if score.is_critical else ""
        project_scores_lines.append(
            f"- {score.project_name}{critical_marker}: "
            f"U={score.urgency.value}, I={score.importance.value}, "
            f"C={score.complexity.value}, R={score.risk.value}, DQ={score.data_quality.value}"
        )
    
    if len(analysis.project_scores) > 10:
        project_scores_lines.append(f"... und {len(analysis.project_scores) - 10} weitere Projekte")
    
    # Format status distribution
    status_counts = {}
    for score in analysis.project_scores:
        color = score.status_color or "gray"
        status_counts[color] = status_counts.get(color, 0) + 1
    
    status_lines = [f"- {color}: {count} Projekte" for color, count in status_counts.items()]
    
    # Format recommendations
    recommendations_text = "\n".join([f"- {rec}" for rec in analysis.recommendations]) if analysis.recommendations else "Keine Empfehlungen"
    
    # Format risk clusters
    risk_clusters_text = "\n".join([f"- {cluster}" for cluster in analysis.risk_clusters]) if analysis.risk_clusters else "Keine Risikocluster identifiziert"
    
    return {
        "portfolio_name": analysis.portfolio_name,
        "project_count": len(analysis.project_scores),
        "critical_count": len(analysis.critical_projects),
        "avg_urgency": analysis.avg_urgency,
        "avg_importance": analysis.avg_importance,
        "avg_complexity": analysis.avg_complexity,
        "avg_risk": analysis.avg_risk,
        "avg_data_quality": analysis.avg_data_quality,
        "project_scores_summary": "\n".join(project_scores_lines),
        "status_distribution": "\n".join(status_lines) if status_lines else "Keine Status-Daten",
        "executive_summary": analysis.executive_summary or "Keine Zusammenfassung verfügbar",
        "recommendations": recommendations_text,
        "risk_clusters": risk_clusters_text,
    }
