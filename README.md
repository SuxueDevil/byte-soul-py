# ByteSoul

字节灵魂 — RAG 助手

## 安装依赖
```bash
uv sync
```

## 根目录创建 config.yaml

复制 `config.yaml.example` 为 `config.yaml`，填写实际值：

```yaml
java:
  url: http://localhost:8080/api

mysql:
  user: root
  password: your_password
  host: localhost
  port: 3306
  database: your_db_name

llm:
  model: qwen-plus
  api_key: sk-your-api-key
  base_url: https://dashscope.aliyuncs.com/compatible-mode/v1

checkpointer:
  model: async_sqlite
```

也可通过 `CONFIG_FILE` 环境变量指定配置文件路径。

## 项目架构

```
agent/
├── builder.py               # LangGraph 状态图构建器
├── tools.py                 # 工具定义（@tool 装饰器）
├── memory/
│   └── checkpointer.py      # 记忆持久化
├── nodes/
│   ├── intent_node.py       # 意图分类
│   ├── react_node.py        # ReAct 循环（推理 + 工具调用）
│   └── refuse_node.py       # 拒绝回答
├── schemas/
│   ├── state.py             # AgentState 定义
│   └── rag.py               # RAG 数据结构
├── rag/
│   ├── pipeline.py          # RAG 管道
│   ├── ingestion/           # 离线处理
│   │   ├── markdown_loader.py
│   │   ├── markdown_splitter.py
│   │   └── doc_store.py
│   ├── pre_retrieval/       # 检索前
│   │   ├── query_rewriter.py
│   │   └── query_expansion.py
│   ├── mid_retrieval/       # 检索中
│   │   ├── embeddings.py
│   │   ├── vectorstore.py
│   │   ├── vector_retriever.py
│   │   └── bm25_retriever.py
│   └── post_retrieval/      # 检索后
│       ├── fusion.py
│       └── reranker.py
└── raggraph/                # RAG 图谱（待实现）
```

## 架构

```
用户提问 → intent_node → react_node → refuse_node → 输出
                          ↓
                    ┌─────────────┐
                    │ ReAct 循环   │
                    │ Thought     │
                    │ Action      │
                    │ Observation │
                    └─────────────┘
                          ↓
                    rag_search 工具
                          ↓
                    RAG 管道
                    ├─ 检索前：改写 + 扩展
                    ├─ 检索中：向量 + BM25
                    └─ 检索后：RRF 融合 + 重排序
```

## 启动

```bash
uv run uvicorn main:app --reload
```

也可通过 `CONFIG_FILE` 环境变量指定配置文件路径。
