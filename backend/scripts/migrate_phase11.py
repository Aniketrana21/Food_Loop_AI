"""
Phase 11 - QR Chain of Custody Migration Script
Adds immutable_donation_id to donations, creates donation_custody_events and donation_qr_tokens tables.
"""
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv("backend/.env")

conn = psycopg2.connect(os.getenv("DATABASE_URL"))
cur = conn.cursor()

# 1. Add immutable_donation_id to donations if not exists
cur.execute("""
ALTER TABLE donations 
ADD COLUMN IF NOT EXISTS immutable_donation_id VARCHAR(64) UNIQUE;
""")

# Backfill immutable_donation_id for existing rows
cur.execute("""
UPDATE donations 
SET immutable_donation_id = 'DON-' || UPPER(SUBSTRING(COALESCE(tracking_number, id) FROM 1 FOR 8))
WHERE immutable_donation_id IS NULL;
""")

# 2. Create donation_custody_events table
cur.execute("""
CREATE TABLE IF NOT EXISTS donation_custody_events (
    id VARCHAR(36) PRIMARY KEY,
    donation_id VARCHAR(36) NOT NULL REFERENCES donations(id) ON DELETE CASCADE,
    event VARCHAR(100) NOT NULL,
    from_status VARCHAR(50) NOT NULL,
    to_status VARCHAR(50) NOT NULL,
    user_id VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL,
    user_name VARCHAR(150),
    role VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    token_nonce VARCHAR(64),
    proof_type VARCHAR(50),
    verified_temp_c DOUBLE PRECISION,
    verified_lat DOUBLE PRECISION,
    verified_lng DOUBLE PRECISION,
    signature_data TEXT,
    proof_image_url TEXT,
    notes TEXT,
    proof_metadata JSONB DEFAULT '{}'::jsonb,
    previous_hash VARCHAR(64),
    integrity_hash VARCHAR(64) NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_custody_events_donation ON donation_custody_events(donation_id);
CREATE INDEX IF NOT EXISTS idx_custody_events_timestamp ON donation_custody_events(timestamp);
""")

# 3. Create donation_qr_tokens table
cur.execute("""
CREATE TABLE IF NOT EXISTS donation_qr_tokens (
    id VARCHAR(36) PRIMARY KEY,
    donation_id VARCHAR(36) NOT NULL REFERENCES donations(id) ON DELETE CASCADE,
    stage VARCHAR(50) NOT NULL,
    nonce VARCHAR(64) UNIQUE NOT NULL,
    hmac_signature VARCHAR(128) NOT NULL,
    token_string TEXT NOT NULL,
    expires_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    is_burned BOOLEAN DEFAULT FALSE NOT NULL,
    burned_at TIMESTAMP WITHOUT TIME ZONE,
    burned_by_user_id VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_donation_qr_nonce ON donation_qr_tokens(nonce);
CREATE INDEX IF NOT EXISTS idx_donation_qr_donation ON donation_qr_tokens(donation_id);
""")

conn.commit()
print("Phase 11 migration successfully executed!")
cur.close()
conn.close()
