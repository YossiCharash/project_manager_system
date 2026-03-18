"""Shared mapper helpers that convert ORM objects to serialisable dicts."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.models.transaction import Transaction
    from backend.repositories.user_repository import UserRepository


def transaction_to_dict(tx: "Transaction") -> dict:
    """Convert a *Transaction* ORM object to a dict compatible with ``TransactionOut``.

    Accesses only attributes that are already loaded on the ORM object (no
    extra DB queries).  Relationship objects (``category``, ``created_by_user``)
    are resolved inline when available.
    """
    category_name: str | None = None
    category = getattr(tx, "category", None)
    if category is not None:
        category_name = getattr(category, "name", None)

    created_by_user_dict: dict | None = None
    created_by_user = getattr(tx, "created_by_user", None)
    if created_by_user is not None:
        created_by_user_dict = {
            "id": created_by_user.id,
            "full_name": getattr(created_by_user, "full_name", None),
            "email": getattr(created_by_user, "email", None),
        }

    return {
        "id": tx.id,
        "project_id": tx.project_id,
        "tx_date": tx.tx_date,
        "type": tx.type,
        "amount": float(tx.amount) if tx.amount is not None else 0.0,
        "description": tx.description,
        "category": category_name,
        "category_id": tx.category_id,
        "payment_method": tx.payment_method,
        "notes": tx.notes,
        "is_exceptional": tx.is_exceptional,
        "is_generated": tx.is_generated,
        "file_path": tx.file_path,
        "supplier_id": tx.supplier_id,
        "created_by_user_id": tx.created_by_user_id,
        "created_at": tx.created_at,
        "created_by_user": created_by_user_dict,
        "from_fund": tx.from_fund,
        "recurring_template_id": tx.recurring_template_id,
        "period_start_date": tx.period_start_date,
        "period_end_date": tx.period_end_date,
    }


async def transaction_to_dict_with_user(
    tx: "Transaction",
    user_repo: "UserRepository",
) -> dict:
    """Like :func:`transaction_to_dict` but loads the creator's user record when
    the relationship is not already populated.

    Falls back to ``transaction_to_dict`` if no ``created_by_user_id`` is set.
    """
    result = transaction_to_dict(tx)

    # If created_by_user is not yet populated but we have an ID, load it now.
    if result["created_by_user"] is None and tx.created_by_user_id is not None:
        user = await user_repo.get_by_id(tx.created_by_user_id)
        if user is not None:
            result["created_by_user"] = {
                "id": user.id,
                "full_name": getattr(user, "full_name", None),
                "email": getattr(user, "email", None),
            }

    return result
