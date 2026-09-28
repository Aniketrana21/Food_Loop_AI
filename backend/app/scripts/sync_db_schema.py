import sys
import logging
from sqlalchemy import text
from app.core.database import engine, Base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sync_db_schema")

def sync_schema():
    logger.info(f"Connecting to database: dialect = {engine.dialect.name}")

    if engine.dialect.name == "postgresql":
        with engine.connect() as conn:
            # 1. surplus_items fpu_batch_id
            try:
                conn.execute(text("""
                    ALTER TABLE surplus_items 
                    ADD COLUMN IF NOT EXISTS fpu_batch_id VARCHAR(36) REFERENCES fpu_production_batches(id) ON DELETE SET NULL;
                """))
                conn.commit()
                logger.info("Added surplus_items.fpu_batch_id successfully.")
            except Exception as e:
                logger.warning(f"Error adding fpu_batch_id to surplus_items: {e}")

            # 2. Check organizations is_active
            try:
                conn.execute(text("""
                    ALTER TABLE organizations 
                    ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
                """))
                conn.commit()
                logger.info("Verified organizations.is_active.")
            except Exception as e:
                logger.warning(f"Error on organizations.is_active: {e}")

            # 3. Check notifications event_id
            try:
                conn.execute(text("""
                    ALTER TABLE notifications 
                    ADD COLUMN IF NOT EXISTS event_id VARCHAR(36) REFERENCES notification_events(id) ON DELETE SET NULL;
                """))
                conn.commit()
                logger.info("Verified notifications.event_id.")
            except Exception as e:
                logger.warning(f"Error on notifications.event_id: {e}")

            # 4. Check fpu_inventory items and production batches
            try:
                conn.execute(text("""
                    ALTER TABLE fpu_raw_materials
                    ADD COLUMN IF NOT EXISTS notes TEXT;
                """))
                conn.commit()
            except Exception as e:
                logger.warning(f"Error on fpu_raw_materials: {e}")

    # Ensure all tables exist
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Base.metadata.create_all executed cleanly.")
    except Exception as e:
        logger.error(f"Error in create_all: {e}")

    logger.info("Schema synchronization complete.")

if __name__ == "__main__":
    sync_schema()
