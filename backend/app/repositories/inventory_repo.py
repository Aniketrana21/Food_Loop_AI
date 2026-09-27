"""
FoodLoop AI - Inventory Repository
Provides double-entry inventory transactions, atomic balance updates, and stock threshold queries.
"""
from typing import Optional
from sqlalchemy.orm import Session
from app.repositories.base import BaseRepository
from app.models.models import Inventory, InventoryTransaction
from app.utils.exceptions import InventoryInsufficientError, NotFoundError


class InventoryRepository(BaseRepository[Inventory]):
    def __init__(self, db: Session):
        super().__init__(Inventory, db)

    def adjust_stock(
        self,
        inventory_id: str,
        quantity_change: float,
        transaction_type: str = "MANUAL_ADJUSTMENT",
        notes: Optional[str] = None
    ) -> InventoryTransaction:
        """
        Executes atomic double-entry inventory adjustment.
        Rolls back if stock would fall below zero on reduction.
        """
        inv = self.get_or_404(inventory_id, "Inventory")

        new_balance = inv.quantity + quantity_change
        if new_balance < 0:
            raise InventoryInsufficientError(
                f"Cannot reduce stock of '{inv.item_name}' by {abs(quantity_change)} {inv.unit}. "
                f"Available balance is {inv.quantity} {inv.unit}."
            )

        inv.quantity = new_balance

        tx = InventoryTransaction(
            inventory_id=inv.id,
            transaction_type=transaction_type,
            quantity=quantity_change,
            unit=inv.unit,
            notes=notes
        )
        self.db.add(tx)
        self.db.commit()
        self.db.refresh(tx)
        self.db.refresh(inv)
        return tx
