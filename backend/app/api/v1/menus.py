"""
FoodLoop AI - Menus & Recipes API Router
Manages menu cycles, standardized recipes, allergen profiles, and portion costs.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user, RoleChecker
from app.models.models import Menu, MenuItem
from app.schemas.enterprise_schemas import MenuCreate, MenuOut, MenuItemCreate, MenuItemOut
from app.repositories.base import BaseRepository
from app.utils.pagination import PaginationParams

router = APIRouter(prefix="/menus", tags=["5. Menus & Recipes"])


@router.get("", response_model=dict)
def list_menus(
    kitchen_id: Optional[str] = Query(None),
    params: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Lists menus with pagination."""
    repo = BaseRepository(Menu, db)
    filters = {"kitchen_id": kitchen_id} if kitchen_id else {}
    return repo.list(params, filters=filters, search_columns=["name", "season_or_cycle"])


@router.post("", response_model=MenuOut, status_code=status.HTTP_201_CREATED)
def create_menu(
    menu_in: MenuCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(RoleChecker(["ADMIN", "KITCHEN_MANAGER"]))
):
    """Creates a menu and nested menu items."""
    menu = Menu(
        organization_id=menu_in.organization_id,
        kitchen_id=menu_in.kitchen_id,
        name=menu_in.name,
        season_or_cycle=menu_in.season_or_cycle,
        is_active=menu_in.is_active
    )
    db.add(menu)
    db.flush()

    for item_data in menu_in.items:
        m_item = MenuItem(
            menu_id=menu.id,
            **item_data.model_dump()
        )
        db.add(m_item)

    db.commit()
    db.refresh(menu)
    return menu


@router.get("/{menu_id}", response_model=MenuOut)
def get_menu(
    menu_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Retrieves menu by ID with all item details."""
    repo = BaseRepository(Menu, db)
    return repo.get_or_404(menu_id, "Menu")


@router.post("/{menu_id}/items", response_model=MenuItemOut, status_code=status.HTTP_201_CREATED)
def add_menu_item(
    menu_id: str,
    item_in: MenuItemCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(RoleChecker(["ADMIN", "KITCHEN_MANAGER"]))
):
    """Adds a recipe item to an existing menu."""
    menu_repo = BaseRepository(Menu, db)
    menu_repo.get_or_404(menu_id, "Menu")

    item = MenuItem(menu_id=menu_id, **item_in.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/{menu_id}/items", response_model=List[MenuItemOut])
def list_menu_items(
    menu_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Lists all recipe items belonging to a menu."""
    menu_repo = BaseRepository(Menu, db)
    menu = menu_repo.get_or_404(menu_id, "Menu")
    return menu.items


@router.get("/ingredients/catalog", response_model=List[dict])
def list_ingredients_catalog(
    organization_id: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Lists available raw ingredients with standard portion costs and supplier tags."""
    from app.models.models import Ingredient
    query = db.query(Ingredient).filter(Ingredient.deleted_at.is_(None))
    if organization_id:
        query = query.filter(Ingredient.organization_id == organization_id)
    if category:
        query = query.filter(Ingredient.category == category)
        
    ingredients = query.all()
    return [
        {
            "id": ing.id,
            "organization_id": ing.organization_id,
            "name": ing.name,
            "category": ing.category,
            "unit": ing.unit,
            "reorder_point": ing.reorder_point,
            "standard_cost_per_unit": ing.standard_cost_per_unit,
            "supplier_name": getattr(ing, "supplier_name", "Primary Fresh Distributor"),
            "storage_temp_category": ing.storage_temp_category,
            "allergen_profile": ing.allergen_profile or []
        }
        for ing in ingredients
    ]


@router.post("/ingredients/catalog", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_ingredient(
    ingredient_data: dict,
    db: Session = Depends(get_db),
    user: dict = Depends(RoleChecker(["ADMIN", "KITCHEN_MANAGER"]))
):
    """Registers a new raw ingredient in the institutional culinary catalog."""
    from app.models.models import Ingredient
    ing = Ingredient(
        organization_id=ingredient_data["organization_id"],
        name=ingredient_data["name"],
        category=ingredient_data.get("category", "PRODUCE"),
        unit=ingredient_data.get("unit", "kg"),
        reorder_point=ingredient_data.get("reorder_point", 10.0),
        standard_cost_per_unit=ingredient_data.get("standard_cost_per_unit", 0.0),
        storage_temp_category=ingredient_data.get("storage_temp_category", "ROOM_TEMP"),
        allergen_profile=ingredient_data.get("allergen_profile", [])
    )
    db.add(ing)
    db.commit()
    db.refresh(ing)
    return {
        "id": ing.id,
        "organization_id": ing.organization_id,
        "name": ing.name,
        "category": ing.category,
        "unit": ing.unit,
        "reorder_point": ing.reorder_point,
        "standard_cost_per_unit": ing.standard_cost_per_unit,
        "storage_temp_category": ing.storage_temp_category
    }
