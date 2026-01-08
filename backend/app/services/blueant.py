"""
BlueAnt REST API Client.
Wraps all API calls to BlueAnt for fetching project portfolio data.
"""

import logging
from typing import List, Optional, Union

import httpx

from app.config import get_settings
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

logger = logging.getLogger(__name__)


class BlueAntClientError(Exception):
    """Exception raised for BlueAnt API errors."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class BlueAntService:
    """
    HTTP client for BlueAnt REST API.

    Provides methods to fetch:
    - Portfolio and project data
    - Planning entries (effort, milestones, forecasts)
    - Status masterdata
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: float = 30.0,
    ):
        settings = get_settings()
        self.base_url = (base_url or settings.blueant_base_url).rstrip("/")
        self.api_key = api_key or settings.blueant_api_key
        self.timeout = timeout

        if not self.api_key:
            logger.warning("BlueAnt API key not configured!")

    def _get_headers(self) -> dict[str, str]:
        """Build request headers with authentication."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "BA-Authorization": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict] = None,
        json_data: Optional[dict] = None,
    ) -> Union[dict, list]:
        """Execute HTTP request to BlueAnt API."""
        url = f"{self.base_url}{endpoint}"
        logger.debug(f"BlueAnt API request: {method} {url}")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self._get_headers(),
                    params=params,
                    json=json_data,
                )

            if response.status_code >= 400:
                error_msg = f"BlueAnt API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise BlueAntClientError(error_msg, status_code=response.status_code)

            return response.json()

        except httpx.TimeoutException as e:
            error_msg = f"BlueAnt API timeout: {url}"
            logger.error(error_msg)
            raise BlueAntClientError(error_msg) from e
        except httpx.RequestError as e:
            error_msg = f"BlueAnt API request failed: {e}"
            logger.error(error_msg)
            raise BlueAntClientError(error_msg) from e

    # =========================================================================
    # Portfolio Endpoints
    # =========================================================================

    async def get_portfolio(self, portfolio_id: Union[str, int]) -> BlueAntPortfolio:
        """Fetch portfolio by ID."""
        data = await self._request("GET", f"/v1/portfolios/{portfolio_id}")
        if isinstance(data, dict) and "portfolio" in data:
            return BlueAntPortfolio.model_validate(data["portfolio"])
        return BlueAntPortfolio.model_validate(data)

    async def get_all_portfolios(self) -> List[BlueAntPortfolio]:
        """Fetch all portfolios."""
        data = await self._request("GET", "/v1/portfolios")

        if isinstance(data, dict) and "portfolios" in data:
            return [BlueAntPortfolio.model_validate(p) for p in data["portfolios"]]
        elif isinstance(data, list):
            return [BlueAntPortfolio.model_validate(p) for p in data]
        elif isinstance(data, dict) and "items" in data:
            return [BlueAntPortfolio.model_validate(p) for p in data["items"]]
        return []

    async def search_portfolios(self, name: str) -> List[BlueAntPortfolio]:
        """Search portfolios by name (case-insensitive partial match)."""
        portfolios = await self.get_all_portfolios()
        name_lower = name.lower()
        return [p for p in portfolios if name_lower in p.name.lower()]

    async def get_portfolio_projects(self, portfolio_id: str) -> List[BlueAntProject]:
        """Fetch all projects belonging to a portfolio."""
        try:
            portfolio = await self.get_portfolio(portfolio_id)
            if portfolio.project_ids:
                projects = []
                for project_id in portfolio.project_ids:
                    try:
                        project = await self.get_project(project_id)
                        projects.append(project)
                    except BlueAntClientError as e:
                        logger.warning(f"Failed to fetch project {project_id}: {e}")
                return projects
        except BlueAntClientError:
            pass

        # Fallback: Get all projects and filter by portfolio
        data = await self._request(
            "GET", 
            "/v1/projects", 
            params={
                "portfolioId": portfolio_id,
                "includeMemoFields": "true"
            }
        )

        if isinstance(data, list):
            return [BlueAntProject.model_validate(p) for p in data]
        elif isinstance(data, dict) and "items" in data:
            return [BlueAntProject.model_validate(p) for p in data["items"]]
        elif isinstance(data, dict) and "projects" in data:
            return [BlueAntProject.model_validate(p) for p in data["projects"]]
        return []

    # =========================================================================
    # Project Endpoints
    # =========================================================================

    async def get_project(self, project_id: Union[str, int]) -> BlueAntProject:
        """Fetch single project by ID with memo fields."""
        data = await self._request(
            "GET", 
            f"/v1/projects/{project_id}",
            params={"includeMemoFields": "true"}
        )
        if isinstance(data, dict) and "project" in data:
            return BlueAntProject.model_validate(data["project"])
        return BlueAntProject.model_validate(data)

    async def get_all_projects(self) -> List[BlueAntProject]:
        """Fetch all projects."""
        data = await self._request("GET", "/v1/projects")

        if isinstance(data, dict) and "projects" in data:
            return [BlueAntProject.model_validate(p) for p in data["projects"]]
        elif isinstance(data, list):
            return [BlueAntProject.model_validate(p) for p in data]
        elif isinstance(data, dict) and "items" in data:
            return [BlueAntProject.model_validate(p) for p in data["items"]]
        return []

    # =========================================================================
    # Planning Entries
    # =========================================================================

    async def get_project_planning_entries(
        self, project_id: Union[str, int]
    ) -> List[BlueAntPlanningEntry]:
        """Fetch planning entries for a project."""
        data = await self._request(
            "GET", f"/v1/projects/{project_id}/planningentries"
        )

        if isinstance(data, dict) and "entries" in data:
            return [BlueAntPlanningEntry.model_validate(e) for e in data["entries"]]
        elif isinstance(data, list):
            return [BlueAntPlanningEntry.model_validate(e) for e in data]
        elif isinstance(data, dict) and "items" in data:
            return [BlueAntPlanningEntry.model_validate(e) for e in data["items"]]
        return []

    # =========================================================================
    # Status Masterdata
    # =========================================================================

    async def get_status_masterdata(self) -> List[BlueAntStatus]:
        """Fetch status masterdata (traffic light definitions)."""
        data = await self._request("GET", "/v1/masterdata/projects/statuses")

        if isinstance(data, list):
            return [BlueAntStatus.model_validate(s) for s in data]
        elif isinstance(data, dict) and "items" in data:
            return [BlueAntStatus.model_validate(s) for s in data["items"]]
        return []

    async def get_priority_masterdata(self) -> List[BlueAntPriority]:
        """Fetch priority masterdata."""
        data = await self._request("GET", "/v1/masterdata/projects/priorities")

        if isinstance(data, list):
            return [BlueAntPriority.model_validate(p) for p in data]
        elif isinstance(data, dict) and "items" in data:
            return [BlueAntPriority.model_validate(p) for p in data["items"]]
        return []

    async def get_project_type_masterdata(self) -> List[BlueAntProjectType]:
        """Fetch project type masterdata."""
        data = await self._request("GET", "/v1/masterdata/projects/types")

        if isinstance(data, list):
            return [BlueAntProjectType.model_validate(t) for t in data]
        elif isinstance(data, dict) and "items" in data:
            return [BlueAntProjectType.model_validate(t) for t in data["items"]]
        return []

    async def get_department_masterdata(self) -> List[BlueAntDepartment]:
        """Fetch department masterdata."""
        data = await self._request("GET", "/v1/masterdata/departments")

        if isinstance(data, list):
            return [BlueAntDepartment.model_validate(d) for d in data]
        elif isinstance(data, dict) and "items" in data:
            return [BlueAntDepartment.model_validate(d) for d in data["items"]]
        elif isinstance(data, dict) and "departments" in data:
            return [BlueAntDepartment.model_validate(d) for d in data["departments"]]
        return []

    async def get_customer_masterdata(self) -> List[BlueAntCustomer]:
        """Fetch customer masterdata."""
        data = await self._request("GET", "/v1/masterdata/customers")

        if isinstance(data, list):
            return [BlueAntCustomer.model_validate(c) for c in data]
        elif isinstance(data, dict) and "items" in data:
            return [BlueAntCustomer.model_validate(c) for c in data["items"]]
        elif isinstance(data, dict) and "customers" in data:
            return [BlueAntCustomer.model_validate(c) for c in data["customers"]]
        return []

    async def get_all_masterdata(self) -> dict:
        """Fetch all relevant masterdata in parallel."""
        import asyncio
        
        statuses, priorities, types, departments, customers = await asyncio.gather(
            self.get_status_masterdata(),
            self.get_priority_masterdata(),
            self.get_project_type_masterdata(),
            self.get_department_masterdata(),
            self.get_customer_masterdata(),
            return_exceptions=True
        )
        
        return {
            "statuses": statuses if not isinstance(statuses, Exception) else [],
            "priorities": priorities if not isinstance(priorities, Exception) else [],
            "types": types if not isinstance(types, Exception) else [],
            "departments": departments if not isinstance(departments, Exception) else [],
            "customers": customers if not isinstance(customers, Exception) else [],
        }


def get_blueant_service() -> BlueAntService:
    """Get a BlueAnt service instance with default settings."""
    return BlueAntService()
