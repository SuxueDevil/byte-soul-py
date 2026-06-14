# 代码规范

## 命名规范

- **类**：大驼峰；抽象类以 `Base` 开头（`BaseRetriever`）
- **函数/方法**：小写 + 下划线（`load_documents`）；私有方法不加 `_`，位置在公有方法之后
- **配置项**：小写 + 下划线（`rag.chunk_size`）

## 注释规范

- 中文 docstring，简洁说明用途；方法用 `Args:` / `Returns:` 标注
- 行内注释层级编号：一、1、（用了什么 → 干什么 → 用途）
```python
# 一、计算文档哈希
# 1、用 MD5 算法对文件内容取摘要，用于增量更新
doc_hash = hashlib.md5(content).hexdigest()
```

## 代码结构

- **类结构**：类变量 → `__init__` → 公有方法（私有方法在公有方法之后）
- **条件判断**：避免大段 if else，用 early return / 枚举类 / 字典映射

## 设计模式

### 单例模式

| 类型 | 适用 | 关键 |
|---|---|---|
| 模块级单例 | 仅轻量配置/日志 | ❌ 禁止用于重资源（LLM client、LangGraph 图、DB 连接池） |
| `lru_cache(maxsize=1)` 工厂 | 重资源/业务服务 | 懒加载、可被 `dependency_overrides` 替换 |
| 工厂模式 | 运行时按配置切换 | `EmbeddingFactory.create(config)` |

### 依赖注入（FastAPI）

业务服务用 **三件套**：`@lru_cache` 工厂 + `Annotated` 别名 + `dataclass(frozen=True)` 依赖包装。完整示例见 [api/service/agent_service.py](api/service/agent_service.py)。

#### 标准写法

```python
@dataclass(frozen=True)
class AgentServiceDependencies:
    agent: CompiledStateGraph              # 依赖都装进"箱子"

class AgentService:
    def __init__(self, deps: AgentServiceDependencies) -> None:
        self.deps = deps

@lru_cache(maxsize=1)
def _build_agent_service() -> AgentService:
    return AgentService(AgentServiceDependencies(agent=get_agent()))

AgentServiceDep = Annotated[AgentService, Depends(_build_agent_service)]
```

路由层 `agent_service: AgentServiceDep`(消费服务层别名,不再写 `= Depends(...)`)。

#### ❌ 反模式 + 迁移陷阱

- `service: X = Depends(get_x)` 老式写法——混用 `Annotated` 时触发 `SyntaxError`(别名**没有 Python 默认值**,必须排在 `File(...)` 之前)
- `Depends(Class)` 让框架帮你 `new`——无法注入复杂依赖
- 模块级 `service = Service(...)`——不可懒加载、不可测
- 基础设施层导 `XxxDep` 别名——无消费者,纯污染

#### 分层与别名导出

| 层 | 是否导出 `XxxDep` |
|---|---|
| 基础设施（`agent/builder.py`、`config/database.py`） | ❌ |
| 服务（`api/service/xxx_service.py`） | ✅ **必须导出** |
| 路由（`api/controller/xxx_controller.py`） | ❌ 消费服务层别名 |

#### 测试覆盖

```python
app.dependency_overrides[_build_agent_service] = lambda: FakeAgentService()
get_agent.cache_clear()
```

## 类型校验

Pydantic 校验层负责非空检查,业务层**不再写兜底**：

```python
# ❌ 重复且矛盾
name = request.name or "unknown"
# ✅ 信任 Pydantic
name = request.name
```

## 配置管理

```python
from config.settings import settings
chunk_size = settings.rag.chunk_size
api_key = settings.llm.api_key
```
