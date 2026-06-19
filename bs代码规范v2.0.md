# 代码规范

## 命名规范

- **类**：大驼峰；抽象类以 `Base` 开头（`BaseRetriever`）
- **函数/方法**：小写 + 下划线（`load_documents`）
- **配置项**：小写 + 下划线（`rag.chunk_size`）
- **模块级单例**：小驼峰 + `Template` / `Service` / `Pipeline` 后缀（`mysqlTemplate` / `userService` / `ragPipeline`），对齐 Java `@Component` 风格
- 私有方法不加_，位置在公有方法之后

## 注释规范

- 中文 docstring，简洁说明用途；方法用 `Args:` / `Returns:` 标注
- 行内注释层级编号：一、1、（用了什么 → 干什么 → 用途）
- **单行操作只用一级**，不需要二级
```python
# 一、计算文档哈希
# 1、用 MD5 算法对文件内容取摘要，用于增量更新
doc_hash = hashlib.md5(content).hexdigest()

# 一、加载 Markdown 文件
return UnstructuredMarkdownLoader(file_path).load()
```

## 代码结构

- **类结构**：公有方法（私有方法在公有方法之后）
- **条件判断**：避免大段 if else，用 early return / 枚举类
- **多方法类用分隔符**：方法之间用 `# ─────────────────────────── 名称 ───────────────────────────` 分隔，提升可读性

```python
class Spilter:
    """文档切割器"""

    # ─────────────────────────── Markdown ───────────────────────────
    @staticmethod
    def markdown(documents): ...

    # ─────────────────────────── PDF ───────────────────────────
    @staticmethod
    def pdf(documents): ...

    # ─────────────────────────── Word ───────────────────────────
    @staticmethod
    def word(documents): ...

    # ─────────────────────────── 内部方法 ───────────────────────────
    @staticmethod
    def build_children(parents): ...
```

## 设计模式

### 单例：全部模块级 + fail-fast

客户端、业务服务、LangGraph 图**全部**用模块级单例，`import` 时建好。环境配错 / 资源不通 → 启动直接报错，绝不延迟到第一个请求。

| 类型 | 命名 | 例子 |
|---|---|---|
| 客户端 | `xxxTemplate` | `mysqlTemplate` / `milvusTemplate` / `esTemplate` |
| 业务服务 | `xxxService` / `xxxPipeline` | `userService` / `ragService` / `agentService` / `ragPipeline` |

```python
# config/database.py
mysqlTemplate = Database()
milvusTemplate = MilvusClient(host=..., port=...)
esTemplate = Elasticsearch(hosts=[...])
```

### 路由：直接 import

```python
# api/controller/user_controller.py
from api.service.user_service import userService

@user_router.get("/{user_id}")
async def get_user(user_id: int):
    return Response.success(await userService.get_user(user_id))
```

### 响应格式：统一 JSON

所有接口返回 `Response.success()`，前端统一处理：

```json
{
  "code": 200,
  "message": "success",
  "data": { ... }
}
```

## 类型校验

Pydantic 校验层负责非空检查,业务层**不再写兜底**：

```python
# ❌ 重复且矛盾
name = request.name or "unknown"
# ✅ 信任 Pydantic
name = request.name
```

## 异常处理

业务层**不加 try/except**，异常自然传播到全局异常处理器（`api/handler/global_exception_handler.py`）统一捕获、记录日志、返回标准错误响应。

```python
# ❌ 业务层重复 catch
try:
    return UnstructuredMarkdownLoader(file_path).load()
except Exception as e:
    logger.error(f"加载失败: {e}")
    return []

# ✅ 异常自然传播，全局处理器兜底
return UnstructuredMarkdownLoader(file_path).load()
```

## 配置管理

```python
from config.settings import settings
chunk_size = settings.rag.chunk_size
api_key = settings.llm.api_key
```