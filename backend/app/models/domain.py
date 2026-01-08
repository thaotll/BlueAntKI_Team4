"""
Normalized data models for internal use.
These models represent cleaned, structured project data ready for LLM analysis.
"""

from datetime import date, datetime
from enum import Enum
from typing import List, Optional, Union

from pydantic import BaseModel, Field


class StatusColor(str, Enum):
    """Standardized status traffic light colors."""

    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"
    GRAY = "gray"


class MilestoneStatus(str, Enum):
    """Milestone completion status."""

    COMPLETED = "completed"
    ON_TRACK = "on_track"
    AT_RISK = "at_risk"
    DELAYED = "delayed"
    NOT_STARTED = "not_started"


class NormalizedMilestone(BaseModel):
    """Normalized milestone with clear status indication."""

    name: str = Field(..., description="Milestone name")
    planned_date: Optional[date] = Field(None, description="Originally planned date")
    actual_date: Optional[date] = Field(
        None, description="Actual completion date (if completed)"
    )
    forecast_date: Optional[date] = Field(None, description="Current forecast date")
    status: MilestoneStatus = Field(
        default=MilestoneStatus.NOT_STARTED, description="Current milestone status"
    )
    delay_days: int = Field(
        default=0, description="Delay in days (positive = late, negative = early)"
    )
    description: Optional[str] = Field(None, description="Milestone description")


class NormalizedProject(BaseModel):
    """Normalized project data structure ready for LLM analysis."""

    # Identifiers
    id: str = Field(..., description="Unique project identifier")
    name: str = Field(..., description="Project name")
    portfolio_id: Optional[str] = Field(None, description="Parent portfolio ID")

    # Ownership & Organization
    owner_name: Optional[str] = Field(None, description="Project owner/manager name")
    department_name: Optional[str] = Field(None, description="Department name (resolved from ID)")
    customer_name: Optional[str] = Field(None, description="Customer/client name (resolved from ID)")
    
    # Project Classification
    type_name: Optional[str] = Field(None, description="Project type (resolved from ID)")
    priority_name: Optional[str] = Field(None, description="Priority level (resolved from ID)")

    # Status Traffic Light
    status_label: Optional[str] = Field(
        None, description="Human-readable status label (e.g., 'On Track', 'At Risk')"
    )
    status_color: StatusColor = Field(
        default=StatusColor.GRAY, description="Traffic light color"
    )

    # Effort & Planning
    planned_effort_hours: float = Field(
        default=0.0, description="Total planned effort in hours"
    )
    actual_effort_hours: float = Field(
        default=0.0, description="Total actual effort in hours"
    )
    forecast_effort_hours: float = Field(
        default=0.0, description="Forecasted total effort in hours"
    )
    effort_deviation_percent: float = Field(
        default=0.0,
        description="Deviation from plan in percent ((actual-planned)/planned * 100)",
    )
    progress_percent: float = Field(
        default=0.0, description="Overall progress percentage (0-100)"
    )

    # Dates
    start_date: Optional[date] = Field(None, description="Project start date")
    end_date_planned: Optional[date] = Field(None, description="Planned end date")
    end_date_forecast: Optional[date] = Field(None, description="Forecasted end date")
    delay_days: int = Field(
        default=0,
        description="Schedule delay in days (positive = late)",
    )

    # Milestones
    milestones: List[NormalizedMilestone] = Field(
        default_factory=list, description="List of project milestones"
    )
    milestones_total: int = Field(default=0, description="Total number of milestones")
    milestones_completed: int = Field(
        default=0, description="Number of completed milestones"
    )
    milestones_delayed: int = Field(
        default=0, description="Number of delayed milestones"
    )

    # Text Fields
    status_text: Optional[str] = Field(
        None,
        description="Status text field - current status summary",
        max_length=2000,
    )
    scope_summary: Optional[str] = Field(
        None,
        description="Project scope/subject/content summary",
        max_length=2000,
    )
    problem_summary: Optional[str] = Field(
        None,
        description="Known problems and challenges",
        max_length=2000,
    )
    objective_summary: Optional[str] = Field(
        None,
        description="Project objectives and goals",
        max_length=2000,
    )

    # Derived Indicators
    is_potentially_critical: bool = Field(
        default=False,
        description="Heuristic flag indicating potential criticality",
    )
    criticality_reasons: List[str] = Field(
        default_factory=list,
        description="Reasons why project may be critical",
    )

    # Metadata
    last_updated: Optional[datetime] = Field(
        None, description="Last data update timestamp"
    )


class ProjectsPerStatus(BaseModel):
    """Aggregation of project counts per status."""

    status_label: str
    status_color: StatusColor
    count: int


class NormalizedPortfolio(BaseModel):
    """Normalized portfolio with all projects and aggregated metrics."""

    # Identifiers
    id: Union[str, int] = Field(..., description="Portfolio identifier")
    name: str = Field(..., description="Portfolio name")
    description: Optional[str] = Field(None, description="Portfolio description")
    owner_name: Optional[str] = Field(None, description="Portfolio owner name")

    # Projects
    projects: List[NormalizedProject] = Field(
        default_factory=list, description="List of normalized projects"
    )

    # Aggregations
    projects_per_status: List[ProjectsPerStatus] = Field(
        default_factory=list, description="Project count per status"
    )
    total_projects: int = Field(default=0, description="Total number of projects")

    # Effort Aggregations
    total_planned_effort_hours: float = Field(
        default=0.0, description="Sum of planned effort across all projects"
    )
    total_actual_effort_hours: float = Field(
        default=0.0, description="Sum of actual effort across all projects"
    )
    total_forecast_effort_hours: float = Field(
        default=0.0, description="Sum of forecasted effort across all projects"
    )

    # Critical Projects
    critical_projects_count: int = Field(
        default=0, description="Number of potentially critical projects"
    )
    critical_project_ids: List[str] = Field(
        default_factory=list, description="IDs of critical projects"
    )

    # Metadata
    analysis_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(),
        description="Timestamp when this data was compiled",
    )
