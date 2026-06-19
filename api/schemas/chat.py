from __future__ import annotations
from typing import Optional, Literal
from pydantic import BaseModel, Field


# ─────────────────────────── 请求体 ───────────────────────────
# {
#   "messages": [
#     {"role": "user", "content": "你好"}
#   ],
#   "stream": true,
#   "user": "user-001",
#   "model": "qwen-plus"
# }
class ChatRequest(BaseModel):
    """OpenAI chat.completions 请求体"""

    class Message(BaseModel):
        """OpenAI 消息"""
        role: Literal["system", "user", "assistant"]
        content: str

    messages: list[Message]                              # 对话消息列表，支持多轮上下文
    stream: bool = True                                  # 是否流式返回，默认 True
    user: Optional[str] = None                           # 用户标识，映射到 thread_id
    model: Optional[str] = None                          # 可选模型名


# ─────────────────────────── 响应体 ───────────────────────────
# {
#   "id": "chatcmpl-abc123",
#   "object": "chat.completion.chunk",
#   "created": 1718700000,
#   "model": "qwen-plus",
#   "choices": [
#     {
#       "index": 0,
#       "delta": {"role": "assistant", "content": "你"},
#       "finish_reason": null
#     }
#   ]
# }
class ChatChunk(BaseModel):
    """SSE 响应块"""

    class Delta(BaseModel):
        """增量内容"""
        role: Optional[str] = None                       # 角色标识，仅首帧出现
        content: Optional[str] = None                    # 当前帧的增量 token

    class Choice(BaseModel):
        """选项"""
        index: int = 0                                   # 选项序号，恒为 0
        delta: Delta                                     # 当前帧的增量内容
        finish_reason: Optional[Literal["stop"]] = None  # None=生成中，stop=结束

    id: str                                              # 对话唯一标识
    object: str = "chat.completion.chunk"                # 固定值，区分流式/非流式
    created: int                                         # Unix 时间戳（秒）
    model: str                                           # 实际使用的模型名
    choices: list[Choice]                                # 选项列表，恒为单元素
