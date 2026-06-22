# ByteSoul

<div align="center">

**RAG × Agent × Graph**

前端仓库：<https://github.com/SuxueDevil/byte-soul-vue-electron/>

</div>

<p align="center">
  <img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License" />
  <img src="https://img.shields.io/badge/python-≥3.11-blue.svg" alt="Python" />
  <img src="https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey" alt="Platform" />
</p>

---
## 核心

- **FastAPI + LangGraph**：异步 Web 框架 + 状态机驱动的 ReAct Agent
- **父子分块召回**：父块给上下文、子块做精准匹配，命中子块自动回溯父块
- **多路检索**：Milvus 向量召回 + Elasticsearch BM25 召回 + Neo4j 图谱召回（即将接入）+ RRF 融合 + Cross-Encoder 精排
- **检索前优化**：IK/jieba 关键词提取 → LLM 查询改写 → 多路查询扩展
- **三库联删**：PG（原文） + Milvus（向量） + ES（索引）按 `doc_hash` 原子删除
- **多后端记忆**：Checkpointer 支持 `sqlite` / `async_sqlite` / `postgres`，按需切换

---

## 技术栈

| 类别 | 选型 |
|---|---|
| Web 框架 | FastAPI 0.136 + Uvicorn 0.46 |
| Agent | LangGraph 1.2 + LangChain 1.3 |
| 关系数据库 | MySQL 8（用户）、PostgreSQL 16（RAG 原文） |
| 向量数据库 | Milvus（`pymilvus` 3.0） |
| 全文检索 | Elasticsearch 8.17 + IK 分词 |
| 嵌入/重排 | OpenAI 兼容 Embedding + BGE Reranker（`sentence-transformers`） |
| 文档处理 | `pdfplumber`、`unstructured`、`langchain-text-splitters`、`jieba` |
| 依赖管理 | uv（`uv.lock` 锁定） |
| 日志 | loguru（接管标准 logging） |
| 容器化 | Docker + docker-compose |

---

## 运行指南

### 前置依赖

服务侧需自行部署：

| 服务 | 默认端口 | 用途 |
|---|---|---|
| MySQL 8 | 3306 | 用户表 |
| PostgreSQL 16 | 5432 | RAG 文档库（`bs_rag_chunks`） |
| Milvus | 19530 | 向量检索 |
| Elasticsearch 8 | 9200 | BM25 检索（需安装 IK 插件） |
| Neo4j（可选） | 7687 | 知识图谱（配置已预留，暂未接入业务） |
| LLM API | — | OpenAI 兼容接口（如通义千问、DeepSeek） |

### 安装

```bash
# 1、安装 uv（若未安装）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2、同步依赖
uv sync
```

### 配置

```bash
cp config.yaml.example config.yaml
```

