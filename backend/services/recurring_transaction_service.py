"""
Recurring Transaction Service - manages recurring transaction templates and generation.
"""
from __future__ import annotations

import logging
from datetime import date, datetime, timezone
from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.models.recurring_transaction import RecurringTransactionTemplate
from backend.models.transaction import Transaction
from backend.repositories.recurring_transaction_repository import RecurringTransactionRepository
from backend.repositories.transaction_repository import TransactionRepository

logger = logging.getLogger(__name__)


class RecurringTransactionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = RecurringTransactionRepository(db)
        self.tx_repo = TransactionRepository(db)

    async def list_templates_by_project(self, project_id: int) -> list[RecurringTransactionTemplate]:
        return await self.repo.list_by_project(project_id)

    async def create_template(self, data, user_id: Optional[int] = None) -> RecurringTransactionTemplate:
        template = RecurringTransactionTemplate(
            project_id=data.project_id,
            type=data.type,
            amount=data.amount,
            description=data.description,
            category=getattr(data, 'category', None),
            category_id=getattr(data, 'category_id', None),
            supplier_id=getattr(data, 'supplier_id', None),
            day_of_month=data.day_of_month,
            start_date=data.start_date,
            end_date=getattr(data, 'end_date', None),
            is_active=True,
            payment_method=getattr(data, 'payment_method', None),
            notes=getattr(data, 'notes', None),
            created_by_user_id=user_id,
        )
        return await self.repo.create(template)

    async def get_template(self, template_id: int) -> Optional[RecurringTransactionTemplate]:
        return await self.repo.get_by_id(template_id)

    async def update_template(self, template_id: int, data) -> Optional[RecurringTransactionTemplate]:
        template = await self.repo.get_by_id(template_id)
        if not template:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(template, key, value)
        return await self.repo.update(template)

    async def delete_template(self, template_id: int) -> bool:
        template = await self.repo.get_by_id(template_id)
        if not template:
            return False
        await self.repo.delete(template)
        return True

    async def deactivate_template(self, template_id: int) -> Optional[RecurringTransactionTemplate]:
        template = await self.repo.get_by_id(template_id)
        if not template:
            return None
        template.is_active = False
        return await self.repo.update(template)

    async def get_template_transactions(self, template_id: int) -> list[Transaction]:
        result = await self.db.execute(
            select(Transaction).where(Transaction.recurring_template_id == template_id)
            .order_by(Transaction.tx_date)
        )
        return list(result.scalars().all())

    async def generate_transactions_for_date(self, target_date: date) -> list[Transaction]:
        """Generate recurring transactions for a specific date."""
        templates = await self.repo.list_active_templates()
        generated = []
        for template in templates:
            try:
                if not template.is_active:
                    continue
                if template.start_date > target_date:
                    continue
                if template.end_date and template.end_date < target_date:
                    continue
                if template.day_of_month != target_date.day:
                    continue

                # Check if already generated for this month
                from sqlalchemy import and_
                from datetime import date as date_type
                month_start = date_type(target_date.year, target_date.month, 1)
                if target_date.month == 12:
                    month_end = date_type(target_date.year + 1, 1, 1)
                else:
                    month_end = date_type(target_date.year, target_date.month + 1, 1)

                existing = await self.db.execute(
                    select(Transaction).where(
                        and_(
                            Transaction.recurring_template_id == template.id,
                            Transaction.tx_date >= month_start,
                            Transaction.tx_date < month_end,
                        )
                    )
                )
                if existing.scalar_one_or_none():
                    continue

                tx = Transaction(
                    project_id=template.project_id,
                    tx_date=target_date,
                    type=template.type,
                    amount=template.amount,
                    description=template.description,
                    category=template.category,
                    category_id=template.category_id,
                    payment_method=getattr(template, 'payment_method', None),
                    notes=getattr(template, 'notes', None),
                    supplier_id=template.supplier_id,
                    recurring_template_id=template.id,
                    is_generated=True,
                )
                self.db.add(tx)
                await self.db.flush()
                await self.db.refresh(tx)
                generated.append(tx)
            except Exception:
                logger.exception("Error generating transaction for template %s", template.id)

        if generated:
            await self.db.commit()

        return generated

    async def generate_transactions_for_month(self, year: int, month: int) -> list[Transaction]:
        """Generate all recurring transactions for a given month."""
        import calendar
        _, days_in_month = calendar.monthrange(year, month)
        generated = []
        for day in range(1, days_in_month + 1):
            try:
                day_date = date(year, month, day)
                day_txs = await self.generate_transactions_for_date(day_date)
                generated.extend(day_txs)
            except ValueError:
                pass
        return generated

    async def ensure_project_transactions_generated(self, project_id: int) -> int:
        """Ensure all recurring transactions are generated up to the current month."""
        templates = await self.repo.list_by_project(project_id, active_only=True)
        if not templates:
            return 0

        today = date.today()
        generated_count = 0

        for template in templates:
            try:
                if not template.is_active:
                    continue
                start = template.start_date
                end_date = template.end_date if template.end_date else today

                current = date(start.year, start.month, 1)
                target = date(today.year, today.month, 1)

                while current <= target:
                    try:
                        tx_date = date(current.year, current.month, template.day_of_month)
                    except ValueError:
                        # day doesn't exist in this month, skip
                        if current.month == 12:
                            current = date(current.year + 1, 1, 1)
                        else:
                            current = date(current.year, current.month + 1, 1)
                        continue

                    if tx_date < start or tx_date > today:
                        if current.month == 12:
                            current = date(current.year + 1, 1, 1)
                        else:
                            current = date(current.year, current.month + 1, 1)
                        continue
                    if end_date and tx_date > end_date:
                        break

                    from sqlalchemy import and_
                    from datetime import date as date_type
                    month_start = date_type(current.year, current.month, 1)
                    if current.month == 12:
                        month_end = date_type(current.year + 1, 1, 1)
                    else:
                        month_end = date_type(current.year, current.month + 1, 1)

                    existing_result = await self.db.execute(
                        select(Transaction).where(
                            and_(
                                Transaction.recurring_template_id == template.id,
                                Transaction.tx_date >= month_start,
                                Transaction.tx_date < month_end,
                            )
                        )
                    )
                    if not existing_result.scalar_one_or_none():
                        tx = Transaction(
                            project_id=template.project_id,
                            tx_date=tx_date,
                            type=template.type,
                            amount=template.amount,
                            description=template.description,
                            category=template.category,
                            category_id=template.category_id,
                            payment_method=getattr(template, 'payment_method', None),
                            notes=getattr(template, 'notes', None),
                            supplier_id=template.supplier_id,
                            recurring_template_id=template.id,
                            is_generated=True,
                        )
                        self.db.add(tx)
                        await self.db.flush()
                        generated_count += 1

                    if current.month == 12:
                        current = date(current.year + 1, 1, 1)
                    else:
                        current = date(current.year, current.month + 1, 1)

            except Exception:
                logger.exception("Error ensuring transactions for template %s", template.id)

        if generated_count > 0:
            await self.db.commit()

        return generated_count

    async def get_future_occurrences(
        self, template_id: int, start_date: date, months_ahead: int = 12
    ) -> list[dict]:
        """Get future occurrence dates for a template."""
        template = await self.repo.get_by_id(template_id)
        if not template:
            return []

        occurrences = []
        current = date(start_date.year, start_date.month, 1)
        from dateutil.relativedelta import relativedelta
        end = start_date + relativedelta(months=months_ahead)

        while current <= end:
            try:
                occ_date = date(current.year, current.month, template.day_of_month)
                if occ_date >= start_date:
                    if not template.end_date or occ_date <= template.end_date:
                        occurrences.append({
                            "date": occ_date.isoformat(),
                            "amount": float(template.amount),
                            "type": template.type,
                        })
            except ValueError:
                pass
            current = current + relativedelta(months=1)

        return occurrences

    async def update_transaction_instance(self, transaction_id: int, data) -> Optional[Transaction]:
        """Update a specific generated transaction instance."""
        tx = await self.tx_repo.get_by_id(transaction_id)
        if not tx:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if hasattr(tx, key):
                setattr(tx, key, value)
        await self.db.commit()
        await self.db.refresh(tx)
        return tx

    async def delete_transaction_instance(self, transaction_id: int) -> bool:
        """Delete a specific generated transaction instance."""
        tx = await self.tx_repo.get_by_id(transaction_id)
        if not tx or not getattr(tx, 'recurring_template_id', None):
            return False
        await self.db.delete(tx)
        await self.db.commit()
        return True
