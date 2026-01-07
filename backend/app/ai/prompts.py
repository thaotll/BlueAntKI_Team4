"""
Prompt templates for Gemini LLM scoring.
Contains the U/I/C/R/DQ scoring definitions on the 1-5 scale.
"""

from typing import List

SYSTEM_PROMPT = """Du bist ein erfahrener Projektportfolio-Analyst. Deine Aufgabe ist es, Projektdaten aus dem Projektmanagement-Tool BlueAnt zu analysieren und strukturiert zu bewerten.

## Deine Rolle
- Objektive, datenbasierte Bewertung von Projekten
- Erkennung von Risiken, kritischen Projekten und Handlungsbedarf
- Klare, prägnante Begründungen für Management-Entscheidungen

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
- Begründungen sollten kurz und prägnant sein (1-2 Sätze)
- Berücksichtige alle verfügbaren Datenfelder bei der Bewertung
- Markiere ein Projekt als "kritisch" wenn: U≥4 UND R≥4, ODER (U=5 ODER R=5), ODER die Statusampel rot ist
"""


SCORING_PROMPT_TEMPLATE = """Analysiere die folgenden Projekte und bewerte jedes Projekt nach dem U/I/C/R/DQ-Modell.

## Projektdaten

{project_data}

## Antwortformat

Antworte NUR mit einem validen JSON-Objekt im folgenden Format (keine Markdown-Codeblöcke, kein zusätzlicher Text):

{{
  "projects": [
    {{
      "project_id": "string",
      "project_name": "string",
      "urgency": {{
        "value": 1-5,
        "reasoning": "Kurze Begründung"
      }},
      "importance": {{
        "value": 1-5,
        "reasoning": "Kurze Begründung"
      }},
      "complexity": {{
        "value": 1-5,
        "reasoning": "Kurze Begründung"
      }},
      "risk": {{
        "value": 1-5,
        "reasoning": "Kurze Begründung"
      }},
      "data_quality": {{
        "value": 1-5,
        "reasoning": "Kurze Begründung"
      }},
      "is_critical": true/false,
      "summary": "Kurze Gesamteinschätzung (1-2 Sätze)"
    }}
  ]
}}

Wichtig:
- Gib für JEDES Projekt eine vollständige Bewertung ab
- Nutze die volle Skala 1-5, nicht nur Extremwerte
- Begründungen sollen spezifisch auf die Projektdaten eingehen
"""


PORTFOLIO_ANALYSIS_PROMPT_TEMPLATE = """Basierend auf den Einzelbewertungen der Projekte, erstelle eine aggregierte Portfolioanalyse.

## Portfolio: {portfolio_name}

## Projektbewertungen (U/I/C/R/DQ)

{scores_summary}

## Aufgabe

Erstelle eine Management-taugliche Portfolioanalyse mit:
1. Executive Summary (3-5 Sätze Gesamtüberblick)
2. Identifizierte kritische Projekte und warum
3. Priorisierungsempfehlungen
4. Erkannte Risikomuster oder -cluster
5. Konkrete Handlungsempfehlungen

## Antwortformat

Antworte NUR mit einem validen JSON-Objekt im folgenden Format:

{{
  "executive_summary": "Management-taugliche Zusammenfassung des Portfolios (3-5 Sätze)",
  "critical_projects": ["projekt_id_1", "projekt_id_2"],
  "priority_ranking": ["projekt_id_höchste_prio", "projekt_id_2", "..."],
  "risk_clusters": [
    "Beschreibung Risikomuster 1",
    "Beschreibung Risikomuster 2"
  ],
  "recommendations": [
    "Konkrete Handlungsempfehlung 1",
    "Konkrete Handlungsempfehlung 2",
    "Konkrete Handlungsempfehlung 3"
  ]
}}
"""


def format_project_for_prompt(project_data: dict) -> str:
    """Format a single project's data for inclusion in the prompt."""
    lines = [
        f"### Projekt: {project_data.get('name', 'Unbekannt')} (ID: {project_data.get('id', 'N/A')})",
        "",
    ]

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
        lines.append(f"- **Status-Text**: {project_data['status_text'][:500]}")
    if project_data.get("scope_summary"):
        lines.append(f"- **Projektinhalt**: {project_data['scope_summary'][:500]}")

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
            f"- **{score.get('project_name', 'N/A')}** (ID: {score.get('project_id', 'N/A')}): "
            f"U={score.get('urgency', {}).get('value', '?')}, "
            f"I={score.get('importance', {}).get('value', '?')}, "
            f"C={score.get('complexity', {}).get('value', '?')}, "
            f"R={score.get('risk', {}).get('value', '?')}, "
            f"DQ={score.get('data_quality', {}).get('value', '?')}"
            f"{' [KRITISCH]' if score.get('is_critical') else ''}"
        )
        if score.get("summary"):
            lines.append(f"  → {score['summary']}")
    return "\n".join(lines)
