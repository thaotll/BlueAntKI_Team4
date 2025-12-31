"""
Pydantic models representing raw BlueAnt API responses.
These models map directly to the JSON structures returned by BlueAnt REST API.
"""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


# =============================================================================
# Project Entity (/v1/projects/{projectId})
# =============================================================================


class BlueAntProject(BaseModel):
    """
    Raw project entity from BlueAnt API.
    Contains status text, scope/subject, and status fields.
    """

    id: int | str = Field(..., description="Unique project identifier")
    name: str = Field(..., description="Project name")
    number: Optional[str] = Field(None, description="Project number")
    description: Optional[str] = Field(None, description="Project description / scope")
    status_text: Optional[str] = Field(
        None, alias="statusText", description="Free-text status field"
    )
    status_id: Optional[int | str] = Field(
        None, alias="statusId", description="Reference to status masterdata"
    )
    type_id: Optional[int] = Field(None, alias="typeId", description="Project type ID")
    priority_id: Optional[int] = Field(None, alias="priorityId", description="Priority ID")
    department_id: Optional[int] = Field(None, alias="departmentId", description="Department ID")
    owner_id: Optional[int | str] = Field(None, alias="ownerId", description="Project owner ID")
    owner_name: Optional[str] = Field(
        None, alias="ownerName", description="Project owner name"
    )
    project_leader_id: Optional[int] = Field(
        None, alias="projectLeaderId", description="Project leader ID"
    )
    portfolio_ids: Optional[list[int]] = Field(
        None, alias="portfolioIds", description="Associated portfolio IDs"
    )
    portfolio_id: Optional[str] = Field(
        None, alias="portfolioId", description="Associated portfolio ID (single)"
    )
    start: Optional[date] = Field(
        None, description="Project start date"
    )
    end: Optional[date] = Field(
        None, description="Planned project end date"
    )
    start_date: Optional[date] = Field(
        None, alias="startDate", description="Project start date (alt)"
    )
    end_date: Optional[date] = Field(
        None, alias="endDate", description="Planned project end date (alt)"
    )
    is_template: Optional[bool] = Field(None, alias="isTemplate")
    is_archived: Optional[bool] = Field(None, alias="isArchived")
    planning_type: Optional[str] = Field(None, alias="planningType")
    billing_type: Optional[str] = Field(None, alias="billingType")
    custom_fields: Optional[dict] = Field(None, alias="customFields")
    created_at: Optional[datetime] = Field(
        None, alias="createdAt", description="Creation timestamp"
    )
    updated_at: Optional[datetime] = Field(
        None, alias="updatedAt", description="Last update timestamp"
    )

    class Config:
        populate_by_name = True

    @property
    def effective_start_date(self) -> Optional[date]:
        """Get the effective start date from either field."""
        return self.start or self.start_date

    @property
    def effective_end_date(self) -> Optional[date]:
        """Get the effective end date from either field."""
        return self.end or self.end_date


# =============================================================================
# Planning Entries (/v1/projects/{projectId}/planningentries)
# =============================================================================


