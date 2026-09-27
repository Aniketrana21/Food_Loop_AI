"""
Migration script to add Phase 8 columns to SQLite surplus_items table if not present.
"""
from app.core.database import engine
from sqlalchemy import text, inspect

def run_migration():
    inspector = inspect(engine)
    if "surplus_items" not in inspector.get_table_names():
        print("Table surplus_items does not exist yet. Will be auto-created by SQLAlchemy.")
        return

    columns = [c['name'] for c in inspector.get_columns('surplus_items')]
    print(f"Existing columns count: {len(columns)}")

    new_cols = [
        ('food', 'VARCHAR(255)'),
        ('quantity', 'FLOAT'),
        ('unit', 'VARCHAR(50)'),
        ('storage_type', 'VARCHAR(50)'),
        ('temperature', 'FLOAT'),
        ('batch', 'VARCHAR(100)'),
        ('best_use_before', 'TIMESTAMP'),
        ('notes', 'TEXT'),
        ('image', 'TEXT'),
        ('remaining_safe_window_minutes', 'FLOAT'),
        ('urgency', 'VARCHAR(50)'),
        ('eligibility', 'VARCHAR(50)'),
        ('required_action', 'VARCHAR(255)'),
        ('suggested_waste_workflow', 'VARCHAR(100)'),
        ('approved_by', 'VARCHAR(100)'),
        ('approval_status', 'VARCHAR(50)'),
        ('approval_notes', 'TEXT'),
        ('location_name', 'VARCHAR(255)')
    ]

    with engine.connect() as conn:
        for col, col_type in new_cols:
            if col not in columns:
                print(f"Adding column '{col}'...")
                conn.execute(text(f"ALTER TABLE surplus_items ADD COLUMN {col} {col_type}"))
        conn.commit()
    print("Phase 8 SQLite migration completed successfully!")

if __name__ == "__main__":
    run_migration()
