"""
FoodLoop AI - Database Seeding Engine
Populates the database with realistic sample records across all 30 core platform tables.
Uses SQLAlchemy 2.0 ORM objects for 100% dialect independence (PostgreSQL / SQLite).
"""

import os
import sys
import logging
from datetime import datetime, timezone, timedelta

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("foodloop.seed")

# Add backend to path
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.models import (
    User, Organization, OrganizationMember, Kitchen, ProcessingUnit,
    Menu, MenuItem, Ingredient, Inventory, InventoryTransaction,
    ProductionBatch, ConsumptionRecord, WasteRecord, SurplusItem,
    Recipient, RecipientRequirement, Donation, DonationItem,
    PickupRequest, Driver, Vehicle, Route, Delivery,
    QrVerification, Notification, ModelPrediction, AiRecommendation,
    ImpactMetric, Document, AuditLog
)


def run_seed():
    logger.info("[*] Seeding FoodLoop AI Database with sample records via SQLAlchemy ORM...")
    session = SessionLocal()

    try:
        now = datetime.now(timezone.utc)
        pwd_hash = hash_password("DemoSafePass2026!")

        # 1. USERS (6 ROLES)
        u_admin = User(
            id="11111111-1111-1111-1111-111111111111",
            email="admin@foodloop.ai",
            password_hash=pwd_hash,
            full_name="Eleanor Vance",
            role="ADMIN",
            phone="+1-555-0100",
            avatar_url="https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150",
            is_active=True
        )
        u_chef = User(
            id="22222222-2222-2222-2222-222222222222",
            email="chef.vance@hyatt-culinary.com",
            password_hash=pwd_hash,
            full_name="Executive Chef Marcus Vance",
            role="KITCHEN_MANAGER",
            phone="+1-555-0101",
            avatar_url="https://images.unsplash.com/photo-1577219491135-ce391730fb2c?w=150",
            is_active=True
        )
        u_proc = User(
            id="33333333-3333-3333-3333-333333333333",
            email="processor.chen@bayprocessing.com",
            password_hash=pwd_hash,
            full_name="Dr. David Chen",
            role="PROCESSOR",
            phone="+1-555-0102",
            avatar_url="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150",
            is_active=True
        )
        u_ngo = User(
            id="44444444-4444-4444-4444-444444444444",
            email="director@stjudefoodbank.org",
            password_hash=pwd_hash,
            full_name="Maria Rodriguez",
            role="NGO",
            phone="+1-555-0103",
            avatar_url="https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=150",
            is_active=True
        )
        u_driver = User(
            id="55555555-5555-5555-5555-555555555555",
            email="alex.driver@looplogistics.com",
            password_hash=pwd_hash,
            full_name="Alex Mercer",
            role="DRIVER",
            phone="+1-555-0104",
            avatar_url="https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150",
            is_active=True
        )
        u_auditor = User(
            id="66666666-6666-6666-6666-666666666666",
            email="auditor.helena@dph-safety.gov",
            password_hash=pwd_hash,
            full_name="Helena Brandt",
            role="AUDITOR",
            phone="+1-555-0105",
            avatar_url="https://images.unsplash.com/photo-1580489944761-15a19d654956?w=150",
            is_active=True
        )

        for u in [u_admin, u_chef, u_proc, u_ngo, u_driver, u_auditor]:
            session.merge(u)

        # 2. ORGANIZATIONS
        org_hq = Organization(
            id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            name="FoodLoop AI Global Platform HQ",
            org_type="GOVERNMENT_AUDITOR",
            registration_number="REG-FL-HQ-001",
            tax_id="TAX-889412-A",
            license_fssai_fda="LIC-FDA-99410",
            address="1 Market St, Suite 400, San Francisco, CA",
            latitude=37.7955,
            longitude=-122.3937,
            contact_email="governance@foodloop.ai",
            contact_phone="+1-555-0100",
            is_verified=True
        )
        org_kitchen = Organization(
            id="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
            name="Grand Hyatt San Francisco Culinary Center",
            org_type="COMMERCIAL_KITCHEN",
            registration_number="REG-HYATT-SF-04",
            tax_id="TAX-441209-B",
            license_fssai_fda="LIC-FSSAI-88124",
            address="345 Stockton St, San Francisco, CA",
            latitude=37.7892,
            longitude=-122.4064,
            contact_email="kitchen@hyatt-culinary.com",
            contact_phone="+1-415-398-1234",
            is_verified=True
        )
        org_proc = Organization(
            id="cccccccc-cccc-cccc-cccc-cccccccccccc",
            name="Bay Area Canning & Puree Plant",
            org_type="FOOD_PROCESSOR",
            registration_number="REG-BAY-FPU-02",
            tax_id="TAX-661298-C",
            license_fssai_fda="LIC-FDA-44192",
            address="780 Industrial Pkwy, Hayward, CA",
            latitude=37.6481,
            longitude=-122.0682,
            contact_email="intake@bayprocessing.com",
            contact_phone="+1-510-782-9900",
            is_verified=True
        )
        org_ngo = Organization(
            id="dddddddd-dddd-dddd-dddd-dddddddddddd",
            name="Downtown St. Jude Food Bank & Pantry",
            org_type="NGO",
            registration_number="REG-STJUDE-NGO-09",
            tax_id="TAX-501C3-1192",
            license_fssai_fda="LIC-HEALTH-3391",
            address="812 Mission Blvd, San Francisco, CA",
            latitude=37.7818,
            longitude=-122.4057,
            contact_email="intake@stjudefoodbank.org",
            contact_phone="+1-415-552-4411",
            is_verified=True
        )
        org_fleet = Organization(
            id="eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee",
            name="FoodLoop Express Logistics Fleet",
            org_type="LOGISTICS_PROVIDER",
            registration_number="REG-LOOP-FLEET-03",
            tax_id="TAX-339912-E",
            license_fssai_fda="LIC-DOT-77491",
            address="100 Logistics Way, Bay 4, South San Francisco, CA",
            latitude=37.6547,
            longitude=-122.4077,
            contact_email="dispatch@looplogistics.com",
            contact_phone="+1-650-877-3300",
            is_verified=True
        )

        for o in [org_hq, org_kitchen, org_proc, org_ngo, org_fleet]:
            session.merge(o)
        session.commit()

        # 3. ORGANIZATION MEMBERS
        members = [
            OrganizationMember(id="m1111111-1111-1111-1111-111111111111", organization_id=org_hq.id, user_id=u_admin.id, role_in_org="SUPER_ADMIN", is_primary=True),
            OrganizationMember(id="m2222222-2222-2222-2222-222222222222", organization_id=org_kitchen.id, user_id=u_chef.id, role_in_org="EXECUTIVE_CHEF", is_primary=True),
            OrganizationMember(id="m3333333-3333-3333-3333-333333333333", organization_id=org_proc.id, user_id=u_proc.id, role_in_org="PLANT_DIRECTOR", is_primary=True),
            OrganizationMember(id="m4444444-4444-4444-4444-444444444444", organization_id=org_ngo.id, user_id=u_ngo.id, role_in_org="LOGISTICS_DIRECTOR", is_primary=True),
            OrganizationMember(id="m5555555-5555-5555-5555-555555555555", organization_id=org_fleet.id, user_id=u_driver.id, role_in_org="SENIOR_COURIER", is_primary=True),
        ]
        for m in members:
            session.merge(m)
        session.commit()

        # 4. KITCHENS & FPUs
        k_hyatt = Kitchen(
            id="k1111111-1111-1111-1111-111111111111",
            organization_id=org_kitchen.id,
            name="Grand Hyatt Main Banquet Kitchen #04",
            address="345 Stockton St, San Francisco, CA",
            latitude=37.7892,
            longitude=-122.4064,
            daily_meal_capacity=1500,
            storage_specs={"ambient_sqm": 80, "refrigerated_liters": 4500, "frozen_liters": 2500},
            is_active=True
        )
        session.merge(k_hyatt)

        fpu_bay = ProcessingUnit(
            id="p1111111-1111-1111-1111-111111111111",
            organization_id=org_proc.id,
            name="Bay Area Canning & Puree Plant #02",
            address="780 Industrial Pkwy, Hayward, CA",
            latitude=37.6481,
            longitude=-122.0682,
            processing_type="Aseptic Tomato & Puree Processing",
            daily_capacity_kg=5000.0,
            cold_tank_capacity_liters=10000.0,
            is_active=True
        )
        session.merge(fpu_bay)
        session.commit()

        # 5. MENUS & MENU ITEMS
        menu_lunch = Menu(
            id="menu1111-1111-1111-1111-111111111111",
            kitchen_id=k_hyatt.id,
            name="Executive Conference Lunch Service",
            service_date=now,
            meal_service="LUNCH",
            planned_headcount=480,
            status="IN_PRODUCTION"
        )
        session.merge(menu_lunch)

        mi_chicken = MenuItem(
            id="mi111111-1111-1111-1111-111111111111",
            menu_id=menu_lunch.id,
            dish_name="Mediterranean Lemon Herb Grilled Chicken",
            planned_portions=350,
            portion_weight_grams=420.0,
            dietary_category="STANDARD",
            allergens=["Dairy"],
            cost_per_portion=4.15,
            status="ACTIVE"
        )
        session.merge(mi_chicken)
        session.commit()

        # 6. INGREDIENTS & INVENTORY
        ing_chicken = Ingredient(
            id="ing11111-1111-1111-1111-111111111111",
            organization_id=org_kitchen.id,
            name="Fresh Boneless Chicken Thighs",
            category="Meat & Poultry",
            unit="kg",
            standard_cost_per_unit=6.80,
            allergen_profile=[],
            storage_temp_category="REFRIGERATED"
        )
        session.merge(ing_chicken)

        inv_chicken = Inventory(
            id="inv11111-1111-1111-1111-111111111111",
            kitchen_id=k_hyatt.id,
            ingredient_id=ing_chicken.id,
            lot_number="LOT-2026-CHK-71",
            current_quantity=82.0,
            reserved_quantity=20.0,
            unit="kg",
            reorder_level=30.0,
            storage_temp="Chilled (0-4°C)",
            storage_location="Walk-in Chiller Bay A",
            expiry_date=now + timedelta(days=4),
            status="OPTIMAL"
        )
        session.merge(inv_chicken)

        inv_tx = InventoryTransaction(
            id="it111111-1111-1111-1111-111111111111",
            inventory_id=inv_chicken.id,
            transaction_type="INFLOW_PURCHASE",
            quantity=100.0,
            unit="kg",
            reference_id="PO-99412",
            performed_by_user_id=u_chef.id,
            notes="Delivery received with HACCP cold chain stamp."
        )
        session.merge(inv_tx)
        session.commit()

        # 7. PRODUCTION BATCH
        batch_1 = ProductionBatch(
            id="pb111111-1111-1111-1111-111111111111",
            kitchen_id=k_hyatt.id,
            menu_item_id=mi_chicken.id,
            batch_number="BATCH-2026-0927-A",
            planned_quantity=350.0,
            actual_prepared_quantity=345.0,
            unit="portions",
            station="Hot Kitchen Range A",
            target_temp_c=74.0,
            current_temp_c=76.5,
            haccp_compliant=True,
            chef_user_id=u_chef.id,
            status="HOLDING",
            started_at=now - timedelta(hours=2),
            completed_at=now - timedelta(minutes=30)
        )
        session.merge(batch_1)
        session.commit()

        # 8. CONSUMPTION RECORD
        consump = ConsumptionRecord(
            id="cr111111-1111-1111-1111-111111111111",
            batch_id=batch_1.id,
            meal_service="LUNCH",
            planned_headcount=480,
            actual_headcount=420,
            variance_percentage=-12.5,
            total_prepared_kg=144.9,
            total_consumed_kg=102.4,
            unconsumed_kg=42.5,
            diverted_to_surplus_kg=42.5,
            recorded_by_user_id=u_chef.id,
            notes="Rainy conditions reduced attendance. 42.5 kg immediately blast chilled."
        )
        session.merge(consump)

        # 9. WASTE RECORD
        waste_1 = WasteRecord(
            id="wr111111-1111-1111-1111-111111111111",
            kitchen_id=k_hyatt.id,
            batch_id=batch_1.id,
            waste_category="PREPARATION_TRIMMINGS",
            weight_kg=14.2,
            cost_loss_usd=28.40,
            ghg_co2e_kg=35.5,
            epa_hierarchy_tier="COMPOST",
            department="Cold Prep Line 1",
            root_cause="Root vegetable peelings & broccoli stalk ends",
            logged_by_user_id=u_chef.id
        )
        session.merge(waste_1)
        session.commit()

        # 10. SURPLUS ITEM
        surplus_1 = SurplusItem(
            id="s1111111-1111-1111-1111-111111111111",
            organization_id=org_kitchen.id,
            kitchen_id=k_hyatt.id,
            batch_id=batch_1.id,
            title="Mediterranean Lemon Herb Grilled Chicken",
            description="Surplus banquet entrees blast-chilled to 3.2°C.",
            category="COOKED_MEALS",
            quantity_kg=42.5,
            portions=85,
            storage_temp="REFRIGERATED",
            safe_consumption_deadline=now + timedelta(hours=4),
            blast_chilled_at=now - timedelta(hours=1),
            calculated_shelf_life_hours=4.5,
            urgency_tier="EXPEDITED",
            pickup_address="345 Stockton St, Loading Dock B",
            pickup_lat=37.7892,
            pickup_lng=-122.4064,
            dietary_tags=["Halal", "High Protein"],
            status="DECLARED"
        )
        session.merge(surplus_1)
        session.commit()

        # 11. RECIPIENT & REQUIREMENTS
        rec_stjude = Recipient(
            id="r1111111-1111-1111-1111-111111111111",
            organization_id=org_ngo.id,
            name="Downtown St. Jude Food Bank",
            facility_type="FOOD_BANK",
            address="812 Mission Blvd, San Francisco, CA",
            latitude=37.7818,
            longitude=-122.4057,
            max_daily_intake_kg=300.0,
            cold_storage_available=True,
            walk_in_chiller_capacity_kg=150.0,
            verified_charity_id="CH-501C3-9981",
            contact_person="Maria Rodriguez",
            contact_phone="+1-415-552-4411",
            is_active=True
        )
        session.merge(rec_stjude)

        req_stjude = RecipientRequirement(
            id="rr111111-1111-1111-1111-111111111111",
            recipient_id=rec_stjude.id,
            acceptable_categories=["COOKED_MEALS", "BAKERY", "DAIRY", "PRODUCE"],
            dietary_preferences=["Halal", "Vegetarian"],
            required_storage_temp="ANY",
            min_portions_per_drop=20,
            max_delivery_distance_km=15.0
        )
        session.merge(req_stjude)
        session.commit()

        # 12. DONATIONS & ITEMS
        donation_1 = Donation(
            id="d1111111-1111-1111-1111-111111111111",
            donor_org_id=org_kitchen.id,
            recipient_org_id=org_ngo.id,
            tracking_number="TRK-FL-89412-CA",
            total_weight_kg=42.5,
            total_portions=85,
            status="COURIER_ASSIGNED",
            haccp_verified=True,
            safe_handling_ack=True
        )
        session.merge(donation_1)

        di_1 = DonationItem(
            id="di111111-1111-1111-1111-111111111111",
            donation_id=donation_1.id,
            surplus_item_id=surplus_1.id,
            allocated_quantity_kg=42.5,
            allocated_portions=85
        )
        session.merge(di_1)

        # 13. PICKUP REQUEST
        pickup_req = PickupRequest(
            id="pr111111-1111-1111-1111-111111111111",
            donation_id=donation_1.id,
            donor_address="345 Stockton St, Loading Dock B",
            donor_lat=37.7892,
            donor_lng=-122.4064,
            ready_time=now,
            latest_pickup_time=now + timedelta(hours=2),
            assigned_driver_id=u_driver.id,
            status="ACCEPTED"
        )
        session.merge(pickup_req)
        session.commit()

        # 14. VEHICLE & DRIVER
        veh_1 = Vehicle(
            id="v1111111-1111-1111-1111-111111111111",
            organization_id=org_fleet.id,
            license_plate="7XFL492",
            vehicle_type="REFRIGERATED_VAN",
            payload_capacity_kg=500.0,
            active_cooling=True,
            current_compartment_temp_c=3.4,
            is_active=True
        )
        session.merge(veh_1)

        driver_1 = Driver(
            id="drv11111-1111-1111-1111-111111111111",
            user_id=u_driver.id,
            organization_id=org_fleet.id,
            license_number="CA-DL-994821",
            driver_status="EN_ROUTE_PICKUP",
            current_lat=37.7880,
            current_lng=-122.4100,
            vehicle_id=veh_1.id
        )
        session.merge(driver_1)
        session.commit()

        # 15. ROUTE & DELIVERY
        route_1 = Route(
            id="rt111111-1111-1111-1111-111111111111",
            driver_id=driver_1.id,
            vehicle_id=veh_1.id,
            route_code="ROUTE-SF-402",
            total_distance_km=8.4,
            estimated_duration_mins=28.0,
            solver_status="OPTIMAL",
            solver_model="GOOGLE_OR_TOOLS_CVRPTW",
            waypoints_count=3,
            status="IN_PROGRESS"
        )
        session.merge(route_1)

        deliv_1 = Delivery(
            id="del11111-1111-1111-1111-111111111111",
            route_id=route_1.id,
            donation_id=donation_1.id,
            pickup_request_id=pickup_req.id,
            driver_id=driver_1.id,
            stop_sequence=1,
            status="IN_TRANSIT",
            actual_temp_at_delivery_c=3.4,
            distance_km=3.8,
            transit_time_mins=14.0
        )
        session.merge(deliv_1)

        # 16. QR VERIFICATION
        qr_1 = QrVerification(
            id="qr111111-1111-1111-1111-111111111111",
            delivery_id=deliv_1.id,
            stage="PICKUP_HANDOVER",
            nonce="nonce-9941a8e2b8344e7c",
            hmac_signature="a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e",
            payload={"batch_id": "pb111111", "kg": 42.5, "temp": 3.2},
            expires_at=now + timedelta(minutes=30),
            is_burned=True,
            verified_by_user_id=u_driver.id,
            verified_lat=37.7892,
            verified_lng=-122.4064,
            verified_temp_c=3.2
        )
        session.merge(qr_1)
        session.commit()

        # 17. NOTIFICATION
        notif_1 = Notification(
            id="notif111-1111-1111-1111-111111111111",
            user_id=u_chef.id,
            organization_id=org_kitchen.id,
            title="Courier Arriving at Dock B",
            message="Courier Alex Mercer (EV Van #3) is 0.8 km away for surplus pickup.",
            category="DISPATCH",
            priority="HIGH"
        )
        session.merge(notif_1)
        session.commit()

        # 18. PREDICTION & AI RECOMMENDATION
        pred_1 = ModelPrediction(
            id="pred1111-1111-1111-1111-111111111111",
            organization_id=org_kitchen.id,
            kitchen_id=k_hyatt.id,
            model_name="XGBoost_Surplus_Regressor",
            model_version="v2.1",
            prediction_type="DEMAND_HEADCOUNT",
            target_date=now + timedelta(days=1),
            predicted_value=425.0,
            confidence_lower_bound=395.0,
            confidence_upper_bound=455.0,
            r2_score=0.829
        )
        session.merge(pred_1)
        session.commit()

        ai_rec = AiRecommendation(
            id="rec11111-1111-1111-1111-111111111111",
            organization_id=org_kitchen.id,
            prediction_id=pred_1.id,
            recipe_or_item_name="Mediterranean Lemon Herb Grilled Chicken",
            recommendation_type="BATCH_SIZE_ADJUSTMENT",
            recommended_action="Reduce batch prep target from 480 to 425 portions.",
            rationale="Historical drop in Monday lunch headcount post-holiday weekend.",
            estimated_waste_reduction_kg=28.5,
            estimated_cost_savings_usd=232.0,
            confidence_percentage=94
        )
        session.merge(ai_rec)
        session.commit()

        # 19. IMPACT METRICS
        impact_1 = ImpactMetric(
            id="imp11111-1111-1111-1111-111111111111",
            organization_id=org_kitchen.id,
            donation_id=donation_1.id,
            food_diverted_kg=42.5,
            meals_provided=85,
            co2e_avoided_kg=106.25,
            water_saved_liters=2450.0,
            financial_value_usd=348.50,
            calculation_methodology="EPA_WARM_V15"
        )
        session.merge(impact_1)
        session.commit()

        # 20. DOCUMENTS (Vector RAG)
        doc_1 = Document(
            id="doc11111-1111-1111-1111-111111111111",
            title="FDA Food Code Section 3-501.19 (Time Control & 4-Hour Rule)",
            category="FDA_FOOD_CODE",
            content="Ready-to-eat TCS food held without temperature control must be discarded or consumed within 4 hours if removed from cold storage at or below 41°F (5°C).",
            regulatory_source="US FDA Food Code 2022",
            document_version="2022.3",
            is_public=True
        )
        session.merge(doc_1)
        session.commit()

        # 21. AUDIT LOG
        audit_1 = AuditLog(
            id="aud11111-1111-1111-1111-111111111111",
            organization_id=org_kitchen.id,
            user_id=u_chef.id,
            module="SURPLUS_DISPATCH",
            action="DECLARE_SURPLUS_ITEM",
            entity_name="surplus_items",
            entity_id=surplus_1.id,
            client_ip="192.168.1.104",
            sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        )
        session.merge(audit_1)
        session.commit()

        logger.info("[SUCCESS] All sample records committed to database successfully!")
        return True
    except Exception as e:
        session.rollback()
        logger.error(f"[ERROR] Database seeding failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        session.close()


if __name__ == "__main__":
    success = run_seed()
    sys.exit(0 if success else 1)
