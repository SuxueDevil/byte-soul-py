from langchain_openai import ChatOpenAI

from .settings import settings

# 一、创建 LLM 客户端
# 1、streaming=True 开启 SSE 流式输出，astream_events 逐个获取 token
llm = ChatOpenAI(
    model=settings.llm_model,
    api_key=settings.llm_api_key,
    base_url=settings.llm_base_url,
    streaming=True,
)

# 2、非流式实例，供意图分类等不需要流式输出的场景使用
llm_no_stream = ChatOpenAI(
    model=settings.llm_model,
    api_key=settings.llm_api_key,
    base_url=settings.llm_base_url,
    streaming=False,
)
