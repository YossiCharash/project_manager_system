"""
Report Service - generates PDF, Excel, and ZIP reports.
"""
from __future__ import annotations

import io
import logging
import zipfile
from datetime import date, datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from backend.models.transaction import Transaction
from backend.models.project import Project
from backend.repositories.project_repository import ProjectRepository
from backend.repositories.transaction_repository import TransactionRepository

logger = logging.getLogger(__name__)


class ReportService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.proj_repo = ProjectRepository(db)
        self.tx_repo = TransactionRepository(db)

    async def project_profitability(
        self, project_id: int, start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> dict:
        """Return basic profitability report for a project."""
        project = await self.proj_repo.get_by_id(project_id)
        if not project:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Project not found")

        conditions = [Transaction.project_id == project_id, Transaction.from_fund == False]  # noqa: E712
        if start_date:
            conditions.append(Transaction.tx_date >= start_date)
        if end_date:
            conditions.append(Transaction.tx_date <= end_date)

        from sqlalchemy import case
        result = await self.db.execute(
            select(
                func.coalesce(func.sum(case((Transaction.type == "Income", Transaction.amount), else_=0)), 0).label("income"),
                func.coalesce(func.sum(case((Transaction.type == "Expense", Transaction.amount), else_=0)), 0).label("expense"),
            ).where(and_(*conditions))
        )
        row = result.one()
        income = float(row.income or 0)
        expense = float(row.expense or 0)

        return {
            "project_id": project_id,
            "project_name": project.name,
            "total_income": income,
            "total_expense": expense,
            "profit": income - expense,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
        }

    async def get_dashboard_snapshot(self) -> dict:
        """Get a high-level dashboard snapshot."""
        from sqlalchemy import case
        result = await self.db.execute(
            select(
                func.coalesce(func.sum(case((Transaction.type == "Income", Transaction.amount), else_=0)), 0).label("income"),
                func.coalesce(func.sum(case((Transaction.type == "Expense", Transaction.amount), else_=0)), 0).label("expense"),
                func.count(Transaction.id).label("count"),
            ).where(Transaction.from_fund == False)  # noqa: E712
        )
        row = result.one()
        income = float(row.income or 0)
        expense = float(row.expense or 0)
        return {
            "total_income": income,
            "total_expense": expense,
            "profit": income - expense,
            "transaction_count": row.count or 0,
        }

    async def get_project_expense_categories(self, project_id: int) -> dict:
        """Get expense breakdown by category for a project."""
        from backend.models.category import Category
        result = await self.db.execute(
            select(
                Transaction.category,
                func.sum(Transaction.amount).label("total"),
            ).where(
                and_(
                    Transaction.project_id == project_id,
                    Transaction.type == "Expense",
                    Transaction.from_fund == False,  # noqa: E712
                )
            ).group_by(Transaction.category)
        )
        categories = [
            {"category": row.category or "Uncategorized", "total": float(row.total or 0)}
            for row in result.all()
        ]
        return {"project_id": project_id, "categories": categories}

    async def get_expenses_by_transaction_date(
        self,
        project_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> list[dict]:
        """Get expenses aggregated by transaction date."""
        conditions = [Transaction.type == "Expense", Transaction.from_fund == False]  # noqa: E712
        if project_id is not None:
            conditions.append(Transaction.project_id == project_id)
        if start_date:
            conditions.append(Transaction.tx_date >= start_date)
        if end_date:
            conditions.append(Transaction.tx_date <= end_date)

        result = await self.db.execute(
            select(
                Transaction.tx_date,
                func.sum(Transaction.amount).label("total"),
            ).where(and_(*conditions)).group_by(Transaction.tx_date).order_by(Transaction.tx_date)
        )
        return [
            {"date": row.tx_date.isoformat(), "total": float(row.total or 0)}
            for row in result.all()
        ]

    async def generate_custom_report(self, request, chart_images: Optional[dict] = None) -> bytes:
        """Generate a custom report. Returns bytes of the requested format."""
        if request.format == "pdf":
            return await self._generate_pdf_report(request, chart_images)
        elif request.format == "excel":
            return await self._generate_excel_report_for_request(request, chart_images)
        elif request.format == "zip":
            return await self._generate_zip_report(request, chart_images)
        raise ValueError(f"Unsupported format: {request.format}")

    async def generate_excel_report(self, project_id: int, chart_images: Optional[dict] = None) -> bytes:
        """Generate an Excel report for a project."""
        return await self._build_excel_bytes(project_id, None, None, chart_images)

    async def generate_zip_export(self, project_id: int, chart_images: Optional[dict] = None) -> bytes:
        """Generate a ZIP export for a project."""
        excel_bytes = await self._build_excel_bytes(project_id, None, None, chart_images)
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(f"project_{project_id}_report.xlsx", excel_bytes)
        return buf.getvalue()

    async def generate_supplier_report(self, request, chart_images: Optional[dict] = None) -> bytes:
        """Generate a report for a supplier."""
        if request.format == "pdf":
            return await self._generate_supplier_pdf(request, chart_images)
        elif request.format == "excel":
            return await self._generate_supplier_excel(request, chart_images)
        elif request.format == "zip":
            excel_bytes = await self._generate_supplier_excel(request, chart_images)
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
                zf.writestr(f"supplier_{request.supplier_id}_report.xlsx", excel_bytes)
            return buf.getvalue()
        raise ValueError(f"Unsupported format: {request.format}")

    # ── private helpers ──────────────────────────────────────────────────────

    async def _get_project_transactions(
        self,
        project_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> list[Transaction]:
        conditions = [Transaction.project_id == project_id, Transaction.from_fund == False]  # noqa: E712
        if start_date:
            conditions.append(Transaction.tx_date >= start_date)
        if end_date:
            conditions.append(Transaction.tx_date <= end_date)
        result = await self.db.execute(
            select(Transaction).where(and_(*conditions)).order_by(Transaction.tx_date)
        )
        return list(result.scalars().all())

    async def _build_excel_bytes(
        self,
        project_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        chart_images: Optional[dict] = None,
    ) -> bytes:
        try:
            import openpyxl
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Transactions"
            ws.append(["Date", "Type", "Amount", "Description", "Category"])

            txs = await self._get_project_transactions(project_id, start_date, end_date)
            for tx in txs:
                ws.append([
                    tx.tx_date.isoformat() if tx.tx_date else "",
                    str(tx.type) if tx.type else "",
                    float(tx.amount) if tx.amount else 0,
                    tx.description or "",
                    tx.category or "",
                ])

            buf = io.BytesIO()
            wb.save(buf)
            return buf.getvalue()
        except ImportError:
            # Fall back to simple CSV-in-bytes if openpyxl not installed
            lines = ["Date,Type,Amount,Description,Category"]
            txs = await self._get_project_transactions(project_id, start_date, end_date)
            for tx in txs:
                lines.append(f"{tx.tx_date},{tx.type},{tx.amount},{tx.description or ''},{tx.category or ''}")
            return "\n".join(lines).encode("utf-8")

    async def _generate_pdf_report(self, request, chart_images: Optional[dict] = None) -> bytes:
        """Minimal PDF generation - returns placeholder if reportlab not available."""
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas

            buf = io.BytesIO()
            c = canvas.Canvas(buf, pagesize=A4)
            c.drawString(100, 750, f"Project Report - Project ID: {request.project_id}")
            c.drawString(100, 730, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            c.save()
            return buf.getvalue()
        except ImportError:
            return b"%PDF-1.4 placeholder - reportlab not installed"

    async def _generate_excel_report_for_request(self, request, chart_images: Optional[dict] = None) -> bytes:
        return await self._build_excel_bytes(
            request.project_id,
            getattr(request, 'start_date', None),
            getattr(request, 'end_date', None),
            chart_images,
        )

    async def _generate_zip_report(self, request, chart_images: Optional[dict] = None) -> bytes:
        excel_bytes = await self._build_excel_bytes(
            request.project_id,
            getattr(request, 'start_date', None),
            getattr(request, 'end_date', None),
            chart_images,
        )
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(f"project_{request.project_id}_report.xlsx", excel_bytes)
        return buf.getvalue()

    async def _generate_supplier_pdf(self, request, chart_images: Optional[dict] = None) -> bytes:
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas

            buf = io.BytesIO()
            c = canvas.Canvas(buf, pagesize=A4)
            c.drawString(100, 750, f"Supplier Report - Supplier ID: {request.supplier_id}")
            c.save()
            return buf.getvalue()
        except ImportError:
            return b"%PDF-1.4 placeholder - reportlab not installed"

    async def _generate_supplier_excel(self, request, chart_images: Optional[dict] = None) -> bytes:
        try:
            import openpyxl
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Transactions"
            ws.append(["Date", "Type", "Amount", "Description", "Project"])

            conditions = [Transaction.supplier_id == request.supplier_id, Transaction.from_fund == False]  # noqa: E712
            if getattr(request, 'start_date', None):
                conditions.append(Transaction.tx_date >= request.start_date)
            if getattr(request, 'end_date', None):
                conditions.append(Transaction.tx_date <= request.end_date)

            result = await self.db.execute(
                select(Transaction).where(and_(*conditions)).order_by(Transaction.tx_date)
            )
            for tx in result.scalars().all():
                ws.append([
                    tx.tx_date.isoformat() if tx.tx_date else "",
                    str(tx.type) if tx.type else "",
                    float(tx.amount) if tx.amount else 0,
                    tx.description or "",
                    str(tx.project_id),
                ])

            buf = io.BytesIO()
            wb.save(buf)
            return buf.getvalue()
        except ImportError:
            return b"Date,Type,Amount,Description,Project"
