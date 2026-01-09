"""
Data normalization service.
Transforms raw BlueAnt data into normalized structures for LLM analysis.
"""

import logging
import re
from collections import Counter
from datetime import date, datetime
from typing import List, Optional, Tuple, Union

from app.models.blueant import (
    BlueAntCustomer,
    BlueAntDepartment,
    BlueAntPlanningEntry,
    BlueAntPortfolio,
    BlueAntPriority,
    BlueAntProject,
    BlueAntProjectType,
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

    def __init__(
        self,
        status_masterdata: Optional[List[BlueAntStatus]] = None,
        priority_masterdata: Optional[List[BlueAntPriority]] = None,
        type_masterdata: Optional[List[BlueAntProjectType]] = None,
        department_masterdata: Optional[List[BlueAntDepartment]] = None,
        customer_masterdata: Optional[List[BlueAntCustomer]] = None,
    ):
        self.status_map: dict[str, BlueAntStatus] = {}
        self.priority_map: dict[str, BlueAntPriority] = {}
        self.type_map: dict[str, BlueAntProjectType] = {}
        self.department_map: dict[str, BlueAntDepartment] = {}
        self.customer_map: dict[str, BlueAntCustomer] = {}
        
        if status_masterdata:
            self.status_map = {str(s.id): s for s in status_masterdata}
        if priority_masterdata:
            self.priority_map = {str(p.id): p for p in priority_masterdata}
        if type_masterdata:
            self.type_map = {str(t.id): t for t in type_masterdata}
        if department_masterdata:
            self.department_map = {str(d.id): d for d in department_masterdata}
        if customer_masterdata:
            self.customer_map = {str(c.id): c for c in customer_masterdata}

    def set_all_masterdata(self, masterdata: dict) -> None:
        """Update all masterdata mappings from a dict."""
        if masterdata.get("statuses"):
            self.status_map = {str(s.id): s for s in masterdata["statuses"]}
            logger.info(f"Loaded {len(self.status_map)} status entries")
        if masterdata.get("priorities"):
            self.priority_map = {str(p.id): p for p in masterdata["priorities"]}
            logger.info(f"Loaded {len(self.priority_map)} priority entries")
        if masterdata.get("types"):
            self.type_map = {str(t.id): t for t in masterdata["types"]}
            logger.info(f"Loaded {len(self.type_map)} type entries")
        if masterdata.get("departments"):
            self.department_map = {str(d.id): d for d in masterdata["departments"]}
            logger.info(f"Loaded {len(self.department_map)} department entries")
        if masterdata.get("customers"):
            self.customer_map = {str(c.id): c for c in masterdata["customers"]}
            logger.info(f"Loaded {len(self.customer_map)} customer entries")

    def set_status_masterdata(self, status_masterdata: List[BlueAntStatus]) -> None:
        """Update status masterdata mapping."""
        self.status_map = {str(s.id): s for s in status_masterdata}
        logger.info(f"Loaded {len(self.status_map)} status entries")

    def get_priority_name(self, priority_id: Optional[Union[int, str]]) -> Optional[str]:
        """Resolve priority ID to display name."""
        if priority_id is None:
            return None
        priority = self.priority_map.get(str(priority_id))
        return priority.display_name if priority else None

    def get_type_name(self, type_id: Optional[Union[int, str]]) -> Optional[str]:
        """Resolve project type ID to display name."""
        if type_id is None:
            return None
        ptype = self.type_map.get(str(type_id))
        return ptype.display_name if ptype else None

    def get_department_name(self, department_id: Optional[Union[int, str]]) -> Optional[str]:
        """Resolve department ID to display name."""
        if department_id is None:
            return None
        dept = self.department_map.get(str(department_id))
        return dept.display_name if dept else None

    def get_customer_name(self, customer_id: Optional[Union[int, str]]) -> Optional[str]:
        """Resolve customer ID to display name."""
        if customer_id is None:
            return None
        customer = self.customer_map.get(str(customer_id))
        return customer.display_name if customer else None

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

    def _derive_status_from_memo(self, memo: str) -> Tuple[Optional[str], StatusColor]:
        """
        Derive project status from statusMemo text.
        Analyzes the memo content to determine project state.
        """
        memo_lower = memo.lower()
        
        # Check for completion indicators
        completion_keywords = [
            "erfolgreich abgeschlossen", "abgeschlossen", "completed", 
            "fertiggestellt", "beendet", "finished", "closed",
            "projekt wurde am", "go-live wurde"
        ]
        if any(kw in memo_lower for kw in completion_keywords):
            return "Abgeschlossen", StatusColor.GREEN
        
        # Check for critical/problem indicators
        critical_keywords = [
            "kritisch", "critical", "blockiert", "blocked", "stopped",
            "massive probleme", "erhebliche verzögerung", "gestoppt"
        ]
        if any(kw in memo_lower for kw in critical_keywords):
            return "Kritisch", StatusColor.RED
        
        # Check for at-risk indicators
        risk_keywords = [
            "verzögerung", "delay", "risiko", "risk", "probleme",
            "schwierigkeiten", "issues", "herausforderung"
        ]
        if any(kw in memo_lower for kw in risk_keywords):
            return "Gefährdet", StatusColor.YELLOW
        
        # Check for early/planning phase
        planning_keywords = [
            "prephase", "startphase", "planungsphase", "vorbereitung",
            "startet gerade", "wird gestartet", "initialisierung"
        ]
        if any(kw in memo_lower for kw in planning_keywords):
            return "In Planung", StatusColor.GRAY
        
        # Check for active/in progress
        active_keywords = [
            "in bearbeitung", "in progress", "läuft", "aktiv",
            "durchführung", "umsetzung"
        ]
        if any(kw in memo_lower for kw in active_keywords):
            return "In Bearbeitung", StatusColor.GREEN
        
        # Default: Unknown but extract first sentence as hint
        return None, StatusColor.GRAY

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
        self, status_id: Optional[Union[int, str, dict]]
    ) -> Tuple[Optional[str], StatusColor]:
        """Get status label and color from status ID or embedded object."""
        if not status_id:
            return None, StatusColor.GRAY
        
        # Handle embedded status object (when API returns expanded data)
        if isinstance(status_id, dict):
            status_text = status_id.get("text") or status_id.get("name")
            status_color = status_id.get("color")
            return status_text, self.map_status_color(status_color)
        
        # Handle status ID lookup from masterdata
        status_id_str = str(status_id)
        if status_id_str not in self.status_map:
            return None, StatusColor.GRAY

        status = self.status_map[status_id_str]
        return status.display_name, self.map_status_color(status.color)

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
        planning_entries: Optional[List[BlueAntPlanningEntry]] = None,
    ) -> NormalizedProject:
        """Transform raw BlueAnt project into normalized structure."""
        entries = planning_entries or []

        # Map status - try multiple sources
        status_label = None
        status_color = StatusColor.GRAY
        
        # 1. Try embedded status object
        if project.status and isinstance(project.status, dict):
            status_label, status_color = self.get_status_info(project.status)
        
        # 2. Try status ID from masterdata
        if not status_label and project.status_id:
            status_label, status_color = self.get_status_info(project.status_id)
        
        # 3. Try to derive status from statusMemo text
        if not status_label and project.status_memo:
            status_label, status_color = self._derive_status_from_memo(project.status_memo)
            if status_label:
                logger.info(f"Derived status '{status_label}' from memo for project '{project.name}'")

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

        # Resolve IDs to names via masterdata
        priority_name = self.get_priority_name(project.priority_id)
        type_name = self.get_type_name(project.type_id)
        department_name = self.get_department_name(project.department_id)
        
        # Get customer name from clients array (first client)
        customer_name = None
        if project.clients and len(project.clients) > 0:
            first_client = project.clients[0]
            client_id = first_client.get("clientId") or first_client.get("id")
            customer_name = self.get_customer_name(client_id)

        return NormalizedProject(
            id=str(project.id),
            name=project.name,
            portfolio_id=str(project.portfolio_ids[0]) if project.portfolio_ids else project.portfolio_id,
            owner_name=project.owner_name,
            department_name=department_name,
            customer_name=customer_name,
            type_name=type_name,
            priority_name=priority_name,
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
            status_text=self.clean_text(project.status_memo or project.status_text),
            scope_summary=self.clean_text(project.subject_memo or project.description),
            problem_summary=self.clean_text(project.problem_memo),
            objective_summary=self.clean_text(project.objective_memo),
            is_potentially_critical=is_critical,
            criticality_reasons=criticality_reasons,
            last_updated=project.updated_at,
        )

    def normalize_portfolio(
        self,
        portfolio: BlueAntPortfolio,
        projects: List[NormalizedProject],
    ) -> NormalizedPortfolio:
        """Create normalized portfolio from portfolio entity and normalized projects."""
        status_counter: Counter[Tuple[str, StatusColor]] = Counter()
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
    status_masterdata: Optional[List[BlueAntStatus]] = None,
) -> DataNormalizer:
    """Get a DataNormalizer instance."""
    return DataNormalizer(status_masterdata)
