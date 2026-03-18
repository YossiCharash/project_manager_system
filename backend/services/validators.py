"""Shared validation helpers used by TransactionService and transaction endpoints."""
from __future__ import annotations

from datetime import date
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession


async def get_first_contract_start(db: AsyncSession, project_id: int) -> Optional[date]:
    """Return the earliest contract period start date for *project_id*.

    Returns ``None`` if no contract periods exist yet (new project).
    """
    from backend.repositories.contract_period_repository import ContractPeriodRepository

    repo = ContractPeriodRepository(db)
    return await repo.get_earliest_start_date(project_id)


def validate_date_not_before_contract(
    tx_date: date,
    first_start: Optional[date],
    label: str = "עסקה",
) -> None:
    """Raise ``ValueError`` if *tx_date* is earlier than *first_start*.

    When *first_start* is ``None`` (no contract periods defined yet) the check
    is skipped – the project is brand-new and any date is acceptable.
    """
    if first_start is None:
        return
    if tx_date < first_start:
        formatted = first_start.strftime("%d/%m/%Y")
        raise ValueError(
            f"תאריך {label} ({tx_date.strftime('%d/%m/%Y')}) לפני תחילת החוזה הראשון ({formatted}). "
            "לא ניתן להוסיף עסקה לפני תחילת התקופה הראשונה."
        )


async def resolve_category(
    db: AsyncSession,
    *,
    category_id: Optional[int] = None,
    category_name: Optional[str] = None,
    allow_missing: bool = False,
):
    """Resolve a Category ORM instance from *category_id* or *category_name*.

    Args:
        db: Async database session.
        category_id: Primary key of the category (preferred).
        category_name: Fallback – look up by name when *category_id* is absent.
        allow_missing: When ``True``, return ``None`` instead of raising if the
            category cannot be found (used for fund / cash-register transactions).

    Returns:
        The ``Category`` ORM instance, or ``None`` when *allow_missing* is set.

    Raises:
        ValueError: When the category is not found and *allow_missing* is
            ``False``.
    """
    from backend.repositories.category_repository import CategoryRepository

    repo = CategoryRepository(db)

    if category_id is not None:
        category = await repo.get(category_id)
        if category is None:
            if allow_missing:
                return None
            raise ValueError(f"קטגוריה עם מזהה {category_id} לא נמצאה.")
        return category

    if category_name:
        category = await repo.get_by_name_global(category_name)
        if category is None:
            if allow_missing:
                return None
            raise ValueError(f"קטגוריה בשם '{category_name}' לא נמצאה.")
        return category

    if allow_missing:
        return None

    raise ValueError("קטגוריה היא שדה חובה. יש לבחור קטגוריה מהרשימה.")
