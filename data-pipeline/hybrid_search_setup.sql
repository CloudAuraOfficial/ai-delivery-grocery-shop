-- Hybrid retrieval support for the AI service.
-- Run once after EF migrations have created the Products table.
-- Idempotent — safe to re-run.

CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Trigram index on Name for fuzzy "did you mean" matches.
CREATE INDEX IF NOT EXISTS ix_products_name_trgm
    ON "Products" USING gin ("Name" gin_trgm_ops);

-- Full-text-search index covering Name, Description, Tags.
-- Used by ai-service/app/services/retriever.py::_keyword_search_products.
CREATE INDEX IF NOT EXISTS ix_products_fts
    ON "Products" USING gin (
        to_tsvector(
            'english',
            "Name" || ' ' || coalesce("Description", '') || ' ' || coalesce("Tags", '')
        )
    );
