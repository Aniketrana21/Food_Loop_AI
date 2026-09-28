import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

logger = logging.getLogger("foodloop.database")

# Attempt primary connection (Supabase PostgreSQL), fallback to SQLite if offline
db_url = settings.DATABASE_URL
engine = None

def _create_db_engine(url: str):
    if url.startswith("sqlite"):
        return create_engine(
            url,
            connect_args={"check_same_thread": False}
        )
    else:
        # PostgreSQL / Supabase connection with pool resilience
        return create_engine(
            url,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
            pool_recycle=300,
            connect_args={"connect_timeout": 5}
        )

try:
    test_engine = _create_db_engine(db_url)
    with test_engine.connect() as conn:
        pass
    engine = test_engine
    logger.info(f"Successfully connected to primary database (Dialect: {engine.dialect.name}).")
except Exception as e:
    logger.warning(f"Could not connect directly to primary database ({db_url}): {e}. Falling back to SQLite.")
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
