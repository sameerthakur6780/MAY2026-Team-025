-- SmartBatch RAG schema for Supabase Postgres (requires pgvector extension)

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS rag_books (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pdf_hash TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    subject TEXT NOT NULL,
    grade INTEGER NOT NULL CHECK (grade >= 1 AND grade <= 12),
    resource_id INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS rag_parent_sections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    book_id UUID NOT NULL REFERENCES rag_books(id) ON DELETE CASCADE,
    chapter TEXT NOT NULL DEFAULT '',
    section TEXT NOT NULL DEFAULT '',
    page_range TEXT NOT NULL DEFAULT '',
    full_text TEXT NOT NULL,
    content_type TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS rag_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    book_id UUID NOT NULL REFERENCES rag_books(id) ON DELETE CASCADE,
    parent_section_id UUID NOT NULL REFERENCES rag_parent_sections(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding vector(768) NOT NULL,
    content_type TEXT NOT NULL,
    subject TEXT NOT NULL,
    grade INTEGER NOT NULL CHECK (grade >= 1 AND grade <= 12),
    chapter TEXT NOT NULL DEFAULT '',
    section TEXT NOT NULL DEFAULT '',
    page_range TEXT NOT NULL DEFAULT '',
    search_vector tsvector,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_rag_chunks_book_id ON rag_chunks(book_id);
CREATE INDEX IF NOT EXISTS idx_rag_chunks_subject_grade ON rag_chunks(subject, grade);
CREATE INDEX IF NOT EXISTS idx_rag_chunks_search_vector ON rag_chunks USING gin(search_vector);
CREATE INDEX IF NOT EXISTS idx_rag_chunks_embedding ON rag_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
