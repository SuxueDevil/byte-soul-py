# AGENTS.md

## 最高准则

写代码之前请三思，找我确认清楚，我不允许任何垃圾和冗余代码出现，并且必须遵循 `bs代码规范v1.0.md`，否则我会狠狠击打身旁的小猫，你是就罪人

## 概述

FastAPI + LangGraph RAG 助手，代号 **ByteSoul**。Python ≥3.10，使用 **uv** 管理依赖。

## 命令

```bash
uv sync                          # 安装依赖
uv run uvicorn main:app --reload # 开发服务器，监听 :8000
uv run uvicorn main:app          # 生产模式（也可：docker compose up in docker/）
```

项目未配置测试套件、linter 或 formatter。

## 架构


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

