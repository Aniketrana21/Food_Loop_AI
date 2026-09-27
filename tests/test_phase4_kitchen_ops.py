"""
FoodLoop AI - Phase 4 Kitchen, Inventory & Waste Test Suite
Validates the complete operational workflow for institutional kitchens:
1. Kitchen Profile & Staff Management
2. Menus & Ingredients Catalog
3. Inventory CRUD with full field contract (quantity, unit, batch, dates, storage, supplier, cost, status)
4. Purchase Records (PO batch intake & ledger entries)
5. All 7 Inventory Transaction Types (PURCHASE, CONSUMPTION, PRODUCTION, ADJUSTMENT, WASTE, TRANSFER, DONATION)
6. Production Batches & Meal Prep Completion
7. Meal Consumption & Leftover Routing (Surplus vs Waste)
8. Waste Records with all 8 Categories (OVERPRODUCTION, PLATE_WASTE, SPOILAGE, EXPIRED, PREPARATION_WASTE, DAMAGED, QUALITY_REJECTION, OTHER)
9. Multi-dimensional Waste Analytics (Daily, Weekly, Monthly, By Category, By Food Item, Cost, Trend)
"""
import pytest
from datetime import datetime, timezone, timedelta
from app.core.security import create_access_token
from app.models.models import Organization, Kitchen, Ingredient, Inventory, ProductionBatch, ConsumptionRecord, WasteRecord


@pytest.fixture
def auth_headers():
    token = create_access_token({
        "sub": "22222222-2222-2222-2222-222222222222",
        "email": "chef@grandhyatt.com",
        "role": "KITCHEN_MANAGER",
        "organization_id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
    })
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_kitchen_env(db):
    org = Organization(
        name="Apex Culinary Hospitality Center",
        org_type="CENTRAL_KITCHEN",
        registration_number=f"REG-CULINARY-{datetime.now().timestamp()}",
        address="100 Culinary Way, SF",
        latitude=37.7749,
        longitude=-122.4194,
        contact_phone="+1-555-9000",
        contact_email="culinary@apex.internal"
    )
    db.add(org)
    db.flush()

    kitchen = Kitchen(
        organization_id=org.id,
        name="Production Bay Alpha",
        facility_type="COMMERCIAL_KITCHEN",
        daily_meal_capacity=1200,
        address="100 Culinary Way, Bay Alpha",
        latitude=37.7749,
        longitude=-122.4194,
        contact_name="Chef Antoine Laurent",
        contact_phone="+1-555-9001",
        storage_specs={
            "cold_storage": True,
            "hot_holding": True,
            "cold_room_c": 3.0,
            "freezer_c": -18.0
        }
    )
    db.add(kitchen)
    db.commit()
    db.refresh(org)
    db.refresh(kitchen)
    return {"org": org, "kitchen": kitchen}


