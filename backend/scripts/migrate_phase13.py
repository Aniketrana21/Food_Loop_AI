"""
FoodLoop AI - Phase 13 Database Migration Script
Creates vision_scans table for food detection, classification, confidence logging,
and human-in-the-loop verification history.
"""
from sqlalchemy import text
from app.core.database import engine

def migrate_phase13():
    with engine.begin() as conn:
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS vision_scans (
            id VARCHAR(36) PRIMARY KEY,
            organization_id VARCHAR(36) REFERENCES organizations(id) ON DELETE SET NULL,
            kitchen_id VARCHAR(36) REFERENCES kitchens(id) ON DELETE SET NULL,
            user_id VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL,
            image_url TEXT NOT NULL,
            prediction VARCHAR(50) NOT NULL,
            confidence FLOAT NOT NULL,
            confidence_tier VARCHAR(20) NOT NULL,
            requires_manual_confirmation BOOLEAN DEFAULT TRUE NOT NULL,
            is_confirmed BOOLEAN DEFAULT FALSE NOT NULL,
            corrected_label VARCHAR(50),
            detected_bounding_box JSONB DEFAULT '{}'::jsonb,
            top_candidates JSONB DEFAULT '[]'::jsonb,
            preprocessing_metadata JSONB DEFAULT '{}'::jsonb,
            created_record_type VARCHAR(50),
            created_record_id VARCHAR(36),
            notes TEXT,
            created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
            confirmed_at TIMESTAMP WITHOUT TIME ZONE
        );

        CREATE INDEX IF NOT EXISTS idx_vision_org ON vision_scans(organization_id);
        CREATE INDEX IF NOT EXISTS idx_vision_prediction ON vision_scans(prediction);
        CREATE INDEX IF NOT EXISTS idx_vision_created_at ON vision_scans(created_at);
        """))
    print("Phase 13 vision_scans table created successfully!")

if __name__ == "__main__":
    migrate_phase13()
