"""
Database module interface for FoodLoop AI.
Provides unified access to engine, Base, SessionLocal, and DB dependencies.
"""
from app.core.database import engine, Base, SessionLocal, get_db

__all__ = ["engine", "Base", "SessionLocal", "get_db"]
