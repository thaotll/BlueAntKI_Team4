"""
Data normalization service.
Transforms raw BlueAnt data into normalized structures for LLM analysis.
"""

import logging
import re
from collections import Counter
from datetime import date, datetime
from typing import Optional

from app.models.blueant import (
    BlueAntPlanningEntry,
    BlueAntPortfolio,
    BlueAntProject,
    BlueAntStatus,
)
from app.models.domain import (
    MilestoneStatus,
    NormalizedMilestone,
    NormalizedPortfolio,
    NormalizedProject,
    ProjectsPerStatus,
    StatusColor,
)

logger = logging.getLogger(__name__)


class DataNormalizer:
    """
    Transforms raw BlueAnt API data into normalized, LLM-ready structures.

    Responsibilities:
    - Clean text fields (remove HTML, normalize whitespace)
    - Map status IDs to labels and colors
    - Aggregate planning entries into effort metrics
    - Extract and normalize milestones
    - Compute derived indicators (criticality, delays)
    """

    def __init__(self, status_masterdata: Optional[list[BlueAntStatus]] = None):
        self.status_map: dict[str, BlueAntStatus] = {}
        if status_masterdata:
            self.status_map = {s.id: s for s in status_masterdata}

    def set_status_masterdata(self, status_masterdata: list[BlueAntStatus]) -> None:
        """Update status masterdata mapping."""
        self.status_map = {s.id: s for s in status_masterdata}

    @staticmethod
    def clean_text(text: Optional[str], max_length: int = 2000) -> Optional[str]:
        """Clean and normalize text content."""
        if not text:
            return None

        # Remove HTML tags
        text = re.sub(r"<[^>]+>", " ", text)

        # Decode common HTML entities
        text = (
            text.replace("&nbsp;", " ")
            .replace("&amp;", "&")
            .replace("&lt;", "<")
            .replace("&gt;", ">")
            .replace("&quot;", '"')
            .replace("&#39;", "'")
        )

        # Normalize whitespace
        text = re.sub(r"\s+", " ", text).strip()

        # Truncate if needed
        if len(text) > max_length:
            text = text[: max_length - 3] + "..."

        return text if text else None

    def map_status_color(self, color_str: Optional[str]) -> StatusColor:
        """Map color string to StatusColor enum."""
        if not color_str:
            return StatusColor.GRAY

        color_lower = color_str.lower()

        if any(c in color_lower for c in ["green", "grün", "#00", "#0f", "#2e"]):
            return StatusColor.GREEN
        elif any(c in color_lower for c in ["yellow", "gelb", "orange", "#ff", "#f0"]):
            return StatusColor.YELLOW
        elif any(c in color_lower for c in ["red", "rot", "#f00", "#e00", "#d00"]):
            return StatusColor.RED
        return StatusColor.GRAY

    def get_status_info(
        self, status_id: Optional[str]
    ) -> tuple[Optional[str], StatusColor]:
        """Get status label and color from status ID."""
        if not status_id or status_id not in self.status_map:
            return None, StatusColor.GRAY

        status = self.status_map[status_id]
        return status.name, self.map_status_color(status.color)

    def determine_milestone_status(
        self,
        entry: BlueAntPlanningEntry,
        reference_date: Optional[date] = None,
    ) -> MilestoneStatus:
        """Determine milestone status based on dates and completion."""
        ref_date = reference_date or date.today()

        if entry.status and "complet" in entry.status.lower():
            return MilestoneStatus.COMPLETED
        if entry.actual_date:
            return MilestoneStatus.COMPLETED

        progress = entry.progress_actual if entry.progress_actual is not None else entry.progress_percent
        if progress is not None:
            if progress >= 100:
                return MilestoneStatus.COMPLETED
            elif progress == 0:
                end_date = entry.end.date() if entry.end else (entry.planned_date or entry.baseline_date)
                if end_date and end_date < ref_date:
                    return MilestoneStatus.DELAYED
                return MilestoneStatus.NOT_STARTED

        planned = entry.end.date() if entry.end else (entry.planned_date or entry.baseline_date)
        if planned:
            if planned < ref_date:
                return MilestoneStatus.DELAYED
            elif (planned - ref_date).days < 7:
                return MilestoneStatus.AT_RISK
            return MilestoneStatus.ON_TRACK

        return MilestoneStatus.NOT_STARTED

    def normalize_milestone(self, entry: BlueAntPlanningEntry) -> NormalizedMilestone:
        """Convert planning entry to normalized milestone."""
        planned = entry.end.date() if entry.end else (entry.planned_date or entry.baseline_date)
        actual = entry.actual_date
        forecast = planned

        delay_days = 0
        if planned:
            comparison_date = actual or date.today()
            delay_days = (comparison_date - planned).days

        return NormalizedMilestone(
            name=entry.name or f"Milestone {entry.id}",
            planned_date=planned,
            actual_date=actual,
            forecast_date=forecast,
            status=self.determine_milestone_status(entry),
            delay_days=delay_days,
            description=self.clean_text(entry.description, max_length=500),
        )

    def normalize_project(
        self,
        project: BlueAntProject,
        planning_entries: Optional[list[BlueAntPlanningEntry]] = None,
    ) -> NormalizedProject:
        """Transform raw BlueAnt project into normalized structure."""
        entries = planning_entries or []

        # Map status
        status_label, status_color = self.get_status_info(project.status_id)

        # Aggregate effort
        planned_effort = sum(e.planned_effort_hours for e in entries)
        actual_effort = sum(e.actual_effort_hours for e in entries)
        forecast_effort = sum(e.forecast_effort or 0 for e in entries)

        # Calculate deviation
        effort_deviation = 0.0
        if planned_effort > 0:
            effort_deviation = ((actual_effort - planned_effort) / planned_effort) * 100

        # Calculate progress
        total_planned = sum(e.planned_effort_hours for e in entries)
        total_actual = sum(e.actual_effort_hours for e in entries)

        progress_values = [e.progress_actual for e in entries if e.progress_actual is not None and not e.is_collective_task]
        if progress_values:
            progress_percent = sum(progress_values) / len(progress_values)
        elif total_planned > 0:
            progress_percent = (total_actual / total_planned * 100)
        else:
            progress_percent = 0.0

        # Extract milestones
        milestone_entries = [
            e for e in entries if e.is_likely_milestone or (e.entry_type and "milestone" in str(e.entry_type).lower())
        ]
        milestones = [self.normalize_milestone(e) for e in milestone_entries]
        milestones_completed = sum(1 for m in milestones if m.status == MilestoneStatus.COMPLETED)
        milestones_delayed = sum(1 for m in milestones if m.status == MilestoneStatus.DELAYED)

        # Calculate schedule delay
        delay_days = 0
        end_date = project.effective_end_date
        if end_date:
            today = date.today()
            if end_date < today:
                delay_days = (today - end_date).days

        # Determine criticality
        criticality_reasons = []
        is_critical = False

        if status_color == StatusColor.RED:
            is_critical = True
            criticality_reasons.append("Status ist rot")
        if effort_deviation > 20:
            is_critical = True
            criticality_reasons.append(f"Aufwandsüberschreitung: {effort_deviation:.0f}%")
        if milestones_delayed > 0:
            is_critical = True
            criticality_reasons.append(f"{milestones_delayed} Meilenstein(e) verzögert")
        if delay_days > 14:
            is_critical = True
            criticality_reasons.append(f"Terminverzug: {delay_days} Tage")

        return NormalizedProject(
            id=str(project.id),
            name=project.name,
            portfolio_id=str(project.portfolio_ids[0]) if project.portfolio_ids else project.portfolio_id,
            owner_name=project.owner_name,
            status_label=status_label,
            status_color=status_color,
            planned_effort_hours=planned_effort,
            actual_effort_hours=actual_effort,
            forecast_effort_hours=forecast_effort if forecast_effort > 0 else actual_effort,
            effort_deviation_percent=effort_deviation,
            progress_percent=min(progress_percent, 100.0),
            start_date=project.effective_start_date,
            end_date_planned=project.effective_end_date,
            end_date_forecast=project.effective_end_date,
            delay_days=delay_days,
            milestones=milestones,
            milestones_total=len(milestones),
            milestones_completed=milestones_completed,
            milestones_delayed=milestones_delayed,
            status_text=self.clean_text(project.status_text),
            scope_summary=self.clean_text(project.description),
            is_potentially_critical=is_critical,
            criticality_reasons=criticality_reasons,
            last_updated=project.updated_at,
        )

    def normalize_portfolio(
        self,
        portfolio: BlueAntPortfolio,
        projects: list[NormalizedProject],
    ) -> NormalizedPortfolio:
        """Create normalized portfolio from portfolio entity and normalized projects."""
        status_counter: Counter[tuple[str, StatusColor]] = Counter()
        for p in projects:
            key = (p.status_label or "Unknown", p.status_color)
            status_counter[key] += 1

        projects_per_status = [
            ProjectsPerStatus(
                status_label=label,
                status_color=color,
                count=count,
            )
            for (label, color), count in status_counter.items()
        ]

        total_planned = sum(p.planned_effort_hours for p in projects)
        total_actual = sum(p.actual_effort_hours for p in projects)
        total_forecast = sum(p.forecast_effort_hours for p in projects)

        critical_projects = [p for p in projects if p.is_potentially_critical]

        return NormalizedPortfolio(
            id=str(portfolio.id),
            name=portfolio.name,
            description=self.clean_text(portfolio.description),
            owner_name=portfolio.owner_name,
            projects=projects,
            projects_per_status=projects_per_status,
            total_projects=len(projects),
            total_planned_effort_hours=total_planned,
            total_actual_effort_hours=total_actual,
            total_forecast_effort_hours=total_forecast,
            critical_projects_count=len(critical_projects),
            critical_project_ids=[p.id for p in critical_projects],
            analysis_timestamp=datetime.now(),
        )


def get_normalizer(
    status_masterdata: Optional[list[BlueAntStatus]] = None,
) -> DataNormalizer:
    """Get a DataNormalizer instance."""
    return DataNormalizer(status_masterdata)
