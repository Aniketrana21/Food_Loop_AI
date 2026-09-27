import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

logger = logging.getLogger("foodloop.database")

# Attempt primary connection (Supabase PostgreSQL), fallback to SQLite if offline
db_url = settings.DATABASE_URL
engine = None

try:
    # Connect with 5-second timeout to avoid long hangs if remote DB is unreachable
    test_engine = create_engine(
        db_url,
        pool_pre_ping=True,
        connect_args={"connect_timeout": 5}
    )
    with test_engine.connect() as conn:
        pass
    engine = test_engine
    logger.info("Successfully connected to Supabase PostgreSQL database.")
except Exception as e:
    logger.warning(f"Could not connect directly to remote Postgres: {e}. Falling back to SQLite.")
    engine = create_engine(
        settings.FALLBACK_SQLITE_URL,
        connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
