"""
FoodLoop AI - Phase 12 Knowledge & Operational Data Seeder
Populates verified compliance documents, organization-specific internal policies,
and live operational records (waste, production, impact, surplus) for RAG assistant testing.
"""
import os
import math
import re
from datetime import datetime, date, timedelta, timezone
from dotenv import load_dotenv

load_dotenv("backend/.env")

from app.core.database import SessionLocal
from app.models.models import (
    Organization,
    Kitchen,
    Document,
    DocumentChunk,
    WasteRecord,
    ProductionBatch,
    SurplusItem,
    ImpactMetric,
    User
)

# Text chunker helper
def chunk_text(text: str, chunk_size: int = 300, overlap: int = 60):
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk_words = words[i:i + chunk_size]
        chunks.append(" ".join(chunk_words))
        if i + chunk_size >= len(words):
            break
        i += (chunk_size - overlap)
    return chunks if chunks else [text]

def compute_term_vector(text: str):
    words = re.findall(r"\w+", text.lower())
    vec = {}
    for w in words:
        if len(w) > 2:
            vec[w] = vec.get(w, 0.0) + 1.0
    norm = math.sqrt(sum(v * v for v in vec.values()))
    if norm > 0:
        for k in vec:
            vec[k] = round(vec[k] / norm, 4)
    return vec


