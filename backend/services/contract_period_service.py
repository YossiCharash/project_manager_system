"""
Contract Period Service - manages contract periods for projects.
"""
from __future__ import annotations

import logging
from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from dateutil.relativedelta import relativedelta

from backend.models.contract_period import ContractPeriod
from backend.repositories.contract_period_repository import ContractPeriodRepository
from backend.repositories.project_repository import ProjectRepository

logger = logging.getLogger(__name__)


class ContractPeriodService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ContractPeriodRepository(db)

    async def get_current_contract_period(self, project_id: int) -> Optional[ContractPeriod]:
        """Get the contract period that contains today's date."""
        today = date.today()
        periods = await self.repo.get_by_project(project_id)
        for period in periods:
            if period.start_date <= today < period.end_date:
                return period
        # Return the most recent period if none contains today
        if periods:
            return periods[0]
        return None

    async def get_previous_contracts_by_year(self, project_id: int) -> dict:
        """Get all contract periods grouped by year."""
        periods = await self.repo.get_by_project(project_id)
        by_year: dict[int, list[ContractPeriod]] = {}
        for period in periods:
            year = period.contract_year
            by_year.setdefault(year, []).append(period)
        return by_year

    async def generate_initial_periods_by_duration(
        self,
        project_id: int,
        start_date: date,
        contract_duration_months: int,
        end_date: Optional[date] = None,
    ) -> list[ContractPeriod]:
        """Generate initial contract periods from start_date up to today (or end_date)."""
        if contract_duration_months <= 0:
            return []

        today = date.today()
        target = end_date if end_date else today + relativedelta(months=contract_duration_months)
        periods = []
        current_start = start_date
        max_iterations = 200

        for _ in range(max_iterations):
            current_end = current_start + relativedelta(months=contract_duration_months)
            contract_year = current_start.year

            year_count = await self.repo.count_by_year(project_id, contract_year)
            year_index = year_count + 1

            period = ContractPeriod(
                project_id=project_id,
                start_date=current_start,
                end_date=current_end,
                contract_year=contract_year,
                year_index=year_index,
            )
            created = await self.repo.create(period)
            periods.append(created)

            if current_end >= target:
                # Update project end_date
                try:
                    proj_repo = ProjectRepository(self.db)
                    project = await proj_repo.get_by_id(project_id)
                    if project:
                        project.end_date = current_end
                        await proj_repo.update(project)
                except Exception:
                    logger.warning("Could not update project end_date", exc_info=True)
                break

            current_start = current_end

        return periods

    async def check_and_renew_contract(self, project_id: int) -> Optional[ContractPeriod]:
        """
        Check if the current contract period has ended and create a new one if needed.
        Returns the newly created period if renewal happened, else None.
        """
        try:
            proj_repo = ProjectRepository(self.db)
            project = await proj_repo.get_by_id(project_id)
            if not project or not project.end_date:
                return None

            today = date.today()
            if project.end_date > today:
                return None

            duration = getattr(project, 'contract_duration_months', None) or 12
            new_start = project.end_date
            new_end = new_start + relativedelta(months=duration)
            contract_year = new_start.year

            # Check if this period already exists
            existing = await self.repo.get_by_exact_dates(project_id, new_start, new_end)
            if existing:
                return None

            year_count = await self.repo.count_by_year(project_id, contract_year)
            year_index = year_count + 1

            period = ContractPeriod(
                project_id=project_id,
                start_date=new_start,
                end_date=new_end,
                contract_year=contract_year,
                year_index=year_index,
            )
            created = await self.repo.create(period)

            # Update project end_date
            project.end_date = new_end
            await proj_repo.update(project)

            return created
        except Exception:
            logger.exception("Error in check_and_renew_contract for project %s", project_id)
            return None
