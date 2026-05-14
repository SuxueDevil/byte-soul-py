from typing import Literal

from pydantic import BaseModel


class IntentResult(BaseModel):
    """意图识别结果，供 LLM 结构化输出使用"""
    intent: Literal["medical", "refuse"]
