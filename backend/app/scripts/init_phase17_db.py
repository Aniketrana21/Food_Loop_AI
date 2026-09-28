import sys
import logging
from sqlalchemy import text
from app.core.database import engine, Base
from app.models.models import (
    NotificationPreference,
    NotificationTemplate,
    NotificationEvent,
    Notification
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("init_phase17")

def init_db():
    logger.info("Initializing Phase 17 Notification tables...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Base.metadata.create_all executed successfully.")
    except Exception as e:
        logger.error(f"Error in create_all: {e}")

    # Also run ALTER TABLE on notifications to ensure event_id column exists
    try:
        with engine.connect() as conn:
            if engine.dialect.name == "postgresql":
                conn.execute(text("""
                    ALTER TABLE notifications 
                    ADD COLUMN IF NOT EXISTS event_id VARCHAR(36) REFERENCES notification_events(id) ON DELETE SET NULL;
                """))
                conn.commit()
                logger.info("PostgreSQL notifications.event_id column verified.")
    except Exception as e:
        logger.warning(f"Note on notifications event_id alter: {e}")

    logger.info("Phase 17 DB initialization complete.")

if __name__ == "__main__":
    init_db()
