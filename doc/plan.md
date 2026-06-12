# ByteSoul 开发路线图

## 项目定位

从医疗 AI Agent 演进为通用 RAG 助手，支持 ReACT 推理、工具调用、长期记忆和知识图谱检索。

## 当前状态

- FastAPI + LangGraph 基础框架已搭建
- SSE 流式输出（OpenAI 格式）
- 短期记忆（Checkpointer：SQLite / PostgreSQL）
- 基础对话能力（意图分类 → 生成 → 终审）
- 配置已迁移到 YAML（pyyaml）

## 待解决问题

- `refuse_node` 意图判断逻辑不匹配（`"chat"`/`"refuse"` vs `"medical"`），重构时一并清理
- `UserService.get_user` 空实现
- 模块级单例在 import 时初始化所有连接，任一不可用即崩溃
- 无健康检查端点、无 CORS 中间件、无数据库迁移工具

## 能力规划

### 一、工具调用 + ReACT

将 `chat_node` 改造为 ReACT 循环（思考 → 调用工具 → 观察 → 再思考）。

- `AgentState` 新增 `tool_calls` 字段
- 新增 `agent/tools/` 目录，定义可调用工具（查资料、查数据、执行计算等）
- 换用支持 function calling 的模型（DeepSeek 已支持）
- 路径：`agent/nodes/chat_node.py` → ReACT 节点

### 二、RAG（检索增强生成）

在生成前检索相关文档，注入上下文，提升回答准确性。

- 文档加载 → 分块 → embedding → 存入向量库（Chroma / Milvus）
- 新增 `agent/nodes/retriever_node`，在 `chat_node` 前执行检索
- 改造 prompt 模板，注入检索到的文档片段
- 需要在 `config.yaml` 新增向量库和 embedding 模型配置

### 三、长期记忆

跨会话持久化用户画像、偏好、历史摘要。

- `agent/memory/` 新增长期记忆层（向量数据库或 KV 存储）
- `AgentState` 新增 `long_term_memory` 字段
- 节点执行前自动检索相关记忆注入上下文
- 区分短期（会话内 checkpointer）和长期（跨会话持久化）

### 四、GraphRAG

在 RAG 基础上引入知识图谱，支持多跳推理。

- 构建知识图谱（Neo4j 或 NetworkX）
- 查询时结合图谱结构做子图检索
- 与向量检索融合，互补结构化与语义信息

## 建议优先级

```
工具调用 → RAG → 长期记忆 → GraphRAG
```

工具调用是 ReACT 的基础，RAG 是最容易出效果的增强，长期记忆依赖向量库（与 RAG 共用基础设施），GraphRAG 最复杂放最后。

## 其他待办

- [ ] 引入 Alembic 管理数据库迁移
- [ ] 添加 `/health` 健康检查端点
- [ ] 添加 CORS 中间件
- [ ] 懒加载单例（数据库、LLM、Checkpointer 按需初始化）
- [ ] 补充 UserService.get_user 实现
