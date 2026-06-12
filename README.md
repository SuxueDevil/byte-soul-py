## 安装依赖
uv sync


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
