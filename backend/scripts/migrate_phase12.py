"""
FoodLoop AI - Phase 12 Database Migration Script
Creates document_chunks and rag_chat_messages tables,
and adds Phase 12 metadata columns (document_type, access_level, doc_date) to documents.
"""
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv("backend/.env")

conn = psycopg2.connect(os.getenv("DATABASE_URL"))
cur = conn.cursor()

# 1. Add Phase 12 metadata columns to documents table
cur.execute("""
ALTER TABLE documents 
ADD COLUMN IF NOT EXISTS document_type VARCHAR(100),
ADD COLUMN IF NOT EXISTS access_level VARCHAR(50) DEFAULT 'PUBLIC',
ADD COLUMN IF NOT EXISTS doc_date DATE;
""")

# Backfill existing documents
cur.execute("""
UPDATE documents 
SET document_type = COALESCE(category, 'GOVERNMENT_GUIDELINE'),
    access_level = CASE WHEN is_public THEN 'PUBLIC' ELSE 'ORGANIZATION_INTERNAL' END,
    doc_date = COALESCE(created_at::date, CURRENT_DATE)
WHERE document_type IS NULL;
""")

# 2. Create document_chunks table
cur.execute("""
CREATE TABLE IF NOT EXISTS document_chunks (
    id VARCHAR(36) PRIMARY KEY,
    document_id VARCHAR(36) NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    organization_id VARCHAR(36) REFERENCES organizations(id) ON DELETE SET NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    token_count INTEGER DEFAULT 0,
    chunk_metadata JSONB DEFAULT '{}'::jsonb,
    embedding_vector JSONB,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_chunks_document ON document_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_chunks_org ON document_chunks(organization_id);
""")

# 3. Create rag_chat_messages table for conversation history
cur.execute("""
CREATE TABLE IF NOT EXISTS rag_chat_messages (
    id VARCHAR(36) PRIMARY KEY,
    session_id VARCHAR(64) NOT NULL,
    user_id VARCHAR(36),
    organization_id VARCHAR(36),
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    sources JSONB DEFAULT '[]'::jsonb,
    data_context JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_chat_session ON rag_chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_created_at ON rag_chat_messages(created_at);
""")

conn.commit()
print("Phase 12 migration executed successfully!")
cur.close()
conn.close()
