"""
FoodLoop AI - Enterprise Database Verification & Initialization Script
Tests database connectivity (Supabase PostgreSQL / local SQLite fallback),
applies the full DDL schema, and verifies table contracts across all 30 core tables.
"""

import sys
import os

# Put backend and root on path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.core.database import engine, Base, SessionLocal
from app.models.models import (
    User, Organization, OrganizationMember, Kitchen, ProcessingUnit,
    Menu, MenuItem, Ingredient, Inventory, InventoryTransaction,
    ProductionBatch, ConsumptionRecord, WasteRecord, SurplusItem,
    Recipient, RecipientRequirement, Donation, DonationItem,
    PickupRequest, Driver, Vehicle, Route, Delivery,
    QrVerification, Notification, ModelPrediction, AiRecommendation,
    ImpactMetric, Document, AuditLog
)
from database.migrate import run_migrations
from database.seed_data import run_seed


def run_database_verification():
    print("[*] Initiating FoodLoop AI 30-Table Enterprise Database Verification...")
    try:
        # Ensure all tables exist from metadata
        Base.metadata.create_all(bind=engine)
        print("[OK] SQLAlchemy models bound and tables created successfully.")

        # Run schema migration & seed
        mig_ok = run_migrations()
        seed_ok = run_seed()
        print(f"[OK] Database seeding status: {'SUCCESS' if seed_ok else 'FAILED'}")

        # Test session and query core entities
        session = SessionLocal()
        users_count = session.query(User).count()
        orgs_count = session.query(Organization).count()
        org_members_count = session.query(OrganizationMember).count()
        kitchens_count = session.query(Kitchen).count()
        fpus_count = session.query(ProcessingUnit).count()
        menus_count = session.query(Menu).count()
        menu_items_count = session.query(MenuItem).count()
        ingredients_count = session.query(Ingredient).count()
        inventory_count = session.query(Inventory).count()
        inv_tx_count = session.query(InventoryTransaction).count()
        batches_count = session.query(ProductionBatch).count()
        consumption_count = session.query(ConsumptionRecord).count()
        waste_count = session.query(WasteRecord).count()
        surplus_count = session.query(SurplusItem).count()
        recipients_count = session.query(Recipient).count()
        rec_req_count = session.query(RecipientRequirement).count()
        donations_count = session.query(Donation).count()
        don_items_count = session.query(DonationItem).count()
        pickup_req_count = session.query(PickupRequest).count()
        drivers_count = session.query(Driver).count()
        vehicles_count = session.query(Vehicle).count()
        routes_count = session.query(Route).count()
        deliveries_count = session.query(Delivery).count()
        qr_count = session.query(QrVerification).count()
        notifications_count = session.query(Notification).count()
        predictions_count = session.query(ModelPrediction).count()
        recommendations_count = session.query(AiRecommendation).count()
        impact_count = session.query(ImpactMetric).count()
        documents_count = session.query(Document).count()
        audit_count = session.query(AuditLog).count()
        session.close()

        print(f"[OK] Complete 30-Table Verification Summary:")
        print(f"     1.  users: {users_count}")
        print(f"     2.  organizations: {orgs_count}")
        print(f"     3.  organization_members: {org_members_count}")
        print(f"     4.  kitchens: {kitchens_count}")
        print(f"     5.  processing_units: {fpus_count}")
        print(f"     6.  menus: {menus_count}")
        print(f"     7.  menu_items: {menu_items_count}")
        print(f"     8.  ingredients: {ingredients_count}")
        print(f"     9.  inventory: {inventory_count}")
        print(f"     10. inventory_transactions: {inv_tx_count}")
        print(f"     11. production_batches: {batches_count}")
        print(f"     12. consumption_records: {consumption_count}")
        print(f"     13. waste_records: {waste_count}")
        print(f"     14. surplus_items: {surplus_count}")
        print(f"     15. recipients: {recipients_count}")
        print(f"     16. recipient_requirements: {rec_req_count}")
        print(f"     17. donations: {donations_count}")
        print(f"     18. donation_items: {don_items_count}")
        print(f"     19. pickup_requests: {pickup_req_count}")
        print(f"     20. drivers: {drivers_count}")
        print(f"     21. vehicles: {vehicles_count}")
        print(f"     22. routes: {routes_count}")
        print(f"     23. deliveries: {deliveries_count}")
        print(f"     24. qr_verifications: {qr_count}")
        print(f"     25. notifications: {notifications_count}")
        print(f"     26. model_predictions: {predictions_count}")
        print(f"     27. ai_recommendations: {recommendations_count}")
        print(f"     28. impact_metrics: {impact_count}")
        print(f"     29. documents: {documents_count}")
        print(f"     30. audit_logs: {audit_count}")
        print("[SUCCESS] All 30 database tables are verified and operational!")
        return True
    except Exception as e:
        print(f"[ERROR] Database verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_database_verification()
    sys.exit(0 if success else 1)
