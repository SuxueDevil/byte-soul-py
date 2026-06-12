"""通用工具函数"""
import tiktoken


def count_tokens(text: str, model: str = "cl100k_base") -> int:
    """
    计算文本的 token 数量。
    @param text: 文本内容
    @param model: tokenizer 模型名称
    @return: token 数量
    """
    encoding = tiktoken.get_encoding(model)
    return len(encoding.encode(text))


def truncate_text(text: str, max_tokens: int, model: str = "cl100k_base") -> str:
    """
    截断文本到指定 token 数量。
    @param text: 文本内容
    @param max_tokens: 最大 token 数量
    @param model: tokenizer 模型名称
    @return: 截断后的文本
    """
    encoding = tiktoken.get_encoding(model)
    tokens = encoding.encode(text)
    if len(tokens) <= max_tokens:
        return text
    return encoding.decode(tokens[:max_tokens])


def format_docs(docs: list, separator: str = "\n\n") -> str:
    """
    将文档列表格式化为字符串。
    @param docs: 文档列表
    @param separator: 分隔符
    @return: 格式化后的字符串
    """
    return separator.join(doc.page_content for doc in docs)
