# 代码规范

## 命名规范

### 类命名
- 使用大驼峰：`MarkdownLoader`、`IngestionPipeline`
- 抽象类以 `Base` 开头：`BaseRetriever`

### 函数/方法命名
- 使用小写字母 + 下划线：`load_documents`、`split_by_header`
- 私有方法不加_，位置在共有方法之后

### 配置项命名
- 使用小写字母 + 下划线：`rag.chunk_size`、`llm.api_key`

## 注释规范

### 文件头注释
```python
"""模块功能简述"""
```

### 类注释
```python
class MarkdownLoader:
    """Markdown 文件加载器"""
```

### 方法注释
```python
def load(self, file_path: str) -> list[Document]:
    """
    加载单个 Markdown 文件。
    @param file_path: 文件路径
    @return: Document 列表
    """
```

### 行内注释
- 使用中文
- 简洁明了
- 使用层级编号标注（一、1、）
- 格式：用了什么 → 干什么 → 用途
```python
# 一、计算文档哈希
# 1、用 MD5 算法对文件内容取摘要，用于增量更新时判断文档是否变化
doc_hash = hashlib.md5(content).hexdigest()
```

## 代码结构

### 类结构
```python
class ExampleClass:
    """类文档"""

    # 1. 类变量
    DEFAULT_VALUE = "default"

    # 2. __init__ 方法
    def __init__(self):
        self.instance_var = None

    # 3. 公有方法
    def public_method(self):
        pass
```

### 条件判断
- 避免大段 if else，使用 early return、枚举类、字典映射
```python
# 一、early return（卫语句）
# 1、提前处理异常情况并返回，减少嵌套层级
if not user:
    raise NotFoundError()
if not user.active:
    raise InactiveError()
if not user.has_permission:
    raise PermissionError()
do_something()

# 二、枚举类
# 1、用枚举管理有限状态，避免魔法字符串
from enum import Enum

class PaymentStatus(Enum):
    SUCCESS = "success"
    ERROR = "error"
    PENDING = "pending"

# 使用枚举判断
if status == PaymentStatus.SUCCESS:
    handle_success()

```

## 设计模式

### 单例模式
- 配置、日志：模块级单例
- 业务服务：依赖注入（FastAPI Depends）
- 需要动态切换：工厂模式

```python
# 一、模块级单例（配置、日志）
# 1、用于全局共享的配置和日志实例
settings = Settings()
logger = Logger()

# 二、依赖注入（业务服务）
# 1、FastAPI 的 Depends 机制，便于测试和替换
@router.post("/chat")
async def chat(request: ChatRequest, service: AgentService = Depends(get_agent_service)):
    ...

# 三、工厂模式（需要动态切换）
# 1、根据配置创建不同的实现
class EmbeddingFactory:
    @staticmethod
    def create(config) -> Embeddings:
        if config.type == "openai":
            return OpenAIEmbeddings(...)
        elif config.type == "local":
            return LocalEmbeddings(...)
```

## 类型校验

- 既然用了 Pydantic 做参数校验，就不要在代码里再加兜底逻辑
- 让校验层负责非空检查，业务层信任校验结果
```python
# 不推荐：Pydantic 校验 + 代码兜底，重复且矛盾
name = request.name or "unknown"

# 推荐：Pydantic 校验非空，业务层直接用
name = request.name  # Pydantic 已保证非空
```

## 配置管理

### 配置读取
```python
from config.settings import settings

# 读取配置
chunk_size = settings.rag.chunk_size
api_key = settings.llm.api_key
```

## Git 规范

### 提交信息
```
<type>(<scope>): <subject>

<body>

<footer>
```

类型：
- `feat`: 新功能
- `fix`: 修复
- `refactor`: 重构
- `docs`: 文档
- `style`: 格式
- `test`: 测试
- `chore`: 构建/工具

### 分支命名
- `feature/xxx`: 新功能
- `fix/xxx`: 修复
- `refactor/xxx`: 重构