def seed_phase12():
    db = SessionLocal()
    try:
        hyatt_org = db.query(Organization).filter(Organization.id == "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb").first()
        canning_org = db.query(Organization).filter(Organization.id == "cccccccc-cccc-cccc-cccc-cccccccccccc").first()
        kitchen = db.query(Kitchen).filter(Kitchen.organization_id == "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb").first()
        chef_user = db.query(User).first()

        hyatt_id = hyatt_org.id if hyatt_org else "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        canning_id = canning_org.id if canning_org else "cccccccc-cccc-cccc-cccc-cccccccccccc"
        kitchen_id = kitchen.id if kitchen else None
        chef_id = chef_user.id if chef_user else None

        print(f"Seeding with Hyatt Org: {hyatt_id}, Canning Org: {canning_id}, Kitchen: {kitchen_id}")

        # ---------------------------------------------------------
        # 1. SEED VERIFIED DOCUMENTS & CHUNKS
        # ---------------------------------------------------------
        documents_to_seed = [
            {
                "id": "doc-gov-fda-3501",
                "organization_id": None,
                "title": "FDA Food Code § 3-501: Temperature Danger Zone & 4-Hour Rule",
                "category": "FDA_FOOD_CODE",
                "document_type": "GOVERNMENT_GUIDELINE",
                "version": "2022.3",
                "access_level": "PUBLIC",
                "doc_date": date(2022, 12, 15),
                "source": "U.S. Food and Drug Administration (FDA) Food Code 2022",
                "is_public": True,
                "content": (
                    "FDA Food Code Section 3-501.16 & 3-501.19 establishes temperature safety boundaries for Time/Temperature "
                    "Control for Safety (TCS) foods. Bacterial pathogens including Salmonella, Clostridium perfringens, and "
                    "Staphylococcus aureus multiply rapidly within the Danger Zone of 4°C to 60°C (40°F to 140°F). "
                    "All hot TCS foods must be maintained at 60°C (140°F) or above. Cold foods must be held at 4°C (40°F) or below. "
                    "Under the 4-Hour Rule, food taken out of temperature control may be held for a maximum of 4 continuous hours "
                    "if marked with the exact time removed. Any food remaining unconsumed at the 4-hour mark must be discarded. "
                    "Two-stage cooling mandates cooling cooked foods from 60°C down to 21°C within 2 hours, and from 21°C down to 4°C "
                    "within an additional 4 hours (total 6 hours)."
                )
            },
            {
                "id": "doc-gov-good-samaritan",
                "organization_id": None,
                "title": "Bill Emerson Good Samaritan Food Donation Act (42 U.S. Code § 1791)",
                "category": "GOOD_SAMARITAN_ACT",
                "document_type": "GOVERNMENT_GUIDELINE",
                "version": "1996.1",
                "access_level": "PUBLIC",
                "doc_date": date(1996, 10, 1),
                "source": "USDA & Federal Register / 42 U.S. Code § 1791",
                "is_public": True,
                "content": (
                    "The Bill Emerson Good Samaritan Food Donation Act protects food donors, restaurants, retail grocers, "
                    "caterers, and recipient non-profit organizations from civil and criminal liability when donating wholesome food in good faith. "
                    "Liability protection applies even if donated food is not readily marketable due to cosmetic appearance, labeling, "
                    "or surplus volume. Protection is only forfeited in cases of gross negligence or intentional misconduct. "
                    "The 2023 Food Donation Improvement Act expanded coverage to include direct donations to needy individuals "
                    "and qualified social enterprises without an intermediate 501(c)(3) food bank."
                )
            },
            {
                "id": "doc-sop-haccp-donation",
                "organization_id": None,
                "title": "HACCP Standard Operating Procedure for Food Donation & Redistribution",
                "category": "HACCP_SOP",
                "document_type": "HACCP_SOP",
                "version": "2024.2",
                "access_level": "PUBLIC",
                "doc_date": date(2024, 3, 1),
                "source": "FoodLoop National HACCP Technical Advisory Panel",
                "is_public": True,
                "content": (
                    "All prepared food surplus intended for community redistribution must adhere to Critical Control Point (CCP) protocols. "
                    "CCP-1: Temperature Verification. Internal core temperature must be probed and logged in FoodLoop before packaging. "
                    "CCP-2: Rapid Blast Chilling. Cooked leftovers must reach below 4°C within 90 minutes if not kept at hot-holding (>60°C). "
                    "CCP-3: Allergen Labeling. Dishes containing Milk, Eggs, Fish, Crustacean Shellfish, Tree Nuts, Peanuts, Wheat, "
                    "Soybeans, or Sesame must display clear high-visibility allergen warnings. "
                    "CCP-4: Tamper-Evident Packaging. All food containers must be sealed with tamper-evident tape and date-time stamped."
                )
            },
            {
                "id": "doc-sop-cold-chain",
                "organization_id": None,
                "title": "Cold Chain & Transport Logistics Operating Standards",
                "category": "COLD_CHAIN_STANDARD",
                "document_type": "OPERATIONAL_MANUAL",
                "version": "2024.1",
                "access_level": "PUBLIC",
                "doc_date": date(2024, 2, 15),
                "source": "FoodLoop Global Logistics Standard Operating Manual",
                "is_public": True,
                "content": (
                    "Perishable cooked meals, chilled dairy, and raw produce must remain strictly at or below 4°C during courier transit. "
                    "Drivers and volunteer dispatchers must use certified food-grade insulated cambros or cooler boxes equipped with frozen gel packs. "
                    "Transit duration for unpowered passive cooler transport must not exceed 90 minutes. Digital Bluetooth probe checks "
                    "must be recorded in the FoodLoop driver application at pickup and upon delivery at the recipient shelter. "
                    "If transit temperature exceeds 8°C for more than 30 minutes, courier must reject handover and notify dispatch."
                )
            },
            {
                "id": "doc-bylaw-waste-diversion",
                "organization_id": None,
                "title": "Municipal Commercial Organic Waste Diversion & Composting Bylaw",
                "category": "MUNICIPAL_BYLAW",
                "document_type": "WASTE_MANAGEMENT_POLICY",
                "version": "2023.4",
                "access_level": "PUBLIC",
                "doc_date": date(2023, 11, 1),
                "source": "San Francisco Department of the Environment Regulation #100-09",
                "is_public": True,
                "content": (
                    "Commercial food establishments generating more than 1 cubic yard of solid waste per week must implement three-stream "
                    "source separation: Compostable Food Scraps, Recyclables, and Landfill Trash. Direct disposal of edible surplus into "
                    "landfill bins is strictly prohibited and subject to municipal fines up to $1,000 per violation. "
                    "Entities must follow the EPA Food Recovery Hierarchy: 1. Source Reduction, 2. Feed Hungry People (Donation), "
                    "3. Feed Animals, 4. Industrial Uses / Anaerobic Digestion, 5. Composting, 6. Landfill disposal as final resort."
                )
            },
            # --- Organization-Specific Private Documents ---
            {
                "id": "doc-hyatt-banquet-sop",
                "organization_id": hyatt_id,
                "title": "Grand Hyatt San Francisco: Culinary Internal SOP & Banquet Overproduction Policy",
                "category": "INSTITUTIONAL_POLICY",
                "document_type": "INSTITUTIONAL_POLICY",
                "version": "2024.3-HYATT",
                "access_level": "ORGANIZATION_INTERNAL",
                "doc_date": date(2024, 5, 10),
                "source": "Grand Hyatt Executive Chef Office & Sustainability Committee",
                "is_public": False,
                "content": (
                    "This internal SOP governs banquet overproduction management across Grand Hyatt San Francisco kitchens. "
                    "Production safety buffer is capped at a maximum of 8% above confirmed guest cover count for ballroom events. "
                    "All unserved hot buffet proteins (Braised Short Ribs, Salmon, Chicken Breast) must be removed to the blast chiller "
                    "at exactly 21:30 PM under Sous Chef supervision. Overproduction logs must be filed in the FoodLoop Kitchen station. "
                    "Donation pickup through St. Jude Food Bank must be scheduled via automated API dispatch before 22:15 PM nightly."
                )
            },
            {
                "id": "doc-canning-qc-protocol",
                "organization_id": canning_id,
                "title": "Bay Area Canning & Puree Plant: Industrial Batch Quality Control Protocol",
                "category": "OPERATIONAL_MANUAL",
                "document_type": "OPERATIONAL_MANUAL",
                "version": "2024.B2",
                "access_level": "CONFIDENTIAL",
                "doc_date": date(2024, 4, 18),
                "source": "Bay Area Canning Quality Assurance Directorate",
                "is_public": False,
                "content": (
                    "CONFIDENTIAL MANUFACTURING SPECIFICATION: High-acid vegetable and stone-fruit pureeing requires continuous "
                    "thermal processing at 88°C for 45 seconds to achieve 5-log microbial reduction. Brix sugar refraction must be maintained "
                    "between 14.5° and 16.0° Brix using refractometer station #3. Steam vacuum seals must demonstrate minimum 15 inHg pull. "
                    "Proprietary enzyme deactivation step requires rapid cooling to 35°C within 180 seconds. Non-compliant batches must be "
                    "diverted to industrial anaerobic bio-methane digestion."
                )
            }
        ]

        for d_spec in documents_to_seed:
            existing = db.query(Document).filter(Document.id == d_spec["id"]).first()
            if existing:
                existing.title = d_spec["title"]
                existing.category = d_spec["category"]
                existing.document_type = d_spec["document_type"]
                existing.document_version = d_spec["version"]
                existing.access_level = d_spec["access_level"]
                existing.doc_date = d_spec["doc_date"]
                existing.regulatory_source = d_spec["source"]
                existing.is_public = d_spec["is_public"]
                existing.content = d_spec["content"]
                existing.organization_id = d_spec["organization_id"]
                doc = existing
            else:
                doc = Document(
                    id=d_spec["id"],
                    organization_id=d_spec["organization_id"],
                    title=d_spec["title"],
                    category=d_spec["category"],
                    document_type=d_spec["document_type"],
                    document_version=d_spec["version"],
                    access_level=d_spec["access_level"],
                    doc_date=d_spec["doc_date"],
                    regulatory_source=d_spec["source"],
                    is_public=d_spec["is_public"],
                    content=d_spec["content"],
                )
                db.add(doc)
            db.flush()

            # Remove old chunks if any and regenerate
            db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).delete()
            chunks = chunk_text(doc.content, chunk_size=200, overlap=40)
            for idx, c_text in enumerate(chunks):
                chunk = DocumentChunk(
                    document_id=doc.id,
                    organization_id=doc.organization_id,
                    chunk_index=idx,
                    content=c_text,
                    token_count=len(c_text.split()),
                    chunk_metadata={
                        "organization": "Grand Hyatt SF" if doc.organization_id == hyatt_id else ("Bay Area Canning" if doc.organization_id == canning_id else "Global / Public"),
                        "document_type": doc.document_type,
                        "version": doc.document_version,
                        "date": str(doc.doc_date),
                        "access_level": doc.access_level,
                        "source": doc.regulatory_source,
                        "title": doc.title,
                        "chunk_index": idx,
                        "total_chunks": len(chunks)
                    },
                    embedding_vector=compute_term_vector(f"{doc.title} {c_text} {doc.document_type} {doc.regulatory_source}")
                )
                db.add(chunk)

        # ---------------------------------------------------------
        # 2. SEED REALISTIC OPERATIONAL DATA (Waste Records, Production, Impact)
        # ---------------------------------------------------------
        now = datetime.now(timezone.utc)

        # Create Kitchen if none
        if not kitchen_id:
            new_kitchen = Kitchen(
                organization_id=hyatt_id,
                name="Grand Ballroom Main Commercial Kitchen",
                location="Level B1, Grand Hyatt SF",
                capacity=800
            )
            db.add(new_kitchen)
            db.flush()
            kitchen_id = new_kitchen.id

        # Clean old test waste records for Grand Hyatt to ensure clean baseline
        db.query(WasteRecord).filter(WasteRecord.organization_id == hyatt_id).delete()

        # Seed 14 days of realistic waste records:
        # Week 1 (7-14 days ago): baseline waste total ~62 kg
        # Week 2 (0-7 days ago): increased waste total ~84.5 kg (+36.3% increase!)
        # Key drivers: Banquet Overproduction (+18.5 kg), Friday dinner attendance drops, preparation waste on meats
        waste_items_seed = [
            # Current week (0 to 6 days ago)
            {"food": "Steamed Jasmine Rice", "category": "OVERPRODUCTION", "kg": 22.5, "cost": 45.0, "co2": 56.2, "days_ago": 1, "cause": "Banquet buffet overproduction; actual attendance was 15% below planned guest count"},
            {"food": "Braised Beef Short Ribs", "category": "OVERPRODUCTION", "kg": 16.0, "cost": 192.0, "co2": 432.0, "days_ago": 2, "cause": "Corporate dinner party over-ordering; guest count dropped by 32 covers at the last minute"},
            {"food": "Roasted Root Vegetables", "category": "PREPARATION_WASTE", "kg": 12.0, "cost": 28.8, "co2": 18.0, "days_ago": 3, "cause": "Trimming and peeling excess on bulk prep station for banquet service"},
            {"food": "Mixed Field Greens Salad", "category": "SPOILAGE", "kg": 8.5, "cost": 34.0, "co2": 12.7, "days_ago": 4, "cause": "Walk-in cooler humidity fluctuation caused premature wilting"},
            {"food": "Steamed Jasmine Rice", "category": "OVERPRODUCTION", "kg": 16.0, "cost": 32.0, "co2": 40.0, "days_ago": 5, "cause": "Excess batch cooked during Friday lunch rush; demand did not materialize"},
            {"food": "Herb Roasted Chicken Breast", "category": "PLATE_WASTE", "kg": 9.5, "cost": 57.0, "co2": 66.5, "days_ago": 6, "cause": "Portion size variance on banquet plated dinner (over-portioned by 25%)"},

            # Previous week (7 to 13 days ago) - Lower baseline
            {"food": "Steamed Jasmine Rice", "category": "OVERPRODUCTION", "kg": 14.0, "cost": 28.0, "co2": 35.0, "days_ago": 8, "cause": "Standard shift surplus, redirected partially to staff cafeteria"},
            {"food": "Roasted Root Vegetables", "category": "PREPARATION_WASTE", "kg": 11.0, "cost": 26.4, "co2": 16.5, "days_ago": 9, "cause": "Routine vegetable prep trimming"},
            {"food": "Herb Roasted Chicken Breast", "category": "OVERPRODUCTION", "kg": 12.0, "cost": 72.0, "co2": 84.0, "days_ago": 10, "cause": "Modest overproduction for weekend banquet"},
            {"food": "Mixed Field Greens Salad", "category": "PLATE_WASTE", "kg": 7.0, "cost": 28.0, "co2": 10.5, "days_ago": 11, "cause": "Standard banquet table clearance"},
            {"food": "Artisan Bread Rolls", "category": "OVERPRODUCTION", "kg": 8.0, "cost": 16.0, "co2": 12.0, "days_ago": 12, "cause": "Bakery surplus past 24hr freshness window"},
            {"food": "Steamed Broccoli Florets", "category": "SPOILAGE", "kg": 10.0, "cost": 22.0, "co2": 15.0, "days_ago": 13, "cause": "Delivery crate with partial bruising"}
        ]

        for w in waste_items_seed:
            rec_date = now - timedelta(days=w["days_ago"])
            w_rec = WasteRecord(
                kitchen_id=kitchen_id,
                organization_id=hyatt_id,
                food_item=w["food"],
                unit="kg",
                waste_category=w["category"],
                weight_kg=w["kg"],
                cost_loss_usd=w["cost"],
                ghg_co2e_kg=w["co2"],
                root_cause=w["cause"],
                department="MAIN_KITCHEN",
                recorded_at=rec_date,
                created_at=rec_date
            )
            db.add(w_rec)

        # Seed Production Batches with planned vs actual variance
        db.query(ProductionBatch).filter(ProductionBatch.kitchen_id == kitchen_id).delete()
        batches_seed = [
            {"num": "BATCH-2024-0925-A", "planned": 300.0, "actual": 360.0, "station": "HOT_LINE", "haccp": True, "status": "COMPLETED", "days_ago": 1},
            {"num": "BATCH-2024-0924-B", "planned": 200.0, "actual": 250.0, "station": "BANQUET_GRILL", "haccp": True, "status": "COMPLETED", "days_ago": 2},
            {"num": "BATCH-2024-0926-C", "planned": 400.0, "actual": 420.0, "station": "ROAST_STATION", "haccp": True, "status": "COMPLETED", "days_ago": 0},
        ]
        for b in batches_seed:
            b_date = now - timedelta(days=b["days_ago"])
            batch = ProductionBatch(
                kitchen_id=kitchen_id,
                batch_number=b["num"],
                planned_quantity=b["planned"],
                actual_prepared_quantity=b["actual"],
                unit="portions",
                station=b["station"],
                target_temp_c=65.0,
                current_temp_c=66.5,
                haccp_compliant=b["haccp"],
                status=b["status"],
                chef_user_id=chef_id,
                started_at=b_date - timedelta(hours=3),
                completed_at=b_date,
                created_at=b_date
            )
            db.add(batch)

        # Seed Urgent Surplus Items
        urgent_surplus = db.query(SurplusItem).filter(
            SurplusItem.organization_id == hyatt_id,
            SurplusItem.status.in_(["AVAILABLE", "RESERVED", "DECLARED"])
        ).first()

        if not urgent_surplus:
            urgent_surplus = SurplusItem(
                organization_id=hyatt_id,
                kitchen_id=kitchen_id,
                food="Chef's Herb Roasted Salmon & Asparagus Medley",
                title="Pan-Seared Pacific Salmon Filets (45 Portions)",
                description="Freshly blast-chilled roasted salmon with lemon herb butter and grilled asparagus.",
                category="COOKED_MEALS",
                quantity=18.5,
                quantity_kg=18.5,
                portions=45,
                unit="kg",
                storage_type="REFRIGERATED",
                storage_temp="REFRIGERATED",
                temperature=3.5,
                remaining_safe_window_minutes=75.0,
                urgency="CRITICAL_IMMEDIATE",
                urgency_tier="CRITICAL_IMMEDIATE",
                eligibility="ELIGIBLE_FOR_DONATION",
                required_action="Schedule immediate courier dispatch within 75 minutes to maintain cold chain.",
                status="AVAILABLE",
                pickup_address="345 Stockton St, San Francisco, CA 94108 (Grand Hyatt Loading Bay B)",
                pickup_lat=37.7892,
                pickup_lng=-122.4068,
                best_use_before=now + timedelta(minutes=75),
                created_at=now - timedelta(minutes=45)
            )
            db.add(urgent_surplus)
        else:
            urgent_surplus.remaining_safe_window_minutes = 75.0
            urgent_surplus.urgency = "CRITICAL_IMMEDIATE"
            urgent_surplus.urgency_tier = "CRITICAL_IMMEDIATE"
            urgent_surplus.status = "AVAILABLE"
            urgent_surplus.required_action = "Schedule immediate courier dispatch within 75 minutes to maintain cold chain."

        # Seed Monthly Impact Metrics
        db.query(ImpactMetric).filter(ImpactMetric.organization_id == hyatt_id).delete()
        impact = ImpactMetric(
            organization_id=hyatt_id,
            food_diverted_kg=685.0,
            meals_provided=1420,
            co2e_avoided_kg=1712.5,
            water_saved_liters=42500.0,
            financial_value_usd=4795.0,
            calculation_methodology="EPA_WARM_V15_COMMERCIAL",
            recorded_at=now,
            created_at=now
        )
        db.add(impact)

        db.commit()
        print("Phase 12 seed completed successfully!")
        print(f"Verified documents: {db.query(Document).count()}, Chunks: {db.query(DocumentChunk).count()}")
        print(f"Waste records for Hyatt: {db.query(WasteRecord).filter(WasteRecord.organization_id == hyatt_id).count()}")

    except Exception as e:
        db.rollback()
        print(f"Error during Phase 12 seeding: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_phase12()