按实际环境修改 `config.yaml`（详见下方「[配置说明](#配置说明)」一节）。

### 初始化存储

```bash
# 一、PG 建表（手动执行）
psql -U <user> -d <database> -f data/pg.sql

# 二、Milvus 建集合
python data/milvus.py

# 三、ES 建索引（确认已安装 IK 分词插件）
python data/es.py
```

### 启动

```bash
uv run uvicorn main:app --host 0.0.0.0 --port 8000
```

启动日志会依次打印 MySQL / Milvus / Elasticsearch 连接状态。

### Docker 部署

```bash
# 1、构建并启动
docker compose -f docker/docker-compose.yml up -d --build

# 2、查看日志
docker logs -f api-demo
```

> `docker-compose.yml` 默认只跑 `api` 服务，MySQL / PG / Milvus / ES 仍需外部提供。

---

## 目录结构

```
byte-soul-py/
├── main.py                          # FastAPI 入口：注册路由、lifespan、CORS
├── pyproject.toml                   # 依赖与项目元数据（uv 管理）
├── config.yaml.example              # 配置模板（拷贝为 config.yaml 使用）
│
├── config/                          # 全局基础设施
│   ├── settings.py                  # 配置加载（YAML → 扁平对象）
│   ├── database.py                  # 客户端单例（MySQL/PG/Milvus/ES/Embedding/LLM/Snowflake/Neo4j）
│   ├── logger.py                    # loguru 接管 logging
│   └── prompts.py                   # 提示词模板（意图/改写/扩展/ReAct/拒答）
│
├── api/                             # 接口层（Controller → Service → Model）
│   ├── controller/                  # 路由
│   │   ├── rag_controller.py        # /rag/*
│   │   ├── agent_controller.py      # /agent/chat
│   │   └── user_controller.py       # /users/*
│   ├── service/                     # 业务层
│   │   ├── rag_service.py           # RAG 业务封装
│   │   ├── agent_service.py         # Agent 流式封装
│   │   ├── user_service.py          # 用户业务
│   │   └── product_service.py       # 调用外部 Java 后端
│   ├── schemas/                     # 请求/响应 DTO
│   │   ├── chat.py                  # OpenAI ChatRequest / ChatChunk
│   │   ├── response.py              # Response / ResponsePage 统一包装
│   │   └── user.py                  # UserDTO / UserVO
│   ├── models/                      # ORM 模型（SQLAlchemy 2.0）
│   │   ├── rag.py                   # bs_rag_chunks
│   │   └── user.py                  # user
│   └── handler/                      # 异常/响应处理器
│       ├── global_exception_handler.py  # 全局异常兜底 + 422 校验
│       └── openai_sse_response.py   # OpenAI 格式 SSE 流响应
│
├── agent/                           # LangGraph Agent + RAG 核心
│   ├── builder.py                   # 状态图构建（intent → react/refuse → END）
│   ├── tools.py                     # @tool 工具定义（rag_search）
│   ├── memory/
│   │   └── checkpointer.py          # 短期记忆：sqlite / async_sqlite / postgres
│   ├── nodes/
│   │   ├── intent_node.py           # 意图分类（CHAT / REFUSE）
│   │   ├── react_node.py            # ReAct 循环（Thought/Action/Observation）
│   │   └── refuse_node.py           # 拒答节点
│   ├── schemas/
│   │   ├── state.py                 # AgentState
│   │   └── rag.py                   # ParentChunk / ChildChunk dataclass
│   └── rag/
│       ├── pipeline.py              # RAG 管道（ingest + query）
│       ├── ingestion/               # 离线入库
│       │   ├── loader.py            # 文件 → Document（md/pdf/docx）
│       │   ├── spliter.py           # 父子切割
│       │   └── saver.py             # PG/Milvus/ES 三库写入
│       ├── pre/                     # 检索前
│       │   ├── ik_tokenize.py       # jieba 提取关键词
│       │   ├── query_rewriter.py    # LLM 口语化→正式
│       │   └── query_expansion.py   # LLM 多路扩展
│       ├── mid/                     # 检索中
│       │   └── retriever.py         # 向量 + BM25 双路召回
│       └── post/                    # 检索后
│           ├── rrf_fuser.py         # RRF 融合
│           └── reranker.py          # Cross-Encoder 精排
│
├── data/                            # 初始化脚本
│   ├── pg.sql                       # PG 建表 DDL
│   ├── milvus.py                    # Milvus 建集合
│   ├── es.py                        # ES 建索引（含 IK mapping）
│   └── openapi.json                 # 接口快照（前端联调参考）
│
├── docker/                          # 容器化
│   ├── Dockerfile                   # 基于 python:3.12-slim + uv
│   ├── docker-compose.yml           # 单服务编排
│   └── .dockerignore
│
├── agent/memory/data/               # SQLite checkpoint 文件目录（运行时生成）
└── logs/                            # 日志目录（loguru 按天轮转）
```

---

## 存储架构

```
                    ┌─────────────────────┐
                    │     PostgreSQL      │
                    │  bs_rag_chunks 表   │
                    │  ──────────────────  │
                    │  父块 + 子块         │
                    │  原文 + 元数据       │
                    │  父子 ID 关联        │
                    └──────┬───────┬──────┘
                           │       │
              ┌────────────▼─┐   ┌─▼────────────┐
              │   Milvus     │   │ Elasticsearch│
              │   向量召回    │   │  BM25 召回   │
              │ pg_id+vector │   │ pg_id+文本   │
              └──────────────┘   └──────────────┘

         （Neo4j 已预留配置，业务侧暂未接入）
```

设计要点：

- **PG 是唯一可信源**，存原文 + 元数据 + 父子关系，向量库/索引库都是派生数据
- **`doc_hash` 是一致性锚点**：三库按 `doc_hash` 写入、删除、查重
- **父子模式**：PG 写两份（父块 + 子块），Milvus/ES 只索引子块；检索时命中子块，再用父块内容做生成上下文

---

## RAG 流程

### 离线入库

```
上传文件（md / pdf / docx / txt）
        │
        ▼
┌──────────────┐
│   Loader     │ 按扩展名选 Loader，转为 Document 列表
└──────┬───────┘
       ▼
┌──────────────┐
│   Spliter    │ 父子切割（父块 ~2000 字，子块 ~500 字 + 50 字 overlap）
└──────┬───────┘
       │ 父块 + 子块（子块 metadata 携带 parent_index/parent_content）
       ▼
┌──────────────┐
│    Saver     │ ① PG 写父块 → ② PG 写子块 → ③ Milvus 写向量 → ④ ES 写索引
└──────────────┘
       │ doc_hash（MD5）用于后续去重 / 三库联删
       ▼
   完成入库
```

### 在线检索

```
用户问题
  │
  ▼
① jieba 关键词提取 ───────────┐
  │                            │
  ▼                            │
② LLM 查询改写（口语→正式）◄──┘ 关键词辅助
  │
  ▼
③ LLM 查询扩展（生成 N 路相关查询，默认 3 路）
  │
  ├────────────────────────────┐
  ▼                            ▼
④ Milvus 向量召回           ⑤ ES BM25 召回
  │ 每路 Top-K（默认 5）      │ 每路 Top-K
  ▼                            ▼
  └────────────┬───────────────┘
               ▼
        ⑥ RRF 融合（k=60）
               │
               ▼
        ⑦ 父子替换：命中子块 → 用 metadata 中的父块内容替换
               │
               ▼
        ⑧ Cross-Encoder 精排（BGE-reranker-v2-m3）
               │
               ▼
        返回结果给 Agent（ReAct 节点拼装 Prompt → LLM 生成最终回答）
```

> 注：`①` 的 `jieba` 用于 Python 端提取关键词；ES 检索侧用的是 IK 分词器（`ik_max_word` / `ik_smart`），由 ES 自身完成。两者分工不同。

---

## Agent 流程

LangGraph 状态图：

```
                ┌──────────┐
                │  START   │
                └────┬─────┘
                     ▼
              ┌──────────────┐
              │ intent_node  │  LLM 意图分类（CHAT / REFUSE）
              └──────┬───────┘
                     │
        ┌────────────┼────────────┐
        ▼ CHAT                   ▼ REFUSE
┌──────────────┐         ┌──────────────┐
│  react_node  │         │ refuse_node  │  返回固定拒答文案
└──────┬───────┘         └──────┬───────┘
       │                        │
       ▼                        ▼
   ┌───────┐                ┌───────┐
   │  END  │                │  END  │
   └───────┘                └───────┘
```

**ReAct 循环（react_node）**：

1. 拼装 Prompt（系统提示 + 用户消息 + 历史 Observation）
2. LLM 流式输出 `Thought / Action / Action Input`
3. 解析 Action → 执行工具（`rag_search`）
4. Observation 追加到对话上下文，进入下一轮
5. 解析到 `Final Answer` 即终止，最多循环 `MAX_ITERATIONS=3` 轮

**Checkpointer**：每个会话以 `thread_id`（默认取 `request.user`）隔离，状态由 SQLite / PG 持久化，支持多轮上下文。

---

## API

所有非 SSE 接口返回统一包装：

```json
{ "code": 200, "message": "success", "data": ... }
```

### 用户

| 接口 | 方法 | 说明 |
|---|---|---|
| `/users/{user_id}` | GET | 按 ID 查询用户 |
| `/users` | POST | 创建用户（body: `{name, email, age}`） |

### RAG

| 接口 | 方法 | 说明 |
|---|---|---|
| `/rag/ingest` | POST | `multipart/form-data` 上传文件，返回 `{chunk_count}` |
| `/rag/documents` | GET | 文档列表（去重 + 统计 chunk 数） |
| `/rag/documents/{doc_hash}/chunks` | GET | 单文档全部 chunk（按 `chunk_index` 排序） |
| `/rag/documents/{doc_hash}` | DELETE | 删除文档（三库联删，返回 `deleted_count`） |

### Agent

| 接口 | 方法 | 说明 |
|---|---|---|
| `/agent/chat` | POST | OpenAI `chat.completions` 格式 SSE 流 |

`/agent/chat` 请求示例：

```json
{
  "messages": [
    { "role": "user", "content": "糖尿病吃什么药" }
  ],
  "stream": true,
  "user": "user-001",
  "model": "qwen-plus"
}
```

响应帧（`text/event-stream`）：

```
data: {"id":"user-001","object":"chat.completion.chunk","created":1718700000,"model":"qwen-plus","choices":[{"index":0,"delta":{"role":"assistant","content":"根据"},"finish_reason":null}]}

data: {"id":"user-001",...,"choices":[{"index":0,"delta":{"content":"检索结果"},"finish_reason":null}]}

data: [DONE]
```

---

## 配置说明

`config.yaml` 主要分组（详见 `config.yaml.example`）：

| 分组 | 关键字段 | 默认 |
|---|---|---|
| `java` | `url` | `http://localhost:8080/api` |
| `mysql` | `host/port/user/password/database` + `pool.*` | — |
| `llm` | `model/api_key/base_url` | `qwen-plus` |
| `checkpointer` | `model`（`sqlite`/`async_sqlite`/`postgres`）、`sqlite_url`、`pg_url` | `async_sqlite` |
| `rag.pg_url` | PostgreSQL 异步连接串 | — |
| `rag.neo4j` | `uri/user/password` | `bolt://localhost:7687` |
| `rag.embedding` | `model/dimensions`（不填则继承 `llm`） | `text-embedding-v3` / 1024 |
| `rag.vectorstore` | `milvus_host/port/collection_name` | `bs_rag` |
| `rag.bm25` | `es_hosts/index_name/ik_analyzer/ik_search_analyzer` | `bs_rag` / `ik_max_word` / `ik_smart` |
| `rag.retrieval` | `top_k/score_threshold` | `5` / `0.7` |
| `rag.pre_retrieval` | `enable_rewrite/enable_expansion/expansion_count` | `true/true/3` |
| `rag.mid_retrieval` | `enable_bm25/enable_compression` | `true/true` |
| `rag.post_retrieval` | `enable_reranker/reranker_model` | `true` / `BAAI/bge-reranker-v2-m3` |

> 可通过环境变量 `CONFIG_FILE=/path/to/config.yaml` 指定配置路径。

### 已知 TODO

- `config/database.py`：`esTemplate = None`，ES 客户端未启用；`Saver.save_to_es` 已实现但调用被注释，启用前需补齐 ES 客户端初始化
- `data/milvus.py` / `data/es.py`：连接地址写死为 `localhost`，需手动修改

---

## 开发提示

- **依赖更新**：修改 `pyproject.toml` 后执行 `uv lock` 重新生成 `uv.lock`
- **新增接口**：在 `api/controller/` 加路由 → 在 `api/service/` 加业务 → `main.py` `include_router`
- **新增 RAG 步骤**：在 `agent/rag/{pre,mid,post}/` 加模块，串联到 `pipeline.py`
- **新增 LangGraph 节点**：在 `agent/nodes/` 写节点函数，在 `agent/builder.py` 注册到状态图
- **调试 Agent**：`pyproject.toml` 包含 `debugpy`，可在 IDE 中 attach 到 5678 端口断点调试

---

## License

MIT
