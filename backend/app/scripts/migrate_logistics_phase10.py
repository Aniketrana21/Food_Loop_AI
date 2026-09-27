"""
FoodLoop AI - Phase 10 Logistics & Fleet Migration Script
Adds columns to deliveries table and seeds realistic delivery missions and couriers.
"""
from sqlalchemy import text, inspect
from app.core.database import engine, SessionLocal
from app.models.models import Delivery, Vehicle, Driver, Organization, User
from datetime import datetime, timezone, timedelta
import uuid


def run_migration():
    inspector = inspect(engine)

    if "deliveries" in inspector.get_table_names():
        deliv_cols = [c['name'] for c in inspector.get_columns('deliveries')]
        new_cols = [
            ('vehicle_id', 'VARCHAR(36)'),
            ('surplus_item_id', 'VARCHAR(36)'),
            ('pickup_address', 'TEXT'),
            ('pickup_lat', 'FLOAT'),
            ('pickup_lng', 'FLOAT'),
            ('delivery_address', 'TEXT'),
            ('delivery_lat', 'FLOAT'),
            ('delivery_lng', 'FLOAT'),
            ('food_title', 'VARCHAR(255)'),
            ('food_urgency', 'VARCHAR(50) DEFAULT \'MEDIUM\''),
            ('cargo_weight_kg', 'FLOAT DEFAULT 15.0'),
            ('scheduled_pickup_time', 'TIMESTAMP'),
            ('scheduled_delivery_time', 'TIMESTAMP'),
            ('estimated_arrival_time', 'TIMESTAMP'),
            ('proof_of_delivery_signature', 'TEXT'),
            ('proof_of_delivery_photo', 'TEXT'),
            ('proof_of_delivery_notes', 'TEXT'),
            ('proof_of_delivery_receiver_name', 'VARCHAR(255)'),
            ('proof_of_delivery_verified_at', 'TIMESTAMP'),
        ]

        with engine.connect() as conn:
            # Drop NOT NULL on donation_id if present
            try:
                conn.execute(text("ALTER TABLE deliveries ALTER COLUMN donation_id DROP NOT NULL"))
            except Exception as e:
                print(f"Notice dropping NOT NULL: {e}")

            for col, col_type in new_cols:
                if col not in deliv_cols:
                    print(f"Adding column '{col}' to deliveries...")
                    conn.execute(text(f"ALTER TABLE deliveries ADD COLUMN {col} {col_type}"))
            conn.commit()

    print("Phase 10 delivery columns verified successfully!")

    # Seed vehicles, drivers, and delivery assignments if needed
    db = SessionLocal()
    try:
        org = db.query(Organization).first()
        org_id = org.id if org else str(uuid.uuid4())

        # Seed additional vehicle: EV Cargo Van
        veh_ev = db.query(Vehicle).filter(Vehicle.license_plate == "EV-RESCUE-01").first()
        if not veh_ev:
            veh_ev = Vehicle(
                id="veh-ev-001",
                organization_id=org_id,
                license_plate="EV-RESCUE-01",
                vehicle_type="ELECTRIC_CARGO_VAN",
                payload_capacity_kg=350.0,
                active_cooling=True,
                current_compartment_temp_c=3.2,
                is_active=True
            )
            db.add(veh_ev)
            db.flush()
            print("Created Vehicle: EV-RESCUE-01")

        # Seed driver user & profile for Alex Mercer
        user_driver = db.query(User).filter(User.email == "alex.mercer@foodloop.org").first()
        if not user_driver:
            user_driver = User(
                id="usr-driver-alex",
                email="alex.mercer@foodloop.org",
                full_name="Alex Mercer",
                role="DRIVER",
                phone="+1-415-555-0922",
                is_active=True
            )
            db.add(user_driver)
            db.flush()

        driver_alex = db.query(Driver).filter(Driver.user_id == user_driver.id).first()
        if not driver_alex:
            driver_alex = Driver(
                id="drv-alex-001",
                user_id=user_driver.id,
                organization_id=org_id,
                license_number="CA-COMM-889102",
                driver_status="AVAILABLE",
                current_lat=37.7749,
                current_lng=-122.4194,
                vehicle_id=veh_ev.id
            )
            db.add(driver_alex)
            db.flush()
            print("Created Driver profile for Alex Mercer")

        # Seed today's active delivery missions
        now = datetime.now(timezone.utc)
        sample_deliveries = [
            {
                "id": "deliv-001-chicken",
                "food_title": "Rotisserie Herb Roasted Chicken & Potatoes",
                "cargo_weight_kg": 25.5,
                "food_urgency": "HIGH",
                "status": "ASSIGNED",
                "pickup_address": "Main Production Kitchen, 100 Culinary Way, SF",
                "pickup_lat": 37.7749,
                "pickup_lng": -122.4194,
                "delivery_address": "Downtown St. Jude Food Bank, 450 4th Street, SF",
                "delivery_lat": 37.7812,
                "delivery_lng": -122.3987,
                "scheduled_pickup_time": now + timedelta(minutes=15),
                "scheduled_delivery_time": now + timedelta(minutes=60),
                "estimated_arrival_time": now + timedelta(minutes=35),
                "distance_km": 3.2,
                "transit_time_mins": 14.0,
                "stop_sequence": 1
            },
            {
                "id": "deliv-002-soup",
                "food_title": "Creamy Wild Mushroom & Barley Bisque",
                "cargo_weight_kg": 18.0,
                "food_urgency": "CRITICAL",
                "status": "EN_ROUTE",
                "pickup_address": "Culinary Prep Station #4, 100 Culinary Way, SF",
                "pickup_lat": 37.7749,
                "pickup_lng": -122.4194,
                "delivery_address": "Harbor Light Community Dining, 1275 Mission Street, SF",
                "delivery_lat": 37.7765,
                "delivery_lng": -122.4140,
                "scheduled_pickup_time": now - timedelta(minutes=10),
                "scheduled_delivery_time": now + timedelta(minutes=30),
                "estimated_arrival_time": now + timedelta(minutes=15),
                "distance_km": 1.8,
                "transit_time_mins": 9.0,
                "stop_sequence": 2
            },
            {
                "id": "deliv-003-bakery",
                "food_title": "Artisan Sourdough & Brioche Loaves",
                "cargo_weight_kg": 22.0,
                "food_urgency": "MEDIUM",
                "status": "DELIVERED",
                "pickup_address": "Golden Crust Bakery, 500 Market Street, SF",
                "pickup_lat": 37.7899,
                "pickup_lng": -122.4010,
                "delivery_address": "Hope Mission Family Shelter, 820 Folsom Street, SF",
                "delivery_lat": 37.7801,
                "delivery_lng": -122.4045,
                "scheduled_pickup_time": now - timedelta(hours=2),
                "scheduled_delivery_time": now - timedelta(hours=1),
                "estimated_arrival_time": now - timedelta(hours=1),
                "distance_km": 2.4,
                "transit_time_mins": 11.0,
                "stop_sequence": 3,
                "proof_of_delivery_receiver_name": "Marcus Vance",
                "proof_of_delivery_signature": "M. Vance [Digital Sig]",
                "proof_of_delivery_notes": "All 22kg loaves received in pristine condition",
                "proof_of_delivery_verified_at": now - timedelta(hours=1)
            }
        ]

        for s in sample_deliveries:
            existing = db.query(Delivery).filter(Delivery.id == s["id"]).first()
            if not existing:
                deliv = Delivery(
                    id=s["id"],
                    driver_id=driver_alex.id,
                    vehicle_id=veh_ev.id,
                    food_title=s["food_title"],
                    cargo_weight_kg=s["cargo_weight_kg"],
                    food_urgency=s["food_urgency"],
                    status=s["status"],
                    pickup_address=s["pickup_address"],
                    pickup_lat=s["pickup_lat"],
                    pickup_lng=s["pickup_lng"],
                    delivery_address=s["delivery_address"],
                    delivery_lat=s["delivery_lat"],
                    delivery_lng=s["delivery_lng"],
                    scheduled_pickup_time=s["scheduled_pickup_time"],
                    scheduled_delivery_time=s["scheduled_delivery_time"],
                    estimated_arrival_time=s["estimated_arrival_time"],
                    distance_km=s["distance_km"],
                    transit_time_mins=s["transit_time_mins"],
                    stop_sequence=s["stop_sequence"],
                    proof_of_delivery_receiver_name=s.get("proof_of_delivery_receiver_name"),
                    proof_of_delivery_signature=s.get("proof_of_delivery_signature"),
                    proof_of_delivery_notes=s.get("proof_of_delivery_notes"),
                    proof_of_delivery_verified_at=s.get("proof_of_delivery_verified_at")
                )
                db.add(deliv)
                print(f"Created delivery assignment: {s['food_title']}")

        db.commit()
        print("Phase 10 seed data successfully committed!")
    except Exception as e:
        db.rollback()
        print(f"Error seeding logistics: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_migration()
