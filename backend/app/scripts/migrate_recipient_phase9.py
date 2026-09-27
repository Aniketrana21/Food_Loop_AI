"""
FoodLoop AI - Phase 9 Recipient Matching Database Migration & Seed Script
Adds columns to recipients and surplus_items tables and seeds diverse recipient non-profits.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import text, inspect
from app.core.database import engine, SessionLocal
from app.models.models import Recipient, RecipientRequirement, Organization


def run_migration():
    inspector = inspect(engine)
    
    # 1. Migrate surplus_items columns
    if "surplus_items" in inspector.get_table_names():
        surplus_cols = [c['name'] for c in inspector.get_columns('surplus_items')]
        surplus_new = [
            ('allocated_recipient_id', 'VARCHAR(36)'),
            ('recipient_claim_status', 'VARCHAR(50)'),
            ('pickup_scheduled_time', 'TIMESTAMP'),
            ('pickup_driver_notes', 'TEXT'),
        ]
        with engine.connect() as conn:
            for col, col_type in surplus_new:
                if col not in surplus_cols:
                    print(f"Adding column '{col}' to surplus_items...")
                    conn.execute(text(f"ALTER TABLE surplus_items ADD COLUMN {col} {col_type}"))
            conn.commit()

    # 2. Migrate recipients columns
    if "recipients" in inspector.get_table_names():
        rec_cols = [c['name'] for c in inspector.get_columns('recipients')]
        rec_new = [
            ('pickup_available', 'BOOLEAN DEFAULT TRUE'),
            ('current_demand_portions', 'INTEGER DEFAULT 100'),
            ('current_demand_kg', 'FLOAT DEFAULT 40.0'),
            ('storage_capabilities', 'JSON'),
            ('verification_status', 'VARCHAR(50) DEFAULT \'VERIFIED\''),
            ('reliability_score', 'FLOAT DEFAULT 0.96'),
            ('operating_hours_description', 'VARCHAR(100) DEFAULT \'08:00 - 20:00 Daily\''),
        ]
        with engine.connect() as conn:
            for col, col_type in rec_new:
                if col not in rec_cols:
                    print(f"Adding column '{col}' to recipients...")
                    conn.execute(text(f"ALTER TABLE recipients ADD COLUMN {col} {col_type}"))
            conn.commit()

    print("Phase 9 columns verified successfully!")

    # 3. Seed realistic recipient organizations with varied characteristics
    db = SessionLocal()
    try:
        # Get an active organization ID to link
        org = db.query(Organization).first()
        org_id = org.id if org else str(uuid.uuid4())
        if not org:
            org = Organization(
                id=org_id,
                name="Regional Food Recovery Coalition",
                organization_type="CHARITY_NETWORK"
            )
            db.add(org)
            db.commit()

        seed_data = [
            {
                "id": "rec-001-st-jude",
                "name": "Downtown St. Jude Food Bank",
                "facility_type": "FOOD_BANK",
                "address": "450 4th Street, San Francisco, CA 94107",
                "latitude": 37.7812,
                "longitude": -122.3987,
                "max_daily_intake_kg": 200.0,
                "cold_storage_available": True,
                "walk_in_chiller_capacity_kg": 90.0,
                "verified_charity_id": "501C3-SF-942849",
                "contact_person": "Sister Beatrice Morales",
                "contact_phone": "+1-415-555-0144",
                "pickup_available": True,
                "current_demand_portions": 140,
                "current_demand_kg": 50.0,
                "storage_capabilities": ["COLD_HOLD", "DRY", "HOT_HOLD", "FROZEN"],
                "verification_status": "VERIFIED",
                "reliability_score": 0.98,
                "operating_hours_description": "07:30 - 20:30 Daily",
                "categories": ["COOKED_MEALS", "GRAINS", "VEGETABLES", "PROTEIN", "BAKERY", "SOUP"],
                "dietary": ["HALAL", "VEGETARIAN", "RICE_BASED", "HIGH_PROTEIN", "STANDARD"]
            },
            {
                "id": "rec-002-hope-mission",
                "name": "Hope Mission Family Shelter",
                "facility_type": "SHELTER",
                "address": "820 Folsom Street, San Francisco, CA 94103",
                "latitude": 37.7801,
                "longitude": -122.4045,
                "max_daily_intake_kg": 120.0,
                "cold_storage_available": True,
                "walk_in_chiller_capacity_kg": 45.0,
                "verified_charity_id": "501C3-CA-883921",
                "contact_person": "Marcus Vance",
                "contact_phone": "+1-415-555-0189",
                "pickup_available": True,
                "current_demand_portions": 85,
                "current_demand_kg": 30.0,
                "storage_capabilities": ["COLD_HOLD", "DRY", "HOT_HOLD"],
                "verification_status": "VERIFIED",
                "reliability_score": 0.95,
                "operating_hours_description": "08:00 - 21:00 Daily",
                "categories": ["COOKED_MEALS", "DAIRY", "VEGETABLES", "BAKERY", "SOUP", "GRAINS"],
                "dietary": ["FAMILY_FRIENDLY", "VEGETARIAN", "NUT_FREE", "STANDARD"]
            },
            {
                "id": "rec-003-harbor-light",
                "name": "Harbor Light Community Dining",
                "facility_type": "SOUP_KITCHEN",
                "address": "1275 Mission Street, San Francisco, CA 94103",
                "latitude": 37.7765,
                "longitude": -122.4140,
                "max_daily_intake_kg": 300.0,
                "cold_storage_available": True,
                "walk_in_chiller_capacity_kg": 150.0,
                "verified_charity_id": "501C3-SF-119284",
                "contact_person": "Chef David Alvarez",
                "contact_phone": "+1-415-555-0210",
                "pickup_available": True,
                "current_demand_portions": 220,
                "current_demand_kg": 80.0,
                "storage_capabilities": ["HOT_HOLD", "COLD_HOLD", "DRY", "FROZEN"],
                "verification_status": "VERIFIED",
                "reliability_score": 0.99,
                "operating_hours_description": "06:00 - 22:00 Daily",
                "categories": ["COOKED_MEALS", "SOUP", "VEGETABLES", "GRAINS", "PROTEIN", "BAKERY", "DAIRY"],
                "dietary": ["STANDARD", "HALAL", "VEGETARIAN", "HIGH_PROTEIN", "RICE_BASED"]
            },
            {
                "id": "rec-004-covenant-youth",
                "name": "Covenant Youth Haven",
                "facility_type": "YOUTH_REFUGE",
                "address": "1950 Post Street, San Francisco, CA 94115",
                "latitude": 37.7850,
                "longitude": -122.4350,
                "max_daily_intake_kg": 75.0,
                "cold_storage_available": True,
                "walk_in_chiller_capacity_kg": 30.0,
                "verified_charity_id": "501C3-CA-338291",
                "contact_person": "Nia Jackson",
                "contact_phone": "+1-415-555-0377",
                "pickup_available": False,  # Requires donor or 3rd-party delivery
                "current_demand_portions": 60,
                "current_demand_kg": 20.0,
                "storage_capabilities": ["COLD_HOLD", "DRY"],
                "verification_status": "VERIFIED",
                "reliability_score": 0.92,
                "operating_hours_description": "09:00 - 18:00 Mon-Sat",
                "categories": ["COOKED_MEALS", "BAKERY", "PROTEIN", "GRAINS"],
                "dietary": ["HIGH_PROTEIN", "DAIRY_FREE", "STANDARD"]
            },
            {
                "id": "rec-005-mission-green",
                "name": "Mission Green Community Pantry",
                "facility_type": "COMMUNITY_PANTRY",
                "address": "2840 24th Street, San Francisco, CA 94110",
                "latitude": 37.7530,
                "longitude": -122.4080,
                "max_daily_intake_kg": 50.0,
                "cold_storage_available": True,
                "walk_in_chiller_capacity_kg": 20.0,
                "verified_charity_id": "501C3-SF-772910",
                "contact_person": "Lucia Herrera",
                "contact_phone": "+1-415-555-0422",
                "pickup_available": True,
                "current_demand_portions": 45,
                "current_demand_kg": 15.0,
                "storage_capabilities": ["COLD_HOLD", "DRY"],
                "verification_status": "VERIFIED",
                "reliability_score": 0.91,
                "operating_hours_description": "10:00 - 18:00 Mon-Fri",
                "categories": ["VEGETABLES", "BAKERY", "GRAINS", "PRODUCE"],
                "dietary": ["VEGAN", "VEGETARIAN", "ORGANIC", "GLUTEN_FREE"]
            }
        ]

        for s in seed_data:
            existing = db.query(Recipient).filter(
                (Recipient.id == s["id"]) | (Recipient.name == s["name"])
            ).first()

            if not existing:
                rec = Recipient(
                    id=s["id"],
                    organization_id=org_id,
                    name=s["name"],
                    facility_type=s["facility_type"],
                    address=s["address"],
                    latitude=s["latitude"],
                    longitude=s["longitude"],
                    max_daily_intake_kg=s["max_daily_intake_kg"],
                    cold_storage_available=s["cold_storage_available"],
                    walk_in_chiller_capacity_kg=s["walk_in_chiller_capacity_kg"],
                    verified_charity_id=s["verified_charity_id"],
                    contact_person=s["contact_person"],
                    contact_phone=s["contact_phone"],
                    pickup_available=s["pickup_available"],
                    current_demand_portions=s["current_demand_portions"],
                    current_demand_kg=s["current_demand_kg"],
                    storage_capabilities=s["storage_capabilities"],
                    verification_status=s["verification_status"],
                    reliability_score=s["reliability_score"],
                    operating_hours_description=s["operating_hours_description"],
                    is_active=True
                )
                db.add(rec)
                db.flush()

                # Requirement
                req = RecipientRequirement(
                    recipient_id=rec.id,
                    acceptable_categories=s["categories"],
                    dietary_preferences=s["dietary"],
                    required_storage_temp="ANY",
                    min_portions_per_drop=10,
                    max_delivery_distance_km=25.0,
                    operating_hours={"description": s["operating_hours_description"]}
                )
                db.add(req)
                print(f"Created recipient: {s['name']}")
            else:
                # Update existing recipient with Phase 9 data
                existing.pickup_available = s["pickup_available"]
                existing.current_demand_portions = s["current_demand_portions"]
                existing.current_demand_kg = s["current_demand_kg"]
                existing.storage_capabilities = s["storage_capabilities"]
                existing.verification_status = s["verification_status"]
                existing.reliability_score = s["reliability_score"]
                existing.operating_hours_description = s["operating_hours_description"]
                existing.latitude = s["latitude"]
                existing.longitude = s["longitude"]
                
                # Check requirement
                req = db.query(RecipientRequirement).filter(RecipientRequirement.recipient_id == existing.id).first()
                if not req:
                    req = RecipientRequirement(
                        recipient_id=existing.id,
                        acceptable_categories=s["categories"],
                        dietary_preferences=s["dietary"],
                        required_storage_temp="ANY",
                        min_portions_per_drop=10,
                        max_delivery_distance_km=25.0
                    )
                    db.add(req)
                else:
                    req.acceptable_categories = s["categories"]
                    req.dietary_preferences = s["dietary"]
                print(f"Updated recipient: {existing.name}")

        db.commit()
        print("Phase 9 seed data successfully committed!")
    except Exception as e:
        db.rollback()
        print(f"Error during seed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_migration()