class BlueAntPlanningEntry(BaseModel):
    """
    Planning entry representing effort planning, milestones, or forecasts.
    """

    id: int | str = Field(..., description="Planning entry ID")
    number: Optional[str] = Field(None, description="Entry number (e.g. '1.1')")
    name: Optional[str] = Field(None, description="Entry name / milestone name")
    description: Optional[str] = Field(None, description="Entry description")

    entry_type: Optional[str] = Field(
        None,
        alias="type",
        description="Type of entry: 'WORK', 'DURATION', 'MILESTONE', etc.",
    )
    limitation: Optional[str] = Field(
        None, description="Limitation type (Normal, StartsAt, etc.)"
    )
    parent_id: Optional[int] = Field(None, alias="parentId", description="Parent entry ID")
    sort_id: Optional[int] = Field(None, alias="sortId", description="Sort order")
    is_collective_task: Optional[bool] = Field(
        None, alias="isCollectiveTask", description="Is a summary/collective task"
    )

    # Effort values
    work_planned_minutes: Optional[float] = Field(
        None, alias="workPlannedMinutes", description="Planned work in minutes"
    )
    work_actual_minutes: Optional[float] = Field(
        None, alias="workActualMinutes", description="Actual work in minutes"
    )
    work_estimated_minutes: Optional[float] = Field(
        None, alias="workEstimatedMinutes", description="Estimated work in minutes"
    )
    work_planned_days: Optional[float] = Field(
        None, alias="workPlannedDays", description="Planned work in days"
    )
    work_actual_days: Optional[float] = Field(
        None, alias="workActualDays", description="Actual work in days"
    )
    duration_minutes: Optional[float] = Field(
        None, alias="durationMinutes", description="Duration in minutes"
    )
    duration_days: Optional[float] = Field(
        None, alias="durationDays", description="Duration in days"
    )

    # Legacy effort fields
    planned_effort: Optional[float] = Field(
        None, alias="plannedEffort", description="Planned effort in hours"
    )
    actual_effort: Optional[float] = Field(
        None, alias="actualEffort", description="Actual effort in hours"
    )
    forecast_effort: Optional[float] = Field(
        None, alias="forecastEffort", description="Forecasted total effort"
    )

    # Dates
    start: Optional[datetime] = Field(None, description="Start date/time")
    end: Optional[datetime] = Field(None, description="End date/time")
    start_wished: Optional[str] = Field(None, alias="startWished", description="Wished start date")
    reporting_date: Optional[str] = Field(
        None, alias="reportingDate", description="Reporting reference date"
    )
    planned_date: Optional[date] = Field(
        None, alias="plannedDate", description="Planned date (for milestones)"
    )
    actual_date: Optional[date] = Field(
        None, alias="actualDate", description="Actual date (for milestones)"
    )
    baseline_date: Optional[date] = Field(
        None, alias="baselineDate", description="Baseline / reference date"
    )

    # Progress
    progress_actual: Optional[float] = Field(
        None, alias="progressActual", description="Actual progress percentage (0-100)"
    )
    progress_percent: Optional[float] = Field(
        None, alias="progressPercent", description="Progress percentage (legacy)"
    )

    # Billing
    billable_status: Optional[str] = Field(
        None, alias="billableStatus", description="Billable status"
    )

    # Status
    status: Optional[str] = Field(None, description="Entry status")
    is_milestone: Optional[bool] = Field(
        None, alias="isMilestone", description="Flag indicating if this is a milestone"
    )

    class Config:
        populate_by_name = True

    @property
    def is_likely_milestone(self) -> bool:
        """Determine if this entry is likely a milestone."""
        if self.is_milestone:
            return True
        has_no_work = (self.work_planned_minutes or 0) == 0
        same_start_end = self.start and self.end and self.start == self.end
        return has_no_work and same_start_end

    @property
    def planned_effort_hours(self) -> float:
        """Get planned effort in hours."""
        if self.work_planned_minutes:
            return self.work_planned_minutes / 60.0
        if self.planned_effort:
            return self.planned_effort
        return 0.0

    @property
    def actual_effort_hours(self) -> float:
        """Get actual effort in hours."""
        if self.work_actual_minutes:
            return self.work_actual_minutes / 60.0
        if self.actual_effort:
            return self.actual_effort
        return 0.0


# =============================================================================
# Project Status Masterdata (/v1/masterdata/projects/statuses)
# =============================================================================


class BlueAntStatus(BaseModel):
    """Status masterdata entry (traffic light / status indicator)."""

    id: str = Field(..., description="Status ID")
    name: str = Field(..., description="Status label (e.g., 'On Track', 'At Risk')")
    color: Optional[str] = Field(
        None, description="Status color (e.g., 'green', 'yellow', 'red', or hex)"
    )
    description: Optional[str] = Field(None, description="Status description")
    order: Optional[int] = Field(None, description="Display order")

    class Config:
        populate_by_name = True


# =============================================================================
# Portfolio (/v1/portfolios/{portfolioId})
# =============================================================================


class BlueAntPortfolio(BaseModel):
    """Portfolio entity containing a collection of projects."""

    id: int | str = Field(..., description="Portfolio ID")
    name: str = Field(..., description="Portfolio name")
    number: Optional[str] = Field(None, description="Portfolio number")
    description: Optional[str] = Field(None, description="Portfolio description")
    color: Optional[str] = Field(None, description="Portfolio color")
    active: Optional[bool] = Field(None, description="Is portfolio active")
    owner_id: Optional[str] = Field(None, alias="ownerId", description="Portfolio owner ID")
    owner_name: Optional[str] = Field(
        None, alias="ownerName", description="Portfolio owner name"
    )
    project_ids: list[int | str] = Field(
        default_factory=list,
        alias="projectIds",
        description="List of project IDs in this portfolio",
    )
    date_from: Optional[datetime] = Field(
        None, alias="dateFrom", description="Portfolio start date"
    )
    date_to: Optional[datetime] = Field(
        None, alias="dateTo", description="Portfolio end date"
    )
    created_at: Optional[datetime] = Field(
        None, alias="createdAt", description="Creation timestamp"
    )

    class Config:
        populate_by_name = True
