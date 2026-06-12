# AGENTS.md

## 概述

FastAPI + LangGraph 医疗 AI Agent 演示项目。Python ≥3.10，使用 **uv** 管理依赖。

## 命令

```bash
uv sync                          # 安装依赖
uv run uvicorn main:app --reload # 开发服务器，监听 :8000
uv run uvicorn main:app          # 生产模式（也可：docker compose up in docker/）
```

项目未配置测试套件、linter 或 formatter。

## 架构

Java 风格分层结构，模块级单例模式：

```
main.py                  → FastAPI 入口，注册路由 + 全局异常处理
config/                  → 配置层（.env 通过 pydantic-settings 加载）、数据库、LLM、日志、提示词
  settings.py            → 单例 Settings 实例，所有环境变量在此定义
  database.py            → SQLAlchemy 异步引擎 + session 工厂（asyncmy/MySQL）
  llm.py                 → ChatOpenAI 流式 + 非流式两个实例
  prompt.py              → INTENT_PROMPT、CHAT_PROMPT、REFUSE_PROMPT 常量
api/
  controller/            → FastAPI 路由（user_router、agent_router）
  service/               → 业务逻辑（UserService、AgentService、ProductService）
  models/                → SQLAlchemy ORM 模型（Base 继承自 DeclarativeBase）
  schemas/               → Pydantic 请求/响应 DTO（DTO = 输入，VO = 输出）
  handler/               → 全局异常处理器、OpenAI SSE 响应封装
agent/
  graph.py               → LangGraph StateGraph 构建器 → 模块级 `agent` 单例
  nodes/                 → intent_node → chat_node → refuse_node → END
  state/                 → AgentState（Pydantic BaseModel，含 messages + intent + current_node）
  memory/                → Checkpointer 工厂（sqlite / async_sqlite / postgres，由 .env 控制）
```

## 关键模式

- **配置加载**：`config.settings.settings` — 所有配置通过 pydantic-settings 从 `.env` 读取。运行前需复制 `.env.example` 为 `.env` 并填写实际值。
- **数据库会话**：始终使用 `async with database.session() as db:` — 上下文管理器自动关闭连接。
- **Agent 流程**：`intent_node` 分类医疗/非医疗 → 路由到 `chat_node`（LLM 流式生成）或 `refuse_node`（固定拒绝）。所有消息最终都经过 `refuse_node` 作为终审节点。
- **已知 Bug**：`intent_node` 将 `state.intent` 设为 `"chat"` 或 `"refuse"`，但 `refuse_node` 检查的是 `state.intent != "medical"` — 导致拒绝消息无论意图如何都会被追加。修复方式：统一 intent 值或修正判断条件。
- **SSE 流式输出**：`AgentService.chat()` 通过 `agent.astream_events(version="v2")` 产出 `ChatChunk`，由 `OpenAIStreamResponse` 封装为 `data: {...}\n\n` 帧，末尾发送 `data: [DONE]\n\n`。
- **线程记忆**：`ChatRequest` 中的 `user` 字段映射到 LangGraph 的 `thread_id`。不传则自动生成匿名临时 ID。
- **Checkpointer**：在导入时由 `checkpointer_model` 环境变量决定（默认 `async_sqlite`）。SQLite 文件自动创建于 `agent/data/` 下。
- **日志**：loguru 接管标准库 logging。控制台 ≥INFO，文件按天轮转输出到 `logs/`。
- **响应格式**：所有非流式接口使用 `Response.success(data)` / `Response.error(msg, code)` 统一包装。

## 项目约定

- 注释使用中文，层级编号风格（一、1、）。
- 命名规范：`*DTO` 表示请求体，`*VO` 表示响应体。
- `product_service.py` 调用外部 Java 后端（`java_url` 环境变量）— 目前未挂载到任何路由。
- `.env` 已加入 `.gitignore`；`.env.example` 为模板文件。
- `agent/data/` 和 `logs/` 已加入 `.gitignore`。
