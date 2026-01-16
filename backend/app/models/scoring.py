"""
Pydantic models for U/I/C/R/DQ scoring results.
"""

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class ScoreValue(BaseModel):
    """
    Single dimension score with value and reasoning.
    Scale: 1-5 (1=sehr niedrig, 2=niedrig, 3=mittel, 4=hoch, 5=sehr hoch)
    """

    value: int = Field(..., ge=1, le=5, description="Score from 1 to 5")
    reasoning: str = Field(..., description="Brief explanation for this score")

    @field_validator("value", mode="before")
    @classmethod
    def clamp_value(cls, v):
        """Ensure value is within 1-5 range."""
        if isinstance(v, (int, float)):
            return max(1, min(5, int(v)))
        return v


class ProjectScore(BaseModel):
    """
    Complete U/I/C/R/DQ scoring for a single project.

    Dimensions:
    - U (Urgency/Dringlichkeit): Zeit bis zur Konsequenz, Deadlines
    - I (Importance/Wichtigkeit): Strategische Bedeutung, KPI-Relevanz
    - C (Complexity/Komplexität): Technische/organisatorische Komplexität
    - R (Risk/Risiko): Technische, finanzielle, terminliche Risiken
    - DQ (Data Quality/Datenqualität): Vollständigkeit und Klarheit der Daten
    """

    project_id: str = Field(..., description="Project identifier")
    project_name: str = Field(..., description="Project name for reference")

    urgency: ScoreValue = Field(..., description="Dringlichkeit (U)")
    importance: ScoreValue = Field(..., description="Wichtigkeit (I)")
    complexity: ScoreValue = Field(..., description="Komplexität (C)")
    risk: ScoreValue = Field(..., description="Risiko (R)")
    data_quality: ScoreValue = Field(..., description="Datenqualität (DQ)")

    # Summary and Analysis
    is_critical: bool = Field(
        default=False, description="LLM assessment: is this project critical?"
    )
    summary: str = Field(
        default="", description="Brief overall assessment of the project"
    )
    detailed_analysis: str = Field(
        default="",
        description="Ausführliche Projektanalyse mit Problembeschreibung, Ursachen und Auswirkungen (3-5 Sätze)"
    )

    # Enriched fields from NormalizedProject (for reporting)
    progress_percent: float = Field(
        default=0.0, description="Project completion percentage (0-100)"
    )
    owner_name: Optional[str] = Field(
        default=None, description="Project owner/responsible person"
    )
    status_color: str = Field(
        default="gray", description="Traffic light status (green/yellow/red/gray)"
    )
    status_label: Optional[str] = Field(
        default=None, description="Project status label (e.g., 'Abgeschlossen', 'In Bearbeitung')"
    )
    milestones_total: int = Field(
        default=0, description="Total number of milestones"
    )
    milestones_completed: int = Field(
        default=0, description="Number of completed milestones"
    )
    milestones_delayed: int = Field(
        default=0, description="Number of delayed milestones"
    )
    planned_effort_hours: float = Field(
        default=0.0, description="Planned effort in hours"
    )
    actual_effort_hours: float = Field(
        default=0.0, description="Actual effort in hours"
    )
    has_status_mismatch: bool = Field(
        default=False, description="Status doesn't match actual project data"
    )
    status_mismatch_reasons: List[str] = Field(
        default_factory=list, description="Reasons for status mismatch"
    )

    @property
    def average_score(self) -> float:
        """Calculate average of all dimension scores."""
        scores = [
            self.urgency.value,
            self.importance.value,
            self.complexity.value,
            self.risk.value,
        ]
        return sum(scores) / len(scores)

    @property
    def priority_score(self) -> float:
        """Calculate priority score for ranking."""
        base = (self.urgency.value * 2 + self.importance.value * 2) / 4
        risk_factor = self.risk.value / 5
        confidence = self.data_quality.value / 5
        return base * (1 + risk_factor * 0.3) * confidence


class PortfolioAnalysis(BaseModel):
    """Aggregated portfolio analysis result from LLM."""

    portfolio_id: str = Field(..., description="Portfolio identifier")
    portfolio_name: str = Field(..., description="Portfolio name")

    # Project Scores
    project_scores: List[ProjectScore] = Field(
        default_factory=list, description="Individual project scores"
    )

    # Aggregated Insights
    executive_summary: str = Field(
        default="", description="Management-ready portfolio summary"
    )
    critical_projects: List[str] = Field(
        default_factory=list,
        description="List of project IDs identified as critical",
    )
    priority_ranking: List[str] = Field(
        default_factory=list,
        description="Project IDs sorted by priority (highest first)",
    )
    risk_clusters: List[str] = Field(
        default_factory=list,
        description="Identified risk clusters or patterns",
    )
    recommendations: List[str] = Field(
        default_factory=list,
        description="Actionable recommendations for portfolio management",
    )

    # Statistics
    avg_urgency: float = Field(default=0.0, description="Average urgency across projects")
    avg_importance: float = Field(
        default=0.0, description="Average importance across projects"
    )
    avg_complexity: float = Field(
        default=0.0, description="Average complexity across projects"
    )
    avg_risk: float = Field(default=0.0, description="Average risk across projects")
    avg_data_quality: float = Field(
        default=0.0, description="Average data quality across projects"
    )

    # Data Quality Warnings (from SanityValidator)
    data_warnings: List[str] = Field(
        default_factory=list,
        description="Warnungen zu Daten-Inkonsistenzen und fehlenden Daten"
    )

    def compute_statistics(self) -> None:
        """Compute average statistics from project scores."""
        if not self.project_scores:
            return

        n = len(self.project_scores)
        self.avg_urgency = sum(p.urgency.value for p in self.project_scores) / n
        self.avg_importance = sum(p.importance.value for p in self.project_scores) / n
        self.avg_complexity = sum(p.complexity.value for p in self.project_scores) / n
        self.avg_risk = sum(p.risk.value for p in self.project_scores) / n
        self.avg_data_quality = sum(p.data_quality.value for p in self.project_scores) / n

        # Update critical projects list
        self.critical_projects = [
            p.project_id for p in self.project_scores if p.is_critical
        ]

        # Update priority ranking
        sorted_projects = sorted(
            self.project_scores, key=lambda p: p.priority_score, reverse=True
        )
        self.priority_ranking = [p.project_id for p in sorted_projects]
