import json
from pydantic import BaseModel
from fastapi.responses import StreamingResponse


class OpenAIStreamResponse(StreamingResponse):
    """OpenAI 格式 SSE 流式响应：接收 ChatChunk 流，自动序列化为 SSE 帧"""

    @staticmethod
    def _serialize(chunk):
        if isinstance(chunk, BaseModel):
            return chunk.model_dump_json(exclude_none=True)
        return json.dumps(chunk, ensure_ascii=False)

    def __init__(self, generator, **kwargs):
        kwargs.setdefault("media_type", "text/event-stream")
        super().__init__(self.wrap(generator), **kwargs)

    async def wrap(self, generator):
        async for chunk in generator:
            yield f"data: {self._serialize(chunk)}\n\n"
        yield "data: [DONE]\n\n"
