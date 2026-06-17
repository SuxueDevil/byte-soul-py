-- ============================================================
-- PostgreSQL 建表脚本
-- ============================================================
-- 手动执行：psql -U user -d database -f pg.sql

CREATE TABLE IF NOT EXISTS bs_rag_chunks (
    id            BIGINT PRIMARY KEY,                  -- 雪花 ID，程序生成
    doc_hash      VARCHAR(64) NOT NULL,                -- 文档 MD5 哈希，按文档粒度操作
    file_name     VARCHAR(512),                        -- 原始文件名，前端展示用
    content       TEXT NOT NULL,                       -- 原文内容
    chunk_index   INTEGER DEFAULT 0,                  -- 块序号（从 0 开始），前端按序展示
    parent_id     BIGINT NULL REFERENCES bs_rag_chunks(id),  -- 父块 ID，父块自身为 NULL
    chunk_type    VARCHAR(16) DEFAULT 'parent',       -- parent / child
    section_title VARCHAR(256),                        -- 章节标题
    page          INTEGER,                             -- PDF 页码（Markdown/Word 为 NULL）
    created_at    TIMESTAMP DEFAULT NOW()
);

-- 按文档哈希查询（文档列表、删除、更新）
CREATE INDEX IF NOT EXISTS idx_rag_doc_hash ON bs_rag_chunks(doc_hash);

-- 按父块 ID 查询（父子替换：子块命中后查父块内容）
CREATE INDEX IF NOT EXISTS idx_rag_parent_id ON bs_rag_chunks(parent_id);
