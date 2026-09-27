"""
FoodLoop AI - Enterprise FastAPI Application
Modular architecture with centralized error handling, structured logging, RBAC, and OpenAPI v3 docs.
"""
import time
import logging
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import engine, Base, SessionLocal, get_db

# Middleware & Exception Handlers
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.logging_middleware import StructuredLoggingMiddleware
from app.middleware.exception_handler import register_exception_handlers

# Enterprise API Routers (All 24 Phase 3 Modules)
from app.api.v1.auth import router as auth_router
from app.api.v1.organizations import router as organizations_router
from app.api.v1.kitchens import router as kitchens_router
from app.api.v1.processing import router as processing_router
from app.api.v1.menus import router as menus_router
from app.api.v1.inventory import router as inventory_router
from app.api.v1.production import router as production_router
from app.api.v1.consumption import router as consumption_router
from app.api.v1.waste import router as waste_router
from app.api.v1.forecast import router as forecast_router
from app.api.v1.optimization import router as optimization_router
from app.api.v1.surplus import router as surplus_router
from app.api.v1.recipients import router as recipients_router
from app.api.v1.matching import router as matching_router
from app.api.v1.donations import router as donations_router
from app.api.v1.logistics import router as logistics_router
from app.api.v1.routes import router as routes_router
from app.api.v1.deliveries import router as deliveries_router
from app.api.v1.qr import router as qr_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.assistant import router as assistant_router
from app.api.v1.documents import router as documents_router
from app.api.v1.admin import router as admin_router
from app.api.v1.vision import router as vision_router

# Legacy Routers for Backward Compatibility
from app.api.v1.listings import router as listings_router
from app.api.v1.claims import router as claims_router
from app.api.v1.dispatch import router as dispatch_router
from app.api.v1.ml_routes import router as ml_router
from app.api.v1.rag_routes import router as rag_router
from app.api.v1.impact import router as impact_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
)
logger = logging.getLogger("foodloop")
APP_START_TIME = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager: verifies database connectivity on startup."""
    try:
        # Create tables if not existing (e.g. SQLite test engine)
        Base.metadata.create_all(bind=engine)
        logger.info(f"[FoodLoop AI] Database connected successfully (Dialect: {engine.dialect.name})")
    except Exception as e:
        logger.warning(f"[FoodLoop AI] Startup database initialization check: {e}")
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "FoodLoop AI Enterprise Backend API: Smart Food Reduction & Sustainable Redistribution "
        "Ecosystem for Institutional Kitchens, Food Processing Units, and Charitable Networks."
    ),
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# 1. Register Global Exception Handlers
register_exception_handlers(app)

# 2. Add Middlewares (RequestID -> StructuredLogging -> CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(StructuredLoggingMiddleware)
app.add_middleware(RequestIDMiddleware)

# 3. Mount All 24 Enterprise API Modules
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(organizations_router, prefix=settings.API_V1_STR)
app.include_router(kitchens_router, prefix=settings.API_V1_STR)
app.include_router(processing_router, prefix=settings.API_V1_STR)
app.include_router(menus_router, prefix=settings.API_V1_STR)
app.include_router(inventory_router, prefix=settings.API_V1_STR)
app.include_router(production_router, prefix=settings.API_V1_STR)
app.include_router(consumption_router, prefix=settings.API_V1_STR)
app.include_router(waste_router, prefix=settings.API_V1_STR)
app.include_router(forecast_router, prefix=settings.API_V1_STR)
app.include_router(optimization_router, prefix=settings.API_V1_STR)
app.include_router(surplus_router, prefix=settings.API_V1_STR)
app.include_router(recipients_router, prefix=settings.API_V1_STR)
app.include_router(matching_router, prefix=settings.API_V1_STR)
app.include_router(donations_router, prefix=settings.API_V1_STR)
app.include_router(logistics_router, prefix=settings.API_V1_STR)
app.include_router(routes_router, prefix=settings.API_V1_STR)
app.include_router(deliveries_router, prefix=settings.API_V1_STR)
app.include_router(qr_router, prefix=settings.API_V1_STR)
app.include_router(notifications_router, prefix=settings.API_V1_STR)
app.include_router(analytics_router, prefix=settings.API_V1_STR)
app.include_router(assistant_router, prefix=settings.API_V1_STR)
app.include_router(documents_router, prefix=settings.API_V1_STR)
app.include_router(admin_router, prefix=settings.API_V1_STR)
app.include_router(vision_router, prefix=settings.API_V1_STR)

# 4. Mount Legacy Compatibility Routers
app.include_router(listings_router, prefix=settings.API_V1_STR)
app.include_router(claims_router, prefix=settings.API_V1_STR)
app.include_router(dispatch_router, prefix=settings.API_V1_STR)
app.include_router(ml_router, prefix=settings.API_V1_STR)
app.include_router(rag_router, prefix=settings.API_V1_STR)
app.include_router(impact_router, prefix=settings.API_V1_STR)


# =====================================================================
# SYSTEM & HEALTH ENDPOINTS
# =====================================================================
@app.get("/", tags=["System"])
def root():
    """Returns platform status, version, and active documentation links."""
    return {
        "service": "FoodLoop AI Enterprise API",
        "status": "operational",
        "version": "2.0.0",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "openapi_spec": "/openapi.json"
    }


@app.get("/health", tags=["System"])
def health_check():
    """Liveness probe for orchestrators (Kubernetes / Cloud Run)."""
    return {
        "status": "healthy",
        "service": "foodloop-backend",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.get("/ready", tags=["System"])
def readiness_check(db: Session = Depends(get_db)):
    """Readiness probe checking database connectivity and operational state."""
    try:
        db.execute(text("SELECT 1"))
        return {
            "status": "ready",
            "database": "connected",
            "dialect": engine.dialect.name,
            "uptime_seconds": round(time.time() - APP_START_TIME, 1)
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return {
            "status": "not_ready",
            "database": "disconnected",
            "error": str(e)
        }
