"""
FoodLoop AI - Phase 14 Food Processing Unit (FPU) & FEFO Test Suite
Validates the complete operational workflow for food processing and upcycling units:
1. Processing Unit Registration & Facility Specs
2. Raw Material Inventory CRUD with Full Expiry & Packaging Condition Contracts
3. FEFO (First Expire, First Out) Multi-Lot Allocation Algorithm & Pick Sequencing
4. FEFO Real-time Consumption Queue
5. Industrial Production Batch Creation with Automatic Material Deduction & Yield
6. Quality Control, Damaged Packaging Tracking & Rejected Products Valorization
7. Configurable Alert Threshold Rules (Product & Category Overrides)
8. Automated Expiry Alerts (7-day, 3-day, 1-day, Expired, Damaged Packaging)
9. Surplus Declaration & Charitable Redistribution with Recipient Allocation
10. End-to-End 5-Hop Batch Traceability (Raw Material -> Batch -> Finished Product -> Surplus -> Recipient)
11. Executive Dashboard Multi-Pillar KPI Metrics
"""
import pytest
from datetime import datetime, timezone, timedelta
from app.core.security import create_access_token
from app.models.models import Organization, ProcessingUnit, Recipient, FpuRawMaterial, FpuProductionBatch


@pytest.fixture
def auth_headers():
    token = create_access_token({
        "sub": "33333333-3333-3333-3333-333333333333",
        "email": "processor@foodloop.org",
        "role": "PROCESSOR",
        "organization_id": "cccccccc-cccc-cccc-cccc-cccccccccccc"
    })
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_fpu_env(db):
    """Initializes an industrial food processing facility environment."""
    org = Organization(
        name="Silicon Valley Valorization & Canning Plant",
        org_type="PROCESSING_UNIT",
        registration_number=f"REG-FPU-{datetime.now().timestamp()}",
        address="500 Industrial Parkway, San Jose, CA",
        latitude=37.3382,
        longitude=-121.8863,
        contact_phone="+1-555-4000",
        contact_email="plant@valorization.org"
    )
    db.add(org)
    db.flush()

    unit = ProcessingUnit(
        organization_id=org.id,
        name="Bay Area Upcycling & Canning Hub #04",
        address="500 Industrial Parkway, Plant 4",
        latitude=37.3382,
        longitude=-121.8863,
        processing_type="CANNING_AND_DEHYDRATION",
        daily_capacity_kg=5000.0,
        cold_tank_capacity_liters=10000.0,
        is_active=True
    )
    db.add(unit)

    recipient = Recipient(
        organization_id=org.id,
        name="Second Harvest Regional Food Bank",
        facility_type="FOOD_BANK",
        address="750 Curtner Ave, San Jose, CA",
        latitude=37.2882,
        longitude=-121.8763,
        contact_person="Sarah Jenkins",
        contact_phone="+1-555-8888",
        max_daily_intake_kg=1500.0,
        is_active=True
    )
    db.add(recipient)
    db.commit()

    return {
        "org_id": org.id,
        "unit_id": unit.id,
        "recipient_id": recipient.id
    }


# =====================================================================
# TEST 1: PROCESSING UNIT REGISTRATION & RETRIEVAL
# =====================================================================