def test_kitchen_profile_and_staff(client, auth_headers, test_kitchen_env):
    k_id = test_kitchen_env["kitchen"].id
    
    # 1. Fetch kitchen profile
    res = client.get(f"/api/v1/kitchens/{k_id}/profile", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "Production Bay Alpha"
    assert data["daily_meal_capacity"] == 1200
    assert data["metrics"]["cold_room_target_temp_c"] == 3.5

    # 2. Add staff member
    staff_payload = {
        "full_name": "Elena Rostova",
        "email": f"elena_{datetime.now().timestamp()}@culinary.internal",
        "phone": "+1-555-8822",
        "role": "KITCHEN_MANAGER"
    }
    staff_res = client.post(f"/api/v1/kitchens/{k_id}/staff", json=staff_payload, headers=auth_headers)
    assert staff_res.status_code == 201
    assert staff_res.json()["full_name"] == "Elena Rostova"

    # 3. List staff members
    list_res = client.get(f"/api/v1/kitchens/{k_id}/staff", headers=auth_headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1


def test_menus_and_ingredients_catalog(client, auth_headers, test_kitchen_env):
    org_id = test_kitchen_env["org"].id
    k_id = test_kitchen_env["kitchen"].id

    # 1. Create Raw Ingredient in Catalog
    ing_payload = {
        "organization_id": org_id,
        "name": "Organic Roma Tomatoes",
        "category": "PRODUCE",
        "unit": "kg",
        "reorder_point": 25.0,
        "standard_cost_per_unit": 2.40,
        "storage_temp_category": "REFRIGERATED"
    }
    ing_res = client.post("/api/v1/menus/ingredients/catalog", json=ing_payload, headers=auth_headers)
    assert ing_res.status_code == 201
    assert ing_res.json()["name"] == "Organic Roma Tomatoes"

    # 2. List Ingredients Catalog
    cat_res = client.get(f"/api/v1/menus/ingredients/catalog?organization_id={org_id}", headers=auth_headers)
    assert cat_res.status_code == 200
    assert len(cat_res.json()) >= 1

    # 3. Create Menu with nested Recipe Items
    menu_payload = {
        "organization_id": org_id,
        "kitchen_id": k_id,
        "name": "Autumn Banquet Cycle",
        "season_or_cycle": "AUTUMN_2026",
        "is_active": True,
        "items": [
            {
                "name": "Heirloom Tomato Basil Bisque",
                "category": "SOUP",
                "serving_size_grams": 350.0,
                "cost_per_portion_usd": 1.75,
                "dietary_flags": ["VEGETARIAN", "GLUTEN_FREE"],
                "allergens": ["DAIRY"]
            }
        ]
    }
    menu_res = client.post("/api/v1/menus", json=menu_payload, headers=auth_headers)
    assert menu_res.status_code == 201
    menu_data = menu_res.json()
    assert menu_data["name"] == "Autumn Banquet Cycle"
    assert len(menu_data["items"]) == 1


def test_inventory_full_field_contract_and_purchases(client, auth_headers, test_kitchen_env):
    org_id = test_kitchen_env["org"].id
    k_id = test_kitchen_env["kitchen"].id
    now = datetime.now(timezone.utc)

    # 1. Direct Inventory Intake with Full Fields (quantity, unit, batch, dates, storage, supplier, cost, status)
    inv_payload = {
        "organization_id": org_id,
        "kitchen_id": k_id,
        "item_name": "Grass-Fed Beef Chuck Roast",
        "category": "MEAT",
        "quantity": 80.0,
        "unit": "kg",
        "batch": "LOT-BF-9921",
        "storage_type": "REFRIGERATED_4C",
        "purchase_date": now.isoformat(),
        "expiry_date": (now + timedelta(days=10)).isoformat(),
        "supplier": "Valley Pastures Meat Co.",
        "cost": 8.50,
        "status": "OPTIMAL"
    }
    create_res = client.post("/api/v1/inventory", json=inv_payload, headers=auth_headers)
    assert create_res.status_code == 201
    inv_data = create_res.json()
    inv_id = inv_data["id"]
    assert inv_data["quantity"] == 80.0
    assert inv_data["unit"] == "kg"
    assert inv_data["batch_number"] == "LOT-BF-9921"
    assert inv_data["supplier"] == "Valley Pastures Meat Co."

    # 2. Bulk Purchase Inflow Order
    po_payload = {
        "organization_id": org_id,
        "kitchen_id": k_id,
        "supplier_name": "Pacific Dairy Wholesale",
        "invoice_number": f"PO-DAIRY-{datetime.now().timestamp()}",
        "items": [
            {
                "organization_id": org_id,
                "kitchen_id": k_id,
                "item_name": "Whole Milk Organic 3.8%",
                "category": "DAIRY",
                "quantity": 100.0,
                "unit": "liters",
                "batch": "LOT-MK-1024",
                "storage_type": "REFRIGERATED_4C",
                "expiry_date": (now + timedelta(days=12)).isoformat(),
                "cost": 1.80,
                "supplier": "Pacific Dairy Wholesale"
            },
            {
                "organization_id": org_id,
                "kitchen_id": k_id,
                "item_name": "Aged Cheddar Wheels",
                "category": "DAIRY",
                "quantity": 30.0,
                "unit": "kg",
                "batch": "LOT-CH-5510",
                "storage_type": "REFRIGERATED_4C",
                "expiry_date": (now + timedelta(days=60)).isoformat(),
                "cost": 9.20,
                "supplier": "Pacific Dairy Wholesale"
            }
        ]
    }
    po_res = client.post("/api/v1/inventory/purchase", json=po_payload, headers=auth_headers)
    assert po_res.status_code == 201
    assert po_res.json()["items_received_count"] == 2
    assert po_res.json()["total_cost_usd"] == 456.0

    # 3. Check Purchase History
    hist_res = client.get("/api/v1/inventory/purchases/history", headers=auth_headers)
    assert hist_res.status_code == 200
    assert len(hist_res.json()) >= 2


def test_all_seven_inventory_transaction_types(client, auth_headers, test_kitchen_env):
    org_id = test_kitchen_env["org"].id
    k_id = test_kitchen_env["kitchen"].id
    now = datetime.now(timezone.utc)

    # Base item
    inv_payload = {
        "organization_id": org_id,
        "kitchen_id": k_id,
        "item_name": "Gold Medal All-Purpose Flour",
        "category": "DRY_GOODS",
        "quantity": 200.0,
        "unit": "kg",
        "batch": "LOT-FLOUR-100",
        "storage_type": "ROOM_TEMP",
        "expiry_date": (now + timedelta(days=180)).isoformat(),
        "cost": 1.20,
        "supplier": "General Milling Supplies"
    }
    create_res = client.post("/api/v1/inventory", json=inv_payload, headers=auth_headers)
    inv_id = create_res.json()["id"]

    # 1. PURCHASE (Add 50kg)
    tx1 = client.post(f"/api/v1/inventory/{inv_id}/adjust", json={"quantity_change": 50.0, "transaction_type": "PURCHASE"}, headers=auth_headers)
    assert tx1.status_code == 200
    assert tx1.json()["resulting_balance"] == 250.0

    # 2. CONSUMPTION (Deduct 20kg for dining)
    tx2 = client.post(f"/api/v1/inventory/{inv_id}/adjust", json={"quantity_change": -20.0, "transaction_type": "CONSUMPTION"}, headers=auth_headers)
    assert tx2.status_code == 200
    assert tx2.json()["resulting_balance"] == 230.0

    # 3. PRODUCTION (Deduct 30kg for baking batch)
    tx3 = client.post(f"/api/v1/inventory/{inv_id}/adjust", json={"quantity_change": -30.0, "transaction_type": "PRODUCTION"}, headers=auth_headers)
    assert tx3.status_code == 200
    assert tx3.json()["resulting_balance"] == 200.0

    # 4. ADJUSTMENT (Manual cycle count adjustment +5kg)
    tx4 = client.post(f"/api/v1/inventory/{inv_id}/adjust", json={"quantity_change": 5.0, "transaction_type": "ADJUSTMENT"}, headers=auth_headers)
    assert tx4.status_code == 200
    assert tx4.json()["resulting_balance"] == 205.0

    # 5. WASTE (Deduct 5kg bag damaged by moisture)
    tx5 = client.post(f"/api/v1/inventory/{inv_id}/adjust", json={"quantity_change": -5.0, "transaction_type": "WASTE", "notes": "Moisture damaged bag"}, headers=auth_headers)
    assert tx5.status_code == 200
    assert tx5.json()["resulting_balance"] == 200.0

    # 6. TRANSFER (Relocate 40kg to satellite bakery)
    tx6 = client.post(f"/api/v1/inventory/{inv_id}/adjust", json={"quantity_change": -40.0, "transaction_type": "TRANSFER", "notes": "Transfer to Bay 2"}, headers=auth_headers)
    assert tx6.status_code == 200
    assert tx6.json()["resulting_balance"] == 160.0

    # 7. DONATION (Deduct 10kg allocated to community pantry)
    tx7 = client.post(f"/api/v1/inventory/{inv_id}/adjust", json={"quantity_change": -10.0, "transaction_type": "DONATION", "notes": "Donation transfer"}, headers=auth_headers)
    assert tx7.status_code == 200
    assert tx7.json()["resulting_balance"] == 150.0

    # Verify transaction ledger history
    ledger_res = client.get(f"/api/v1/inventory/{inv_id}/transactions", headers=auth_headers)
    assert ledger_res.status_code == 200
    assert len(ledger_res.json()) >= 7


def test_production_batches_and_leftover_routing(client, auth_headers, test_kitchen_env):
    org_id = test_kitchen_env["org"].id
    k_id = test_kitchen_env["kitchen"].id
    now = datetime.now(timezone.utc)

    # 1. Schedule Production Batch
    batch_payload = {
        "organization_id": org_id,
        "kitchen_id": k_id,
        "batch_number": f"BATCH-{datetime.now().timestamp()}",
        "planned_portions": 200,
        "actual_portions_prepped": 210,
        "total_batch_weight_kg": 75.0,
        "production_date": now.isoformat(),
        "holding_temperature_c": 68.0
    }
    b_res = client.post("/api/v1/production", json=batch_payload, headers=auth_headers)
    assert b_res.status_code == 201
    batch_id = b_res.json()["id"]

    # 2. Complete Batch with HACCP Holding Temp
    comp_res = client.post(f"/api/v1/production/{batch_id}/complete", json={"actual_portions_prepped": 205, "holding_temperature_c": 66.5}, headers=auth_headers)
    assert comp_res.status_code == 200
    assert comp_res.json()["status"] == "COMPLETED"

    # 3. Log Consumption Record
    cons_payload = {
        "organization_id": org_id,
        "kitchen_id": k_id,
        "production_batch_id": batch_id,
        "meal_service": "LUNCH",
        "headcount_served": 160,
        "portions_consumed": 165,
        "portions_remaining_surplus": 40,
        "surplus_weight_kg": 14.5,
        "notes": "40 portions remaining after main lunch service"
    }
    c_res = client.post("/api/v1/consumption", json=cons_payload, headers=auth_headers)
    assert c_res.status_code == 201
    cons_id = c_res.json()["id"]

    # 4. Route Leftover -> DIVERT_TO_SURPLUS
    route_surplus_payload = {
        "action": "DIVERT_TO_SURPLUS",
        "quantity_kg": 14.5,
        "portions": 40,
        "storage_temp_condition": "HOT_HOLDING_60C",
        "notes": "High quality hot banquet surplus"
    }
    surplus_route_res = client.post(f"/api/v1/consumption/{cons_id}/route-leftover", json=route_surplus_payload, headers=auth_headers)
    assert surplus_route_res.status_code == 201
    assert surplus_route_res.json()["action"] == "DIVERT_TO_SURPLUS"
    assert "surplus_id" in surplus_route_res.json()

    # 5. Route Leftover -> LOG_AS_WASTE
    route_waste_payload = {
        "action": "LOG_AS_WASTE",
        "quantity_kg": 4.2,
        "portions": 10,
        "category": "OVERPRODUCTION",
        "notes": "Cold buffet scraps past safe serving window"
    }
    waste_route_res = client.post(f"/api/v1/consumption/{cons_id}/route-leftover", json=route_waste_payload, headers=auth_headers)
    assert waste_route_res.status_code == 201
    assert waste_route_res.json()["action"] == "LOG_AS_WASTE"
    assert "waste_id" in waste_route_res.json()


def test_waste_record_all_categories_and_analytics(client, auth_headers, test_kitchen_env):
    org_id = test_kitchen_env["org"].id
    k_id = test_kitchen_env["kitchen"].id
    now = datetime.now(timezone.utc)

    # Test all 8 categories
    categories = [
        "OVERPRODUCTION",
        "PLATE_WASTE",
        "SPOILAGE",
        "EXPIRED",
        "PREPARATION_WASTE",
        "DAMAGED",
        "QUALITY_REJECTION",
        "OTHER"
    ]

    for cat in categories:
        waste_payload = {
            "organization_id": org_id,
            "kitchen_id": k_id,
            "food_item": f"Tested {cat.replace('_', ' ').title()} Item",
            "quantity": 5.5,
            "unit": "kg",
            "reason": f"Operational check for {cat}",
            "category": cat,
            "date": now.isoformat(),
            "waste_cost": 22.0,
            "notes": f"Batch test {cat}",
            "image_url": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c"
        }
        res = client.post("/api/v1/waste", json=waste_payload, headers=auth_headers)
        assert res.status_code == 201
        data = res.json()
        assert data["category"] == cat
        assert data["quantity_kg"] == 5.5
        assert data["waste_cost"] == 22.0

    # Test Analytics Endpoint
    analytics_res = client.get(f"/api/v1/waste/analytics?organization_id={org_id}&kitchen_id={k_id}", headers=auth_headers)
    assert analytics_res.status_code == 200
    analytics = analytics_res.json()
    assert "daily_waste" in analytics
    assert "weekly_waste" in analytics
    assert "monthly_waste" in analytics
    assert "waste_by_category" in analytics
    assert "waste_by_food_item" in analytics
    assert "waste_cost" in analytics
    assert "waste_trend" in analytics
    assert len(analytics["waste_by_category"]) == 8
