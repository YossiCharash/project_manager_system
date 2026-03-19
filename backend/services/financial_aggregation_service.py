"""
Financial Aggregation Service - consolidated financial summaries for parent projects.
"""
from __future__ import annotations

import logging
from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from backend.models.project import Project
from backend.models.transaction import Transaction
from backend.repositories.project_repository import ProjectRepository
from backend.repositories.transaction_repository import TransactionRepository

logger = logging.getLogger(__name__)


class FinancialAggregationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.proj_repo = ProjectRepository(db)
        self.tx_repo = TransactionRepository(db)

    async def _get_parent_project(self, parent_project_id: int) -> Project:
        project = await self.proj_repo.get_by_id(parent_project_id)
        if not project:
            raise ValueError(f"Project {parent_project_id} not found")
        return project

    async def _get_subproject_ids(self, parent_project_id: int) -> list[int]:
        """Get IDs of the parent project and all subprojects."""
        from sqlalchemy import select
        from backend.models.subproject import Subproject
        result = await self.db.execute(
            select(Subproject.subproject_id).where(Subproject.parent_project_id == parent_project_id)
        )
        sub_ids = [row[0] for row in result.all()]
        return [parent_project_id] + sub_ids

    async def _aggregate_financials(
        self, project_ids: list[int], start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> dict:
        from sqlalchemy import case
        conditions = [Transaction.project_id.in_(project_ids), Transaction.from_fund == False]  # noqa: E712
        if start_date:
            conditions.append(Transaction.tx_date >= start_date)
        if end_date:
            conditions.append(Transaction.tx_date <= end_date)

        result = await self.db.execute(
            select(
                func.coalesce(func.sum(case((Transaction.type == "Income", Transaction.amount), else_=0)), 0).label("income"),
                func.coalesce(func.sum(case((Transaction.type == "Expense", Transaction.amount), else_=0)), 0).label("expense"),
            ).where(and_(*conditions))
        )
        row = result.one()
        income = float(row.income or 0)
        expense = float(row.expense or 0)
        return {"total_income": income, "total_expense": expense, "total_profit": income - expense}

    async def get_parent_project_financial_summary(
        self,
        parent_project_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> dict:
        project = await self._get_parent_project(parent_project_id)
        project_ids = await self._get_subproject_ids(parent_project_id)
        financials = await self._aggregate_financials(project_ids, start_date, end_date)
        return {
            "project_id": parent_project_id,
            "project_name": project.name,
            **financials,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
        }

    async def get_monthly_financial_summary(self, parent_project_id: int, year: int, month: int) -> dict:
        from datetime import date as date_type
        start = date_type(year, month, 1)
        if month == 12:
            end = date_type(year + 1, 1, 1)
        else:
            end = date_type(year, month + 1, 1)
        project = await self._get_parent_project(parent_project_id)
        project_ids = await self._get_subproject_ids(parent_project_id)
        financials = await self._aggregate_financials(project_ids, start, end)
        return {
            "project_id": parent_project_id,
            "year": year,
            "month": month,
            **financials,
        }

    async def get_yearly_financial_summary(self, parent_project_id: int, year: int) -> dict:
        from datetime import date as date_type
        start = date_type(year, 1, 1)
        end = date_type(year, 12, 31)
        project = await self._get_parent_project(parent_project_id)
        project_ids = await self._get_subproject_ids(parent_project_id)
        financials = await self._aggregate_financials(project_ids, start, end)
        return {
            "project_id": parent_project_id,
            "year": year,
            **financials,
        }

    async def get_custom_range_financial_summary(
        self, parent_project_id: int, start_date: date, end_date: date
    ) -> dict:
        project = await self._get_parent_project(parent_project_id)
        project_ids = await self._get_subproject_ids(parent_project_id)
        financials = await self._aggregate_financials(project_ids, start_date, end_date)
        return {
            "project_id": parent_project_id,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            **financials,
        }

    async def get_subproject_performance_comparison(
        self,
        parent_project_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> list[dict]:
        from sqlalchemy import case
        project = await self._get_parent_project(parent_project_id)
        project_ids = await self._get_subproject_ids(parent_project_id)

        performance = []
        for pid in project_ids:
            financials = await self._aggregate_financials([pid], start_date, end_date)
            proj = await self.proj_repo.get_by_id(pid)
            performance.append({
                "project_id": pid,
                "project_name": proj.name if proj else f"Project {pid}",
                **financials,
            })

        performance.sort(key=lambda x: x["total_profit"], reverse=True)
        return performance

    async def get_financial_trends(self, parent_project_id: int, years_back: int = 5) -> dict:
        from datetime import date as date_type
        await self._get_parent_project(parent_project_id)
        project_ids = await self._get_subproject_ids(parent_project_id)
        current_year = date_type.today().year
        trends = []
        for y in range(current_year - years_back + 1, current_year + 1):
            start = date_type(y, 1, 1)
            end = date_type(y, 12, 31)
            financials = await self._aggregate_financials(project_ids, start, end)
            trends.append({"year": y, **financials})
        return {
            "project_id": parent_project_id,
            "years_back": years_back,
            "trends": trends,
        }
