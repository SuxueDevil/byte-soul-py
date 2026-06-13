-- ============================================================
-- RAG 表结构定义
-- ============================================================

-- 一、PostgreSQL：rag_chunks（主存储）
-- 1、存储所有文档切片原文，其他表通过 pg_id 关联回来
-- 2、支持父子模式：parent_id 自引用，父块为 NULL，子块指向父块

CREATE TABLE IF NOT EXISTS rag_chunks (
    id          SERIAL PRIMARY KEY,                    -- 主键，其他表用 pg_id 引用
    doc_hash    VARCHAR(64) NOT NULL,                  -- 文档哈希，用于增量更新/删除
    chunk_index INT NOT NULL,                          -- 块在文档中的序号
    content     TEXT NOT NULL,                         -- 原文内容
    parent_id   INT NULL REFERENCES rag_chunks(id),    -- 父块 ID，NULL 表示自身是父块
    metadata    JSONB DEFAULT '{}',                    -- 元数据（文件名、章节标题等）
    created_at  TIMESTAMP DEFAULT NOW()                -- 创建时间
);

-- 索引：按文档哈希查询（增量更新/删除）
CREATE INDEX IF NOT EXISTS idx_rag_chunks_doc_hash ON rag_chunks(doc_hash);

-- 索引：按父块查询（父子模式）
CREATE INDEX IF NOT EXISTS idx_rag_chunks_parent_id ON rag_chunks(parent_id);


-- ============================================================
-- 二、Milvus：rag_embeddings（向量检索）
-- ============================================================
-- 用 pymilvus 代码创建，SQL 仅做参考记录
--
-- collection_name = "rag_embeddings"
-- fields:
--   id       INT64          PRIMARY KEY AUTO_ID    -- 自增主键
--   pg_id    INT64                                  -- 关联 rag_chunks.id
--   content  VARCHAR(65535)                         -- 原文冗余，避免回查 PG
--   doc_hash VARCHAR(64)                            -- 文档哈希，用于批量删除
--   vector   FLOAT_VECTOR(1024)                     -- 向量（text-embedding-v3 1024维）
--
-- index: IVF_FLAT, metric_type=COSINE, nlist=128


-- ============================================================
-- 三、Elasticsearch：rag_chunks（BM25 检索）
-- ============================================================
-- 用 elasticsearch-py 代码创建，JSON 仅做参考记录
--
-- {
--   "mappings": {
--     "properties": {
--       "pg_id":       { "type": "integer" },                              -- 关联 rag_chunks.id
--       "content":     { "type": "text",                                   -- 原文，IK 分词索引
--                        "analyzer": "ik_max_word",                        -- 索引用粗粒度
--                        "search_analyzer": "ik_smart" },                  -- 搜索用细粒度
--       "doc_hash":    { "type": "keyword" },                              -- 文档哈希
--       "chunk_index": { "type": "integer" }                               -- 块序号
--     }
--   }
-- }
