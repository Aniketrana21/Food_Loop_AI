"""
FoodLoop AI - Inventory & Double-Entry Stock Ledger API Router
Handles real-time inventory tracking, batch expiry alerts, and atomic stock transactions.
"""
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user, RoleChecker
from app.models.models import Inventory, InventoryTransaction
from app.schemas.enterprise_schemas import (
    InventoryCreate,
    InventoryUpdate,
    InventoryOut,
    StockAdjustRequest,
    InventoryTxOut
)
from app.repositories.inventory_repo import InventoryRepository
from app.utils.pagination import PaginationParams

router = APIRouter(prefix="/inventory", tags=["6. Inventory & Stock Ledger"])


@router.get("", response_model=dict)
def list_inventory(
    category: Optional[str] = Query(None, description="Filter by ingredient/product category"),
    kitchen_id: Optional[str] = Query(None, description="Filter by kitchen facility"),
    expiring_soon: Optional[bool] = Query(None, description="Filter items expiring in < 72 hours"),
    params: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Lists inventory lots with pagination, filtering, and sorting."""
    repo = InventoryRepository(db)
    query = db.query(Inventory).filter(Inventory.deleted_at.is_(None))

    if category:
        query = query.filter(Inventory.category == category)
    if kitchen_id:
        query = query.filter(Inventory.kitchen_id == kitchen_id)
    if expiring_soon:
        threshold = datetime.now(timezone.utc) + timedelta(hours=72)
        query = query.filter(Inventory.expiry_date <= threshold)

    if params.search:
        from app.models.models import Ingredient
        query = query.join(Ingredient, Inventory.ingredient_id == Ingredient.id).filter(
            (Ingredient.name.ilike(f"%{params.search}%")) |
            (Inventory.lot_number.ilike(f"%{params.search}%"))
        )

    from app.utils.pagination import paginate_query
    return paginate_query(query, params, model_class=Inventory)


@router.post("", response_model=InventoryOut, status_code=status.HTTP_201_CREATED)
def create_inventory_item(
    item_in: InventoryCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(RoleChecker(["ADMIN", "KITCHEN_MANAGER", "PROCESSOR"]))
):
    """Adds a new inventory batch to stock."""
    import uuid
    from app.models.models import Ingredient

    ing = db.query(Ingredient).filter(
        Ingredient.organization_id == item_in.organization_id,
        Ingredient.name == item_in.item_name
    ).first()
    if not ing:
        ing = Ingredient(
            organization_id=item_in.organization_id,
            name=item_in.item_name,
            category=item_in.category,
            unit=item_in.unit,
            standard_cost_per_unit=item_in.cost_per_unit_usd or 0.0
        )
        db.add(ing)
        db.flush()

    lot_no = item_in.batch_number or item_in.batch or f"LOT-{uuid.uuid4().hex[:6].upper()}"
    p_date = item_in.purchase_date or datetime.now(timezone.utc)
    unit_cost = item_in.cost_per_unit_usd or (item_in.cost if item_in.cost is not None else 0.0)
    
    inv = Inventory(
        kitchen_id=item_in.kitchen_id,
        ingredient_id=ing.id,
        lot_number=lot_no,
        current_quantity=item_in.quantity,
        unit=item_in.unit,
        storage_temp=item_in.storage_condition or item_in.storage_type or "REFRIGERATED",
        expiry_date=item_in.expiry_date,
        purchase_date=p_date,
        supplier=item_in.supplier or getattr(ing, "supplier_name", "Primary Distributor"),
        cost_per_unit=unit_cost,
        reorder_level=item_in.min_threshold_warning or 10.0,
        status=item_in.status or "OPTIMAL"
    )
    db.add(inv)
    db.flush()

    # Record initial receipt transaction as PURCHASE
    tx = InventoryTransaction(
        inventory_id=inv.id,
        transaction_type="PURCHASE",
        quantity=inv.current_quantity,
        unit=inv.unit,
        notes=f"Stock intake batch {lot_no} from {inv.supplier}"
    )
    db.add(tx)
    db.commit()
    db.refresh(inv)
    return inv


@router.post("/purchase", response_model=dict, status_code=status.HTTP_201_CREATED)
def record_purchase_order(
    purchase_in: dict,
    db: Session = Depends(get_db),
    user: dict = Depends(RoleChecker(["ADMIN", "KITCHEN_MANAGER"]))
):
    """
    Records an institutional purchase record / delivery order.
    Creates or increments inventory stock lots and writes immutable PURCHASE ledger entries.
    """
    import uuid
    from app.models.models import Ingredient
    
    org_id = purchase_in.get("organization_id")
    kitchen_id = purchase_in.get("kitchen_id")
    supplier = purchase_in.get("supplier_name", "Bulk Commercial Supplier")
    invoice_no = purchase_in.get("invoice_number", f"INV-{uuid.uuid4().hex[:6].upper()}")
    raw_items = purchase_in.get("items", [])
    
    total_cost = 0.0
    created_lots = []
    now = datetime.now(timezone.utc)
    
    for item_data in raw_items:
        item_name = item_data.get("item_name") or item_data.get("name")
        qty = float(item_data.get("quantity", 10.0))
        unit = item_data.get("unit", "kg")
        unit_cost = float(item_data.get("cost_per_unit", item_data.get("cost", 3.5)))
        storage = item_data.get("storage_type", item_data.get("storage_condition", "REFRIGERATED"))
        lot_no = item_data.get("batch", item_data.get("batch_number", f"LOT-{uuid.uuid4().hex[:6].upper()}"))
        expiry = item_data.get("expiry_date")
        if not expiry:
            expiry = now + timedelta(days=14)
        elif isinstance(expiry, str):
            expiry = datetime.fromisoformat(expiry.replace("Z", "+00:00"))
            
        total_cost += (qty * unit_cost)
        
        # Match or create ingredient
        ing = db.query(Ingredient).filter(
            Ingredient.organization_id == org_id,
            Ingredient.name == item_name
        ).first()
        if not ing:
            ing = Ingredient(
                organization_id=org_id,
                name=item_name,
                category=item_data.get("category", "PRODUCE"),
                unit=unit,
                standard_cost_per_unit=unit_cost
            )
            db.add(ing)
            db.flush()
            
        inv = Inventory(
            kitchen_id=kitchen_id,
            ingredient_id=ing.id,
            lot_number=lot_no,
            current_quantity=qty,
            unit=unit,
            storage_temp=storage,
            expiry_date=expiry,
            purchase_date=now,
            supplier=supplier,
            cost_per_unit=unit_cost,
            reorder_level=item_data.get("min_threshold_warning", 10.0),
            status="OPTIMAL"
        )
        db.add(inv)
        db.flush()
        
        tx = InventoryTransaction(
            inventory_id=inv.id,
            transaction_type="PURCHASE",
            quantity=qty,
            unit=unit,
            reference_id=invoice_no,
            notes=f"PO/Invoice {invoice_no} intake from {supplier}"
        )
        db.add(tx)
        created_lots.append(inv.id)
        
    db.commit()
    return {
        "invoice_number": invoice_no,
        "supplier_name": supplier,
        "items_received_count": len(created_lots),
        "total_cost_usd": round(total_cost, 2),
        "purchase_date": now,
        "created_inventory_lot_ids": created_lots
    }


@router.get("/purchases/history", response_model=List[dict])
def list_purchase_history(
    kitchen_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Lists aggregated purchase intake batches and transactions."""
    query = db.query(InventoryTransaction).filter(
        InventoryTransaction.transaction_type.in_(["PURCHASE", "INFLOW_PURCHASE"])
    ).order_by(InventoryTransaction.created_at.desc())
    
    txs = query.limit(50).all()
    history = []
    for tx in txs:
        inv = tx.inventory
        history.append({
            "transaction_id": tx.id,
            "inventory_id": tx.inventory_id,
            "item_name": inv.item_name if inv else "Unknown Item",
            "quantity": tx.quantity,
            "unit": tx.unit,
            "supplier": inv.supplier if inv else "Primary Supplier",
            "cost_per_unit": inv.cost if inv else 0.0,
            "total_cost": round(tx.quantity * (inv.cost if inv else 0.0), 2),
            "reference_id": tx.reference_id or "PO-DIRECT",
            "date": tx.created_at,
            "notes": tx.notes
        })
    return history


@router.get("/{inventory_id}", response_model=InventoryOut)
def get_inventory_item(
    inventory_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Retrieves specific inventory batch details."""
    repo = InventoryRepository(db)
    return repo.get_or_404(inventory_id, "Inventory")


@router.post("/{inventory_id}/adjust", response_model=InventoryTxOut)
def adjust_inventory_stock(
    inventory_id: str,
    adj_in: StockAdjustRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(RoleChecker(["ADMIN", "KITCHEN_MANAGER", "PROCESSOR"]))
):
    """
    Executes double-entry stock adjustment.
    Supports all 7 transaction types: PURCHASE, CONSUMPTION, PRODUCTION, ADJUSTMENT, WASTE, TRANSFER, DONATION.
    Deducts or adds quantity atomically and updates transaction ledger.
    """
    repo = InventoryRepository(db)
    inv = repo.get_or_404(inventory_id, "Inventory")

    # Multi-Tenant Isolation Check
    from app.core.security import normalize_role
    from fastapi import HTTPException
    user_role = normalize_role(user.get("role", ""))
    if user_role not in ["ADMIN", "AUDITOR"]:
        user_org_id = user.get("organization_id")
        inv_org_id = inv.organization_id
        if str(inv_org_id) != str(user_org_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access Denied: You cannot adjust inventory belonging to another organization."
            )

    return repo.adjust_stock(
        inventory_id=inventory_id,
        quantity_change=adj_in.quantity_change,
        transaction_type=adj_in.transaction_type,
        notes=adj_in.notes
    )


@router.get("/{inventory_id}/transactions", response_model=List[InventoryTxOut])
def get_inventory_transactions(
    inventory_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Retrieves complete audit trail of double-entry ledger transactions for an inventory item."""
    return db.query(InventoryTransaction).filter(
        InventoryTransaction.inventory_id == inventory_id
    ).order_by(InventoryTransaction.created_at.desc()).all()