def test_processing_unit_crud(client, auth_headers, test_fpu_env):
    unit_id = test_fpu_env["unit_id"]

    # 1. Retrieve processing unit
    resp = client.get(f"/api/v1/processing/{unit_id}", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Bay Area Upcycling & Canning Hub #04"
    assert data["daily_throughput_capacity_kg"] == 5000.0


# =====================================================================
# TEST 2: RAW MATERIAL INTAKE WITH FULL FIELD CONTRACT
# =====================================================================

def test_raw_material_intake(client, auth_headers, test_fpu_env):
    unit_id = test_fpu_env["unit_id"]
    now = datetime.now(timezone.utc)

    payload = {
        "material_name": "Organic Roma Tomatoes",
        "category": "PRODUCE",
        "lot_number": "LOT-TOM-2026-001",
        "initial_quantity": 800.0,
        "unit": "kg",
        "storage_condition": "REFRIGERATED",
        "storage_location": "Cold Room Bay 2",
        "harvest_or_mfg_date": (now - timedelta(days=4)).isoformat(),
        "expiry_date": (now + timedelta(days=6)).isoformat(),
        "quality_status": "APPROVED",
        "packaging_condition": "INTACT",
        "supplier": "Central Valley Produce Co-Op",
        "cost_per_unit": 0.95
    }

    resp = client.post(f"/api/v1/processing/{unit_id}/raw-materials", json=payload, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["material_name"] == "Organic Roma Tomatoes"
    assert data["current_quantity"] == 800.0
    assert data["status"] == "AVAILABLE"
    assert data["days_to_expiry"] > 0
    assert data["expiry_urgency_tier"] in ["WARNING_7_DAYS", "OPTIMAL"]


# =====================================================================
# TEST 3: FEFO (FIRST EXPIRE, FIRST OUT) ALLOCATION ALGORITHM
# =====================================================================

def test_fefo_allocation_algorithm(client, auth_headers, test_fpu_env):
    unit_id = test_fpu_env["unit_id"]
    now = datetime.now(timezone.utc)

    # Ingest 3 distinct lots with different expiration dates:
    # Lot A: Expires in 2 days (Earliest - should be picked FIRST)
    # Lot B: Expires in 5 days (Middle - should be picked SECOND)
    # Lot C: Expires in 14 days (Latest - should be picked LAST)

    lots = [
        {"lot": "LOT-A-EXP2D", "qty": 150.0, "days": 2},
        {"lot": "LOT-B-EXP5D", "qty": 200.0, "days": 5},
        {"lot": "LOT-C-EXP14D", "qty": 500.0, "days": 14}
    ]

    for item in lots:
        payload = {
            "material_name": "Culinary Sweet Apples",
            "category": "PRODUCE",
            "lot_number": item["lot"],
            "initial_quantity": item["qty"],
            "unit": "kg",
            "harvest_or_mfg_date": (now - timedelta(days=2)).isoformat(),
            "expiry_date": (now + timedelta(days=item["days"])).isoformat(),
            "quality_status": "APPROVED",
            "packaging_condition": "INTACT",
            "supplier": "Golden State Orchards"
        }
        res = client.post(f"/api/v1/processing/{unit_id}/raw-materials", json=payload, headers=auth_headers)
        assert res.status_code == 201

    # Request 250 kg for a batch:
    # Strict FEFO requires:
    # - 150 kg from Lot A (fully depleted)
    # - 100 kg from Lot B (partial, 100 kg remaining)
    # - 0 kg from Lot C
    alloc_req = {
        "material_name": "Sweet Apples",
        "required_quantity": 250.0,
        "unit": "kg"
    }

    resp = client.post(f"/api/v1/processing/{unit_id}/fefo/allocate", json=alloc_req, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()

    assert data["is_fulfilled"] is True
    assert data["total_allocated"] == 250.0
    assert len(data["pick_list"]) == 2

    # Step 1 should be Lot A
    step1 = data["pick_list"][0]
    assert step1["lot_number"] == "LOT-A-EXP2D"
    assert step1["allocated_quantity"] == 150.0
    assert step1["remaining_in_lot"] == 0.0

    # Step 2 should be Lot B
    step2 = data["pick_list"][1]
    assert step2["lot_number"] == "LOT-B-EXP5D"
    assert step2["allocated_quantity"] == 100.0
    assert step2["remaining_in_lot"] == 100.0


# =====================================================================
# TEST 4: FEFO QUEUE ENDPOINT
# =====================================================================

def test_fefo_queue(client, auth_headers, test_fpu_env):
    unit_id = test_fpu_env["unit_id"]
    now = datetime.now(timezone.utc)

    # Ingest 3 lots with different expiry dates to guarantee test isolation
    for lot_code, days in [("LOT-Q-01", 3), ("LOT-Q-02", 7), ("LOT-Q-03", 15)]:
        payload = {
            "material_name": "Queue Test Berries",
            "category": "PRODUCE",
            "lot_number": lot_code,
            "initial_quantity": 100.0,
            "unit": "kg",
            "harvest_or_mfg_date": now.isoformat(),
            "expiry_date": (now + timedelta(days=days)).isoformat(),
            "quality_status": "APPROVED",
            "packaging_condition": "INTACT"
        }
        res = client.post(f"/api/v1/processing/{unit_id}/raw-materials", json=payload, headers=auth_headers)
        assert res.status_code == 201

    resp = client.get(f"/api/v1/processing/{unit_id}/fefo/queue", headers=auth_headers)
    assert resp.status_code == 200
    queue = resp.json()
    assert len(queue) >= 3

    # Verify strict ascending order of days_to_expiry
    for i in range(len(queue) - 1):
        assert queue[i]["days_to_expiry"] <= queue[i + 1]["days_to_expiry"]
        assert queue[i]["fefo_priority_rank"] == i + 1


# =====================================================================
# TEST 5: PRODUCTION BATCH CREATION & AUTOMATIC RAW MATERIAL CONSUMPTION
# =====================================================================

def test_production_batch_creation_and_yield(client, auth_headers, test_fpu_env):
    unit_id = test_fpu_env["unit_id"]
    now = datetime.now(timezone.utc)

    # 1. Intake fresh carrots lot
    rm_payload = {
        "material_name": "Surplus Carrots",
        "category": "PRODUCE",
        "lot_number": "LOT-CARROT-99",
        "initial_quantity": 400.0,
        "unit": "kg",
        "harvest_or_mfg_date": (now - timedelta(days=1)).isoformat(),
        "expiry_date": (now + timedelta(days=10)).isoformat(),
        "quality_status": "APPROVED",
        "packaging_condition": "INTACT"
    }
    rm_res = client.post(f"/api/v1/processing/{unit_id}/raw-materials", json=rm_payload, headers=auth_headers)
    assert rm_res.status_code == 201
    rm_id = rm_res.json()["id"]

    # 2. Produce batch using 250 kg of carrots
    batch_payload = {
        "batch_number": "PB-CARROT-PUREE-001",
        "product_name": "Aseptic Carrot Puree",
        "category": "PUREE",
        "planned_quantity": 250.0,
        "actual_quantity": 240.0,  # 96% yield
        "unit": "kg",
        "manufacturing_date": now.isoformat(),
        "expiry_date": (now + timedelta(days=90)).isoformat(),
        "quality_status": "PASSED",
        "packaging_condition": "INTACT",
        "surplus_quantity": 80.0,  # 80 kg surplus for redistribution
        "raw_materials": [
            {
                "raw_material_id": rm_id,
                "quantity_used": 250.0,
                "fefo_sequence_order": 1
            }
        ]
    }

    resp = client.post(f"/api/v1/processing/{unit_id}/batches", json=batch_payload, headers=auth_headers)
    assert resp.status_code == 201
    batch_data = resp.json()
    assert batch_data["batch_number"] == "PB-CARROT-PUREE-001"
    assert batch_data["yield_percentage"] == 96.0
    assert batch_data["redistributable_stock"] == 80.0
    assert batch_data["redistribution_status"] == "AVAILABLE_FOR_REDISTRIBUTION"

    # 3. Verify raw material was deducted from 400 to 150 kg
    rm_check = client.get(f"/api/v1/processing/raw-materials/{rm_id}", headers=auth_headers).json()
    assert rm_check["current_quantity"] == 150.0


# =====================================================================
# TEST 6: DAMAGED PACKAGING, QUALITY REJECTION & VALORIZATION
# =====================================================================

def test_damaged_packaging_and_rejections(client, auth_headers, test_fpu_env):
    unit_id = test_fpu_env["unit_id"]
    now = datetime.now(timezone.utc)

    # 1. Create a batch that had sealing failures
    batch_payload = {
        "batch_number": "PB-APPLE-CHIPS-DEFECT-01",
        "product_name": "Dehydrated Apple Chips",
        "category": "DEHYDRATED",
        "planned_quantity": 100.0,
        "actual_quantity": 100.0,
        "unit": "kg",
        "manufacturing_date": now.isoformat(),
        "expiry_date": (now + timedelta(days=120)).isoformat(),
        "quality_status": "DAMAGED_PACKAGING",
        "packaging_condition": "DAMAGED_PACKAGING",
        "damaged_packaging_units": 18.0,
        "rejected_quantity": 18.0,
        "rejection_reason": "Nitrogen flush seal puncture during vacuum bagging",
        "disposition_action": "ANIMAL_FEED_VALORIZATION",
        "surplus_quantity": 0.0
    }

    resp = client.post(f"/api/v1/processing/{unit_id}/batches", json=batch_payload, headers=auth_headers)
    assert resp.status_code == 201
    batch_data = resp.json()
    batch_id = batch_data["id"]

    assert batch_data["status"] == "REJECTED"
    assert batch_data["damaged_packaging_units"] == 18.0
    assert batch_data["disposition_action"] == "ANIMAL_FEED_VALORIZATION"

    # 2. Update QC station decision
    update_payload = {
        "quality_status": "REJECTED",
        "rejection_reason": "Confirmed seal rupture and moisture infiltration",
        "disposition_action": "COMPOST_BIOGAS",
        "qc_officer": "Inspector Marcus Vance"
    }
    patch_res = client.patch(f"/api/v1/processing/batches/{batch_id}/quality", json=update_payload, headers=auth_headers)
    assert patch_res.status_code == 200
    patched = patch_res.json()
    assert patched["qc_officer"] == "Inspector Marcus Vance"
    assert patched["disposition_action"] == "COMPOST_BIOGAS"


# =====================================================================
# TEST 7: CONFIGURABLE THRESHOLD RULES (PRODUCT & CATEGORY)
# =====================================================================

def test_configurable_threshold_rules(client, auth_headers, test_fpu_env):
    unit_id = test_fpu_env["unit_id"]

    # 1. Configure dairy category threshold (4d warning, 2d urgent, 1d critical)
    dairy_rule = {
        "target_type": "CATEGORY",
        "target_name": "DAIRY",
        "warning_threshold_days": 4.0,
        "urgent_threshold_days": 2.0,
        "critical_threshold_days": 1.0,
        "custom_safety_notes": "High microbial susceptibility pasteurized dairy feedstock"
    }
    r1 = client.post(f"/api/v1/processing/{unit_id}/thresholds", json=dairy_rule, headers=auth_headers)
    assert r1.status_code == 201
    assert r1.json()["warning_threshold_days"] == 4.0

    # 2. Configure canned goods category threshold (30d warning, 14d urgent, 5d critical)
    canning_rule = {
        "target_type": "CATEGORY",
        "target_name": "PROCESSED_CANNING",
        "warning_threshold_days": 30.0,
        "urgent_threshold_days": 14.0,
        "critical_threshold_days": 5.0,
        "custom_safety_notes": "Aseptic canned long shelf life products"
    }
    r2 = client.post(f"/api/v1/processing/{unit_id}/thresholds", json=canning_rule, headers=auth_headers)
    assert r2.status_code == 201

    # 3. List rules
    rules = client.get(f"/api/v1/processing/{unit_id}/thresholds", headers=auth_headers).json()
    assert len(rules) >= 2


# =====================================================================
# TEST 8: AUTOMATIC EXPIRY ALERTS (7d, 3d, 1d & EXPIRED)
# =====================================================================

def test_automatic_expiry_alerts(client, auth_headers, test_fpu_env):
    unit_id = test_fpu_env["unit_id"]
    now = datetime.now(timezone.utc)

    # Ingest an item expiring tomorrow (< 1 day -> CRITICAL)
    crit_payload = {
        "material_name": "Fresh Spinach Puree Feedstock",
        "category": "PRODUCE",
        "lot_number": "LOT-CRIT-01D",
        "initial_quantity": 120.0,
        "unit": "kg",
        "harvest_or_mfg_date": (now - timedelta(days=5)).isoformat(),
        "expiry_date": (now + timedelta(hours=18)).isoformat(),
        "quality_status": "APPROVED",
        "packaging_condition": "INTACT"
    }
    client.post(f"/api/v1/processing/{unit_id}/raw-materials", json=crit_payload, headers=auth_headers)

    # Fetch automatic alerts
    resp = client.get(f"/api/v1/processing/{unit_id}/alerts", headers=auth_headers)
    assert resp.status_code == 200
    alerts_data = resp.json()

    assert alerts_data["total_alerts"] > 0
    assert alerts_data["critical_count"] >= 1

    # Verify alert attributes
    alert_codes = [a["code"] for a in alerts_data["alerts"]]
    assert "LOT-CRIT-01D" in alert_codes


# =====================================================================
# TEST 9: SURPLUS DECLARATION & REDISTRIBUTION TO RECIPIENT
# =====================================================================

def test_surplus_redistribution_to_recipient(client, auth_headers, test_fpu_env):
    unit_id = test_fpu_env["unit_id"]
    recipient_id = test_fpu_env["recipient_id"]
    now = datetime.now(timezone.utc)

    # 1. Create a finished batch with surplus
    batch_payload = {
        "batch_number": "PB-TOM-SOUP-SURPLUS-01",
        "product_name": "Upcycled Roasted Tomato Soup",
        "category": "PROCESSED_CANNING",
        "planned_quantity": 500.0,
        "actual_quantity": 500.0,
        "unit": "kg",
        "manufacturing_date": now.isoformat(),
        "expiry_date": (now + timedelta(days=60)).isoformat(),
        "quality_status": "PASSED",
        "packaging_condition": "INTACT",
        "surplus_quantity": 200.0
    }
    batch_res = client.post(f"/api/v1/processing/{unit_id}/batches", json=batch_payload, headers=auth_headers)
    assert batch_res.status_code == 201
    batch_id = batch_res.json()["id"]

    # 2. Redistribute 150 kg to Second Harvest Food Bank
    redist_req = {
        "redistribute_quantity": 150.0,
        "recipient_id": recipient_id,
        "title": "150kg Canned Roasted Tomato Soup Donation",
        "notes": "Direct pallet delivery for family emergency food boxes"
    }

    redist_res = client.post(f"/api/v1/processing/batches/{batch_id}/redistribute", json=redist_req, headers=auth_headers)
    assert redist_res.status_code == 200
    redist_data = redist_res.json()

    assert redist_data["redistributed_quantity"] == 150.0
    assert redist_data["remaining_stock"] == 50.0
    assert redist_data["recipient_name"] == "Second Harvest Regional Food Bank"


# =====================================================================
# TEST 10: END-TO-END BATCH TRACEABILITY (RAW -> BATCH -> FINISHED -> SURPLUS -> RECIPIENT)
# =====================================================================

def test_full_chain_batch_traceability(client, auth_headers, test_fpu_env):
    unit_id = test_fpu_env["unit_id"]
    recipient_id = test_fpu_env["recipient_id"]
    now = datetime.now(timezone.utc)

    # 1. Intake Raw Material
    rm_res = client.post(f"/api/v1/processing/{unit_id}/raw-materials", json={
        "material_name": "Traceable Roma Tomatoes",
        "category": "PRODUCE",
        "lot_number": "LOT-TRACE-TOM-01",
        "initial_quantity": 500.0,
        "unit": "kg",
        "harvest_or_mfg_date": (now - timedelta(days=3)).isoformat(),
        "expiry_date": (now + timedelta(days=12)).isoformat(),
        "quality_status": "APPROVED",
        "packaging_condition": "INTACT",
        "supplier": "Sun Valley Organics"
    }, headers=auth_headers)
    assert rm_res.status_code == 201
    rm_id = rm_res.json()["id"]

    # 2. Produce Batch with Raw Material
    batch_res = client.post(f"/api/v1/processing/{unit_id}/batches", json={
        "batch_number": "PB-TRACE-PUREE-99",
        "product_name": "San Marzano Puree Paste",
        "category": "PUREE",
        "planned_quantity": 300.0,
        "actual_quantity": 290.0,
        "unit": "kg",
        "manufacturing_date": now.isoformat(),
        "expiry_date": (now + timedelta(days=180)).isoformat(),
        "quality_status": "PASSED",
        "packaging_condition": "INTACT",
        "surplus_quantity": 100.0,
        "raw_materials": [{"raw_material_id": rm_id, "quantity_used": 300.0, "fefo_sequence_order": 1}]
    }, headers=auth_headers)
    assert batch_res.status_code == 201
    batch_id = batch_res.json()["id"]

    # 3. Redistribute Surplus to Recipient
    redist_res = client.post(f"/api/v1/processing/batches/{batch_id}/redistribute", json={
        "redistribute_quantity": 100.0,
        "recipient_id": recipient_id,
        "title": "100kg Tomato Puree Direct Rescue Donation"
    }, headers=auth_headers)
    assert redist_res.status_code == 200

    # 4. Search by the batch code
    resp = client.get("/api/v1/processing/traceability/PB-TRACE-PUREE-99", headers=auth_headers)
    assert resp.status_code == 200
    chain = resp.json()

    assert chain["production_batch"]["batch_number"] == "PB-TRACE-PUREE-99"
    assert chain["finished_product"]["product_name"] == "San Marzano Puree Paste"
    assert chain["surplus_donation"] is not None
    assert chain["recipient"]["recipient_name"] == "Second Harvest Regional Food Bank"

    # Verify linear trace stages
    stages = [node["stage"] for node in chain["linear_trace_steps"]]
    assert "RAW_MATERIAL" in stages
    assert "PRODUCTION_BATCH" in stages
    assert "FINISHED_PRODUCT" in stages
    assert "SURPLUS_DONATION" in stages
    assert "RECIPIENT" in stages


# =====================================================================
# TEST 11: EXECUTIVE DASHBOARD SUMMARY (ALL 6 PILLARS)
# =====================================================================

def test_executive_dashboard_summary(client, auth_headers, test_fpu_env):
    unit_id = test_fpu_env["unit_id"]
    now = datetime.now(timezone.utc)

    # Ingest a lot and create a batch so dashboard has live metrics
    client.post(f"/api/v1/processing/{unit_id}/raw-materials", json={
        "material_name": "Dashboard Sweet Corn",
        "category": "PRODUCE",
        "lot_number": "LOT-DASH-01",
        "initial_quantity": 300.0,
        "unit": "kg",
        "harvest_or_mfg_date": now.isoformat(),
        "expiry_date": (now + timedelta(days=2)).isoformat(),
        "quality_status": "APPROVED",
        "packaging_condition": "INTACT"
    }, headers=auth_headers)

    client.post(f"/api/v1/processing/{unit_id}/batches", json={
        "batch_number": "PB-DASH-BATCH-01",
        "product_name": "Vacuum Sealed Sweet Corn",
        "category": "PROCESSED_CANNING",
        "planned_quantity": 200.0,
        "actual_quantity": 200.0,
        "unit": "kg",
        "manufacturing_date": now.isoformat(),
        "expiry_date": (now + timedelta(days=365)).isoformat(),
        "quality_status": "PASSED",
        "packaging_condition": "INTACT",
        "surplus_quantity": 50.0
    }, headers=auth_headers)

    resp = client.get(f"/api/v1/processing/{unit_id}/dashboard", headers=auth_headers)
    assert resp.status_code == 200
    dash = resp.json()

    # Pillar 1: Inventory
    assert "inventory" in dash
    assert dash["inventory"]["total_inventory_kg"] > 0
    assert dash["inventory"]["total_raw_lots_count"] > 0

    # Pillar 2: Near Expiry
    assert "near_expiry" in dash
    assert "warning_7d_count" in dash["near_expiry"]
    assert "urgent_3d_count" in dash["near_expiry"]
    assert "critical_1d_count" in dash["near_expiry"]

    # Pillar 3: Expired
    assert "expired" in dash
    assert "total_expired_count" in dash["expired"]

    # Pillar 4: Production
    assert "production" in dash
    assert dash["production"]["total_batches_all_time"] > 0
    assert dash["production"]["fefo_adherence_percentage"] > 90.0

    # Pillar 5: Rejected
    assert "rejected" in dash
    assert "by_disposition" in dash["rejected"]

    # Pillar 6: Redistributable Stock
    assert "redistributable_stock" in dash
    assert dash["redistributable_stock"]["total_surplus_generated_kg"] > 0
