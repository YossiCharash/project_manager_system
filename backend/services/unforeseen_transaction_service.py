"""
Unforeseen Transaction Service - manages unforeseen/exceptional transactions.
"""
from __future__ import annotations

import logging
from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.models.unforeseen_transaction import UnforeseenTransaction, UnforeseenTransactionLine, UnforeseenTransactionStatus
from backend.repositories.document_repository import DocumentRepository

logger = logging.getLogger(__name__)


class UnforeseenTransactionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, tx_id: int) -> Optional[UnforeseenTransaction]:
        result = await self.db.execute(
            select(UnforeseenTransaction).where(UnforeseenTransaction.id == tx_id)
        )
        return result.scalar_one_or_none()

    async def get_expense_by_id(self, line_id: int) -> Optional[UnforeseenTransactionLine]:
        result = await self.db.execute(
            select(UnforeseenTransactionLine).where(
                UnforeseenTransactionLine.id == line_id,
                UnforeseenTransactionLine.line_type == "expense"
            )
        )
        return result.scalar_one_or_none()

    async def get_income_by_id(self, line_id: int) -> Optional[UnforeseenTransactionLine]:
        result = await self.db.execute(
            select(UnforeseenTransactionLine).where(
                UnforeseenTransactionLine.id == line_id,
                UnforeseenTransactionLine.line_type == "income"
            )
        )
        return result.scalar_one_or_none()

    async def list_by_project(
        self, project_id: int, contract_period_id: Optional[int] = None, include_executed: bool = True
    ) -> list[UnforeseenTransaction]:
        stmt = select(UnforeseenTransaction).where(UnforeseenTransaction.project_id == project_id)
        if contract_period_id is not None:
            stmt = stmt.where(UnforeseenTransaction.contract_period_id == contract_period_id)
        if not include_executed:
            stmt = stmt.where(UnforeseenTransaction.status != UnforeseenTransactionStatus.EXECUTED)
        result = await self.db.execute(stmt.order_by(UnforeseenTransaction.transaction_date.desc()))
        return list(result.scalars().all())

    async def list_by_contract_period(self, contract_period_id: int) -> list[UnforeseenTransaction]:
        result = await self.db.execute(
            select(UnforeseenTransaction)
            .where(UnforeseenTransaction.contract_period_id == contract_period_id)
            .order_by(UnforeseenTransaction.transaction_date.desc())
        )
        return list(result.scalars().all())

    async def get_by_resulting_transaction_id(self, tx_id: int) -> Optional[UnforeseenTransaction]:
        result = await self.db.execute(
            select(UnforeseenTransaction).where(UnforeseenTransaction.resulting_transaction_id == tx_id)
        )
        return result.scalar_one_or_none()


class UnforeseenTransactionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = UnforeseenTransactionRepository(db)

    async def create(self, data, user_id: Optional[int] = None) -> UnforeseenTransaction:
        tx = UnforeseenTransaction(
            project_id=data.project_id,
            contract_period_id=getattr(data, 'contract_period_id', None),
            description=getattr(data, 'description', None),
            notes=getattr(data, 'notes', None),
            transaction_date=getattr(data, 'transaction_date', None) or date.today(),
            status=UnforeseenTransactionStatus.DRAFT,
            created_by_user_id=user_id,
        )
        self.db.add(tx)
        await self.db.flush()
        await self.db.refresh(tx)

        lines = getattr(data, 'lines', None) or []
        for line_data in lines:
            line = UnforeseenTransactionLine(
                unforeseen_transaction_id=tx.id,
                line_type=line_data.line_type,
                amount=line_data.amount,
                description=getattr(line_data, 'description', None),
            )
            self.db.add(line)

        await self.db.commit()
        await self.db.refresh(tx)
        return tx

    async def get_by_id(self, tx_id: int) -> Optional[UnforeseenTransaction]:
        return await self.repo.get_by_id(tx_id)

    async def get_by_resulting_transaction_id(self, tx_id: int) -> Optional[UnforeseenTransaction]:
        return await self.repo.get_by_resulting_transaction_id(tx_id)

    async def list_by_project(
        self, project_id: int, contract_period_id: Optional[int] = None, include_executed: bool = True
    ) -> list[dict]:
        txs = await self.repo.list_by_project(project_id, contract_period_id, include_executed)
        return [await self._format_transaction(tx) for tx in txs]

    async def list_by_contract_period(self, contract_period_id: int) -> list[dict]:
        txs = await self.repo.list_by_contract_period(contract_period_id)
        return [await self._format_transaction(tx) for tx in txs]

    async def update(self, tx_id: int, data, user_id: Optional[int] = None) -> Optional[UnforeseenTransaction]:
        tx = await self.repo.get_by_id(tx_id)
        if not tx:
            return None
        if tx.status == UnforeseenTransactionStatus.EXECUTED:
            raise ValueError("Cannot update an executed transaction")

        update_data = data.model_dump(exclude_unset=True)
        lines_data = update_data.pop('lines', None)

        for key, value in update_data.items():
            if hasattr(tx, key):
                setattr(tx, key, value)

        if lines_data is not None:
            # Remove old lines
            for line in list(tx.lines):
                await self.db.delete(line)
            await self.db.flush()
            # Add new lines
            for line_data in lines_data:
                line = UnforeseenTransactionLine(
                    unforeseen_transaction_id=tx.id,
                    line_type=line_data['line_type'],
                    amount=line_data['amount'],
                    description=line_data.get('description'),
                )
                self.db.add(line)

        await self.db.commit()
        await self.db.refresh(tx)
        return tx

    async def delete(self, tx_id: int) -> bool:
        tx = await self.repo.get_by_id(tx_id)
        if not tx:
            return False
        if tx.status == UnforeseenTransactionStatus.EXECUTED:
            raise ValueError("Cannot delete an executed transaction")
        await self.db.delete(tx)
        await self.db.commit()
        return True

    async def execute(self, tx_id: int, user_id: Optional[int] = None):
        """Execute an unforeseen transaction and optionally create a resulting transaction."""
        tx = await self.repo.get_by_id(tx_id)
        if not tx:
            return None
        if tx.status == UnforeseenTransactionStatus.EXECUTED:
            raise ValueError("Transaction is already executed")

        from backend.models.transaction import Transaction
        total_expense = sum(float(l.amount) for l in tx.lines if l.line_type == "expense")
        total_income = sum(float(l.amount) for l in tx.lines if l.line_type == "income")
        net = total_income - total_expense

        result_tx = None
        if net != 0:
            tx_type = "Income" if net > 0 else "Expense"
            result_tx = Transaction(
                project_id=tx.project_id,
                tx_date=tx.transaction_date,
                type=tx_type,
                amount=abs(net),
                description=tx.description or "Unforeseen transaction",
                is_exceptional=True,
                created_by_user_id=user_id,
            )
            self.db.add(result_tx)
            await self.db.flush()
            await self.db.refresh(result_tx)
            tx.resulting_transaction_id = result_tx.id

        tx.status = UnforeseenTransactionStatus.EXECUTED
        await self.db.commit()
        await self.db.refresh(tx)
        return result_tx

    async def _format_transaction(self, tx: UnforeseenTransaction) -> dict:
        """Format an UnforeseenTransaction for API response."""
        doc_repo = DocumentRepository(self.db)
        lines_out = []
        for line in tx.lines:
            docs = []
            try:
                line_docs = await doc_repo.list_by_entity("unforeseen_expense" if line.line_type == "expense" else "unforeseen_income", line.id)
                docs = [{"id": d.id, "file_path": d.file_path, "description": d.description} for d in line_docs]
            except Exception:
                pass
            lines_out.append({
                "id": line.id,
                "line_type": line.line_type,
                "amount": float(line.amount),
                "description": line.description,
                "documents": docs,
            })
        return {
            "id": tx.id,
            "project_id": tx.project_id,
            "contract_period_id": tx.contract_period_id,
            "status": tx.status.value if hasattr(tx.status, 'value') else str(tx.status),
            "description": tx.description,
            "notes": tx.notes,
            "transaction_date": tx.transaction_date.isoformat() if tx.transaction_date else None,
            "lines": lines_out,
            "resulting_transaction_id": tx.resulting_transaction_id,
            "created_at": tx.created_at.isoformat() if tx.created_at else None,
            "updated_at": tx.updated_at.isoformat() if tx.updated_at else None,
        }
