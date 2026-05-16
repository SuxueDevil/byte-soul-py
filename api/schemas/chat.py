from __future__ import annotations
from typing import Optional, Literal
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """聊天接口请求体"""
    user_id: str = Field()
    message: str


class ChatChunk(BaseModel):
    """SSE 响应块"""

    class Delta(BaseModel):
        """增量内容"""
        # 角色标识，仅首帧出现，值为 "assistant"，后续帧为 None
        role: Optional[str] = None
        # 当前帧的增量 token 文本，结束帧时为 None
        content: Optional[str] = None

    class Choice(BaseModel):
        """选项"""
        # 选项序号，恒为 0（不支持多选 n>1）
        index: int = 0
        # 当前帧的增量内容
        delta: Delta
        # 生成停止原因：None 表示生成中，stop 表示自然结束
        finish_reason: Optional[Literal["stop"]] = None

    # 本次对话唯一标识，格式 chatcmpl-{29位hex}，同一请求所有帧共享
    id: str
    # 固定值，区分于非流式的 chat.completion
    object: str = "chat.completion.chunk"
    # 请求创建时的 Unix 时间戳（秒），同一请求所有帧相同
    created: int
    # 实际使用的模型名，透传回客户端
    model: str
    # 选项列表，恒为单元素
    choices: list[Choice]
