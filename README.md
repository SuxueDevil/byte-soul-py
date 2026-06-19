# ByteSoul

字节灵魂 — RAG 助手

## 安装依赖

```bash
uv sync
```

## 配置

复制 `config.yaml.example` 为 `config.yaml`，填写实际值。也可通过 `CONFIG_FILE` 环境变量指定路径。

## 启动

```bash
uv run uvicorn main:app --reload
```

## 项目架构

```
byte-soul-py/
├── main.py                          # FastAPI 入口
├── config/
│   ├── database.py                  # 客户端单例（MySQL、PG、Milvus、ES、LLM、Embedding、雪花ID）
│   ├── settings.py                  # 配置加载
│   ├── logger.py                    # 日志
│   └── prompts.py                   # 提示词模板
├── api/
│   ├── controller/                  # 路由层
│   │   ├── rag_controller.py        # RAG 接口
│   │   ├── agent_controller.py      # Agent 接口
│   │   └── user_controller.py       # 用户接口
│   ├── service/                     # 业务层
│   │   ├── rag_service.py           # RAG 服务
│   │   ├── agent_service.py         # Agent 服务
│   │   └── user_service.py          # 用户服务
│   ├── schemas/                     # 请求/响应结构
│   └── models/                      # ORM 模型
│       ├── rag.py                   # bs_rag_chunks 表
│       └── user.py                  # 用户表
├── agent/
│   ├── builder.py                   # LangGraph 状态图构建器
│   ├── tools.py                     # 工具定义
│   ├── memory/
│   │   └── checkpointer.py          # 记忆持久化
│   ├── nodes/
│   │   ├── intent_node.py           # 意图分类
│   │   ├── react_node.py            # ReAct 循环
│   │   └── refuse_node.py           # 拒绝回答
│   ├── schemas/
│   │   ├── state.py                 # AgentState 定义
│   │   └── rag.py                   # RAG 数据结构
│   └── rag/
│       ├── pipeline.py              # RAG 管道
│       ├── ingestion/               # 离线处理
│       │   ├── loader.py            # 文档加载器
│       │   ├── spliter.py           # 切割器
│       │   └── saver.py             # 入库器
│       ├── pre/                     # 检索前
│       │   ├── ik_tokenize.py       # IK 分词
│       │   ├── query_rewriter.py    # 查询改写
│       │   └── query_expansion.py   # 查询扩展
│       ├── mid/                     # 检索中（待实现）
│       └── post/                    # 检索后（待实现）
└── data/
    ├── pg.sql                       # PG 建表脚本
    ├── milvus.py                    # Milvus 建集合脚本
    └── es.py                        # ES 建索引脚本
```

## 存储架构

```
┌─────────────────────────────────────────────────┐
│                   PostgreSQL                     │
│   bs_rag_chunks 表：原文 + 元数据 + 父子关系     │
└──────────┬──────────────────┬───────────────────┘
           │                  │
     ┌─────▼─────┐    ┌──────▼──────┐
     │  Milvus   │    │Elasticsearch│
     │  纯向量    │    │  纯 BM25    │
     │ pg_id+vec │    │ pg_id+文本  │
     └───────────┘    └─────────────┘
```

## RAG 流程

```
用户提问
  ↓
① IK 分词 → 提取关键词
② LLM 改写 → 口语化→正式表述
③ 查询扩展 → 生成多个相关查询
④ Milvus 向量检索 → pg_id + score
⑤ ES BM25 检索 → pg_id + score
⑥ 融合(RRF) → 合并结果
⑦ 回 PG 查原文
⑧ 父子替换 → 子块命中→查父块内容
⑨ rerank → 精排
⑩ LLM 生成回答
```

## API

| 接口 | 方法 | 用途 |
|------|------|------|
| `/rag/ingest` | POST | 上传文档入库 |
| `/rag/documents` | GET | 文档列表 |
| `/rag/documents/{doc_hash}/chunks` | GET | chunk 列表 |
| `/rag/documents/{doc_hash}` | DELETE | 删除文档 |
| `/agent/chat` | POST | OpenAI 格式聊天 |
