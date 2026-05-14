FROM python:3.12-slim

WORKDIR /app

# 安装 uv
RUN pip install uv --no-cache-dir

# 先复制依赖文件（利用 Docker 层缓存）
COPY pyproject.toml uv.lock ./

# 安装依赖
RUN uv sync --frozen --no-dev

# 复制源代码
COPY . .

# 暴露端口
EXPOSE 8000

# 启动命令（多副本由容器编排层控制，uvicorn 单进程即可）
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
